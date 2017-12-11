import asyncio
import logging
import os

import bellows.types as t
import bellows.zigbee.appdb
import bellows.zigbee.device
import bellows.zigbee.util
import bellows.zigbee.zcl
import bellows.zigbee.zdo
from bellows.zigbee.exceptions import DeliveryError

LOGGER = logging.getLogger(__name__)


class ControllerApplication(bellows.zigbee.util.ListenableMixin):
    direct = t.EmberOutgoingMessageType.OUTGOING_DIRECT

    def __init__(self, ezsp, database_file=None):
        self._send_sequence = 0
        self._ezsp = ezsp
        self.devices = {}
        self._pending = {}
        self._listeners = {}
        self._ieee = None
        self._nwk = None

        if database_file is not None:
            self._dblistener = bellows.zigbee.appdb.PersistingListener(database_file, self)
            self.add_listener(self._dblistener)
            self._dblistener.load()

    @asyncio.coroutine
    def initialize(self):
        """Perform basic NCP initialization steps"""
        e = self._ezsp

        yield from e.reset()
        yield from e.version()

        c = t.EzspConfigId
        yield from self._cfg(c.CONFIG_STACK_PROFILE, 2)
        yield from self._cfg(c.CONFIG_SECURITY_LEVEL, 5)
        yield from self._cfg(c.CONFIG_SUPPORTED_NETWORKS, 1)
        zdo = (
            t.EmberZdoConfigurationFlags.APP_RECEIVES_SUPPORTED_ZDO_REQUESTS |
            t.EmberZdoConfigurationFlags.APP_HANDLES_UNSUPPORTED_ZDO_REQUESTS
        )
        yield from self._cfg(c.CONFIG_APPLICATION_ZDO_FLAGS, zdo)
        yield from self._cfg(c.CONFIG_TRUST_CENTER_ADDRESS_CACHE_SIZE, 2)
        yield from self._cfg(c.CONFIG_PACKET_BUFFER_COUNT, 0xff)
        yield from self._cfg(c.CONFIG_KEY_TABLE_SIZE, 1)
        yield from self._cfg(c.CONFIG_TRANSIENT_KEY_TIMEOUT_S, 180, True)

    @asyncio.coroutine
    def startup(self, auto_form=False):
        """Perform a complete application startup"""
        yield from self.initialize()
        e = self._ezsp

        v = yield from e.networkInit()
        if v[0] != 0:
            if not auto_form:
                raise Exception("Could not initialize network")
            yield from self.form_network()

        v = yield from e.getNetworkParameters()
        assert v[0] == 0  # TODO: Better check
        if v[1] != t.EmberNodeType.COORDINATOR:
            if not auto_form:
                raise Exception("Network not configured as coordinator")

            LOGGER.info("Forming network")
            yield from self._ezsp.leaveNetwork()
            yield from asyncio.sleep(1)  # TODO
            yield from self.form_network()

        yield from self._policy()
        nwk = yield from e.getNodeId()
        self._nwk = nwk[0]
        ieee = yield from e.getEui64()
        self._ieee = ieee[0]

        e.add_callback(self.ezsp_callback_handler)

    @asyncio.coroutine
    def form_network(self, channel=15, pan_id=None, extended_pan_id=None):
        channel = t.uint8_t(channel)

        if pan_id is None:
            pan_id = t.uint16_t.from_bytes(os.urandom(2), 'little')
        pan_id = t.uint16_t(pan_id)

        if extended_pan_id is None:
            extended_pan_id = t.fixed_list(8, t.uint8_t)([t.uint8_t(0)] * 8)

        initial_security_state = bellows.zigbee.util.zha_security(controller=True)
        v = yield from self._ezsp.setInitialSecurityState(initial_security_state)
        assert v[0] == 0  # TODO: Better check

        parameters = t.EmberNetworkParameters()
        parameters.panId = pan_id
        parameters.extendedPanId = extended_pan_id
        parameters.radioTxPower = t.uint8_t(8)
        parameters.radioChannel = channel
        parameters.joinMethod = t.EmberJoinMethod.USE_MAC_ASSOCIATION
        parameters.nwkManagerId = t.EmberNodeId(0)
        parameters.nwkUpdateId = t.uint8_t(0)
        parameters.channels = t.uint32_t(0)

        yield from self._ezsp.formNetwork(parameters)
        yield from self._ezsp.setValue(t.EzspValueId.VALUE_STACK_TOKEN_WRITING, 1)

    @asyncio.coroutine
    def _cfg(self, config_id, value, optional=False):
        v = yield from self._ezsp.setConfigurationValue(config_id, value)
        if not optional:
            assert v[0] == 0  # TODO: Better check

    @asyncio.coroutine
    def _policy(self):
        """Set up the policies for what the NCP should do"""
        e = self._ezsp
        v = yield from e.setPolicy(
            t.EzspPolicyId.TC_KEY_REQUEST_POLICY,
            t.EzspDecisionId.DENY_TC_KEY_REQUESTS,
        )
        assert v[0] == 0  # TODO: Better check
        v = yield from e.setPolicy(
            t.EzspPolicyId.APP_KEY_REQUEST_POLICY,
            t.EzspDecisionId.ALLOW_APP_KEY_REQUESTS,
        )
        assert v[0] == 0  # TODO: Better check
        v = yield from e.setPolicy(
            t.EzspPolicyId.TRUST_CENTER_POLICY,
            t.EzspDecisionId.ALLOW_PRECONFIGURED_KEY_JOINS,
        )
        assert v[0] == 0  # TODO: Better check

    def add_device(self, ieee, nwk, manufacturer=None):
        assert isinstance(ieee, t.EmberEUI64)
        # TODO: Shut down existing device
        dev = bellows.zigbee.device.Device(self, ieee, nwk, manufacturer)
        self.devices[ieee] = dev
        return dev

    @asyncio.coroutine
    def remove(self, ieee):
        assert isinstance(ieee, t.EmberEUI64)
        dev = self.devices.pop(ieee, None)
        if not dev:
            LOGGER.debug("Device not found for removal: %s", ieee)
            return
        LOGGER.info("Removing device 0x%04x (%s)", dev.nwk, ieee)
        zdo_worked = False
        try:
            resp = yield from dev.zdo.leave()
            zdo_worked = resp[0] == 0
        except Exception:
            pass
        if not zdo_worked:
            # This should probably be delivered to the parent device instead
            # of the device itself.
            yield from self._ezsp.removeDevice(dev.nwk, dev.ieee, dev.ieee)
        self.listener_event('device_removed', dev)

    def ezsp_callback_handler(self, frame_name, args):
        if frame_name == 'incomingMessageHandler':
            self._handle_frame(*args)
        elif frame_name == 'messageSentHandler':
            if args[4] != 0:
                self._handle_frame_failure(*args)
            else:
                self._handle_frame_sent(*args)
        elif frame_name == 'trustCenterJoinHandler':
            if args[2] == t.EmberDeviceUpdate.DEVICE_LEFT:
                self._handle_leave(*args)
            else:
                self._handle_join(*args)

    def _handle_frame(self, message_type, aps_frame, lqi, rssi, sender, binding_index, address_index, message):
        try:
            self.get_device(nwk=sender).radio_details(lqi, rssi)
        except KeyError:
            LOGGER.debug("No such device %s", sender)

        if aps_frame.destinationEndpoint == 0:
            deserialize = bellows.zigbee.zdo.deserialize
        else:
            deserialize = bellows.zigbee.zcl.deserialize

        tsn, command_id, is_reply, args = deserialize(aps_frame.clusterId, message)

        if is_reply:
            self._handle_reply(sender, aps_frame, tsn, command_id, args)
        else:
            self._handle_message(False, sender, aps_frame, tsn, command_id, args)

    def _handle_reply(self, sender, aps_frame, tsn, command_id, args):
        try:
            send_fut, reply_fut = self._pending[tsn]
            if send_fut.done():
                self._pending.pop(tsn)
            reply_fut.set_result(args)
            return
        except KeyError:
            LOGGER.warning("Unexpected response TSN=%s command=%s args=%s", tsn, command_id, args)
        except asyncio.futures.InvalidStateError as exc:
            LOGGER.debug("Invalid state on future - probably duplicate response: %s", exc)
            # We've already handled, don't drop through to device handler
            return

        self._handle_message(True, sender, aps_frame, tsn, command_id, args)

    def _handle_message(self, is_reply, sender, aps_frame, tsn, command_id, args):
        try:
            device = self.get_device(nwk=sender)
        except KeyError:
            LOGGER.warning("Message on unknown device 0x%04x", sender)
            return

        device.handle_message(is_reply, aps_frame, tsn, command_id, args)

    def _handle_join(self, nwk, ieee, device_update, join_dec, parent_nwk):
        LOGGER.info("Device 0x%04x (%s) joined the network", nwk, ieee)
        if ieee in self.devices:
            dev = self.get_device(ieee)
            dev.nwk = nwk
            if dev.initializing or dev.status == bellows.zigbee.device.Status.INITIALIZED:
                LOGGER.debug("Skip initialization for existing device %s", ieee)
                return
        else:
            dev = self.add_device(ieee, nwk)
            self.listener_event('device_joined', dev)

        dev.schedule_initialize()

    def _handle_leave(self, nwk, ieee, *args):
        LOGGER.info("Device 0x%04x (%s) left the network", nwk, ieee)
        dev = self.devices.get(ieee, None)
        if dev is not None:
            self.listener_event('device_left', dev)

    def _handle_frame_failure(self, message_type, destination, aps_frame, message_tag, status, message):
        try:
            send_fut, reply_fut = self._pending.pop(message_tag)
            send_fut.set_exception(DeliveryError("Message send failure: %s" % (status, )))
            reply_fut.cancel()
        except KeyError:
            LOGGER.warning("Unexpected message send failure")
        except asyncio.futures.InvalidStateError as exc:
            LOGGER.debug("Invalid state on future - probably duplicate response: %s", exc)

    def _handle_frame_sent(self, message_type, destination, aps_frame, message_tag, status, message):
        try:
            send_fut, reply_fut = self._pending[message_tag]
            # Sometimes messageSendResult and a reply come out of order
            # If we've already handled the reply, delete pending
            if reply_fut.done():
                self._pending.pop(message_tag)
            send_fut.set_result(True)
        except KeyError:
            LOGGER.warning("Unexpected message send notification")
        except asyncio.futures.InvalidStateError as exc:
            LOGGER.debug("Invalid state on future - probably duplicate response: %s", exc)

    @bellows.zigbee.util.retryable_request
    @asyncio.coroutine
    def request(self, nwk, aps_frame, data, timeout=10):
        seq = aps_frame.sequence
        assert seq not in self._pending
        send_fut = asyncio.Future()
        reply_fut = asyncio.Future()
        self._pending[seq] = (send_fut, reply_fut)

        v = yield from self._ezsp.sendUnicast(self.direct, nwk, aps_frame, seq, data)
        if v[0] != 0:
            self._pending.pop(seq)
            send_fut.cancel()
            reply_fut.cancel()
            raise DeliveryError("Message send failure %s" % (v[0], ))

        # Wait for messageSentHandler message
        v = yield from send_fut
        # Wait for reply
        v = yield from asyncio.wait_for(reply_fut, timeout)
        return v

    def reply(self, nwk, aps_frame, data):
        return self._ezsp.sendUnicast(self.direct, nwk, aps_frame, aps_frame.sequence, data)

    def permit(self, time_s=60):
        assert 0 <= time_s <= 254
        return self._ezsp.permitJoining(time_s)

    def permit_with_key(self, node, code, time_s=60):
        if type(node) is not t.EmberEUI64:
            node = t.EmberEUI64([t.uint8_t(p) for p in node])

        key = bellows.zigbee.util.convert_install_code(code)
        if key is None:
            raise Exception("Invalid install code")

        v = yield from self._ezsp.addTransientLinkKey(node, key)
        if v[0] != 0:
            raise Exception("Failed to set link key")

        return self._ezsp.permitJoining(time_s, True)

    def get_sequence(self):
        self._send_sequence = (self._send_sequence + 1) % 256
        return self._send_sequence

    def get_device(self, ieee=None, nwk=None):
        if ieee is not None:
            return self.devices[ieee]

        for dev in self.devices.values():
            # TODO: Make this not terrible
            if dev.nwk == nwk:
                return dev

        raise KeyError

    @property
    def ieee(self):
        return self._ieee

    @property
    def nwk(self):
        return self._nwk
