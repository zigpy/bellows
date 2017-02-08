import asyncio
import logging
import os
import sqlite3

import bellows.types as t
from bellows.zigbee import device, endpoint, zcl, zdo

LOGGER = logging.getLogger(__name__)


class ControllerApplication:
    direct = t.EmberOutgoingMessageType.EMBER_OUTGOING_DIRECT

    def __init__(self, ezsp):
        self._send_sequence = 0
        self._ezsp = ezsp
        self.devices = {}
        self._pending = {}

    @asyncio.coroutine
    def startup(self):
        e = self._ezsp

        yield from e.reset()
        yield from e.version(4)

        c = t.EzspConfigId
        yield from self._cfg(c.EZSP_CONFIG_STACK_PROFILE, 2)
        yield from self._cfg(c.EZSP_CONFIG_SECURITY_LEVEL, 5)
        yield from self._cfg(c.EZSP_CONFIG_SUPPORTED_NETWORKS, 1)
        yield from self._cfg(c.EZSP_CONFIG_SUPPORTED_NETWORKS, 1)
        zdo = (
            t.EmberZdoConfigurationFlags.EMBER_APP_RECEIVES_SUPPORTED_ZDO_REQUESTS |
            t.EmberZdoConfigurationFlags.EMBER_APP_HANDLES_UNSUPPORTED_ZDO_REQUESTS
        )
        yield from self._cfg(c.EZSP_CONFIG_APPLICATION_ZDO_FLAGS, zdo)
        yield from self._cfg(c.EZSP_CONFIG_TRUST_CENTER_ADDRESS_CACHE_SIZE, 2)
        yield from self._cfg(c.EZSP_CONFIG_PACKET_BUFFER_COUNT, 0xff)

        v = yield from e.networkInit()
        assert v[0] == 0  # TODO: Better check

        v = yield from e.getNetworkParameters()
        assert v[0] == 0  # TODO: Better check
        if v[1] != t.EmberNodeType.EMBER_COORDINATOR:
            raise Exception("Network not configured as coordinator")

        yield from self._policy()
        nwk = yield from e.getNodeId()
        self._nwk = nwk[0]
        ieee = yield from e.getEui64()
        self._ieee = ieee[0]

        e.add_callback(self.ezsp_callback_handler)

    @asyncio.coroutine
    def _cfg(self, config_id, value):
        v = yield from self._ezsp.setConfigurationValue(config_id, value)
        assert v[0] == 0  # TODO: Better check

    @asyncio.coroutine
    def _policy(self):
        """Set up the policies for what the NCP should do"""
        e = self._ezsp
        v = yield from e.setPolicy(
            t.EzspPolicyId.EZSP_TC_KEY_REQUEST_POLICY,
            t.EzspDecisionId.EZSP_DENY_TC_KEY_REQUESTS,
        )
        assert v[0] == 0  # TODO: Better check
        v = yield from e.setPolicy(
            t.EzspPolicyId.EZSP_APP_KEY_REQUEST_POLICY,
            t.EzspDecisionId.EZSP_ALLOW_APP_KEY_REQUESTS,
        )
        assert v[0] == 0  # TODO: Better check
        v = yield from e.setPolicy(
            t.EzspPolicyId.EZSP_TRUST_CENTER_POLICY,
            t.EzspDecisionId.EZSP_ALLOW_PRECONFIGURED_KEY_JOINS,
        )
        assert v[0] == 0  # TODO: Better check

    def add_device(self, ieee, nwk):
        assert isinstance(ieee, t.EmberEUI64)
        if ieee in self.devices:
            # TODO: Check NWK?
            return self.devices[ieee]
        dev = device.Device(self, ieee, nwk)
        self.devices[ieee] = dev
        return dev

    def ezsp_callback_handler(self, frame_name, args):
        if frame_name == 'incomingMessageHandler':
            self._handle_frame(*args)
        elif frame_name == 'messageSentHandler':
            if args[4] != 0:
                self._handle_frame_failure(*args)
        elif frame_name == 'trustCenterJoinHandler':
            if args[2] == t.EmberDeviceUpdate.EMBER_DEVICE_LEFT:
                self._handle_leave(*args)
            else:
                self._handle_join(*args)

    def _handle_frame(self, message_type, aps_frame, lqi, rssi, sender, binding_index, address_index, message):
        try:
            self.get_device(nwk=sender).radio_details(lqi, rssi)
        except KeyError:
            pass

        if aps_frame.destinationEndpoint == 0:
            deserialize = zdo.deserialize
        else:
            deserialize = zcl.deserialize

        tsn, command_id, is_reply, args = deserialize(aps_frame, message)

        if is_reply:
            self._handle_reply(sender, aps_frame, tsn, command_id, args)
        else:
            self._handle_request(sender, aps_frame, tsn, command_id, args)

    def _handle_reply(self, sender, aps_frame, tsn, command_id, args):
        try:
            fut = self._pending.pop(tsn)
            fut.set_result(args)
        except KeyError:
            LOGGER.warning("Unexpected response TSN=%s command=%s args=%s", tsn, command_id, args)

    def _handle_request(self, sender, aps_frame, tsn, command_id, args):
        try:
            device = self.get_device(nwk=sender)
        except KeyError:
            LOGGER.warning("Request on unknown device 0x%04x", sender)
            return

        return device.handle_request(aps_frame, tsn, command_id, args)

    def _handle_join(self, nwk, ieee, device_update, join_dec, parent_nwk):
        LOGGER.info("Device 0x%04x (%s) joined the network", nwk, ieee)
        dev = self.add_device(ieee, nwk)
        loop = asyncio.get_event_loop()
        loop.call_soon(asyncio.async, dev.initialize())

    def _handle_leave(self, nwk, ieee, *args):
        LOGGER.info("Device 0x%04x (%s) left the network", nwk, ieee)
        self.devices.pop(ieee, None)

    def _handle_frame_failure(self, message_type, destination, aps_frame, message_tag, status, message):
        try:
            fut = self._pending.pop(message_tag)
            fut.set_exception(Exception("Message send failure"))
        except KeyError:
            LOGGER.warning("Unexpected message send failure")

    @asyncio.coroutine
    def request(self, nwk, aps_frame, data):
        seq = aps_frame.sequence
        assert seq not in self._pending
        fut = asyncio.Future()
        self._pending[seq] = fut

        v = yield from self._ezsp.sendUnicast(self.direct, nwk, aps_frame, seq, data)
        if v[0] != 0:
            self._pending.pop(seq)
            raise Exception("Message send failure %s" % (v[0], ))

        v = yield from fut
        return v

    def reply(self, nwk, aps_frame, data):
        return self._ezsp.sendUnicast(self.direct, nwk, aps_frame, aps_frame.sequence, data)

    def permit(self, time_s=60):
        assert 0 <= time_s <= 254
        return self._ezsp.permitJoining(time_s)

    def get_sequence(self):
        self._send_sequence = (self._send_sequence + 1) % 256
        return self._send_sequence

    def get_device(self, ieee=None, nwk=None):
        if ieee is not None:
            return self.devices[ieee]

        for dev in self.devices.values():
            # TODO: Make this not terrible
            if dev._nwk == nwk:
                return dev

        raise KeyError

    # Database operations
    # These are not good, and need to be reworked. Maybe the best way would be
    # to have a listener which updates the database as things change?
    def _sqlite_adapters(self):
        def adapt_ieee(eui64):
            return repr(eui64)

        def convert_ieee(s):
            l = [t.uint8_t(p, base=16) for p in s.split(b':')]
            return t.EmberEUI64(l)
        sqlite3.register_adapter(t.EmberEUI64, adapt_ieee)
        sqlite3.register_converter("ieee", convert_ieee)

    def save(self, filename):
        try:
            os.unlink(filename)
        except FileNotFoundError:
            pass

        self._sqlite_adapters()

        db = sqlite3.connect(filename, detect_types=sqlite3.PARSE_DECLTYPES)
        c = db.cursor()

        c.execute("CREATE TABLE devices (ieee ieee, nwk, status)")
        c.execute("CREATE TABLE endpoints (ieee ieee, endpoint_id, profile_id, device_type, status)")
        c.execute("CREATE TABLE clusters (ieee ieee, endpoint_id, cluster)")

        q = "INSERT INTO devices (ieee, nwk, status) VALUES (?, ?, ?)"
        devices = [(ieee, dev._nwk, dev.status) for ieee, dev in self.devices.items()]
        c.executemany(q, devices)

        q = "INSERT INTO endpoints VALUES (?, ?, ?, ?, ?)"
        for ieee, dev in self.devices.items():
            endpoints = []
            for epid, ep in dev.endpoints.items():
                if epid == 0:
                    continue  # Skip zdo
                device_type = None
                try:
                    device_type = ep.device_type
                    device_type = device_type.value
                except:
                    pass
                eprow = (
                    ieee,
                    ep._endpoint_id,
                    getattr(ep, 'profile_id', None),
                    device_type,
                    ep.status,
                )
                endpoints.append(eprow)
            c.executemany(q, endpoints)

        q = "INSERT INTO clusters VALUES (?, ?, ?)"
        for ieee, dev in self.devices.items():
            for epid, ep in dev.endpoints.items():
                if epid == 0:
                    continue
                clusters = [(ieee, epid, cluster.cluster_id) for cluster in ep.clusters.values()]
                c.executemany(q, clusters)
        db.commit()

    def load(self, filename):
        self._sqlite_adapters()
        db = sqlite3.connect(filename, detect_types=sqlite3.PARSE_DECLTYPES)
        c = db.cursor()

        try:
            c.execute("SELECT COUNT(*) FROM devices")
            c.execute("SELECT COUNT(*) FROM endpoints")
            c.execute("SELECT COUNT(*) FROM clusters")
        except Exception as e:
            LOGGER.warn("Database error, aborting loading: %s", e)
            return

        for (ieee, nwk, status) in c.execute("SELECT * FROM devices"):
            dev = self.add_device(ieee, nwk)
            dev.status = device.Status(status)

        for (ieee, endpoint_id, profile_id, device_type, status) in c.execute("SELECT * FROM endpoints"):
            ep = self.devices[ieee].add_endpoint(endpoint_id)
            ep.profile_id = profile_id
            ep.device_type = device_type
            ep.status = endpoint.Status(status)

        for (ieee, endpoint_id, cluster) in c.execute("SELECT * FROM clusters"):
            self.devices[ieee].endpoints[endpoint_id].add_cluster(cluster)
