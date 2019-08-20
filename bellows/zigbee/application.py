import asyncio
import binascii
import logging
import os

from serial import SerialException
from zigpy.exceptions import DeliveryError
from zigpy.quirks import CustomDevice, CustomEndpoint
from zigpy.types import BroadcastAddress
import zigpy.application
import zigpy.device
import zigpy.util
import zigpy.zdo

import bellows.types as t
import bellows.zigbee.util
from bellows.exception import ControllerError, EzspError
import bellows.multicast

APS_ACK_TIMEOUT = 120
APS_REPLY_TIMEOUT = 5
APS_REPLY_TIMEOUT_EXTENDED = 28
MAX_WATCHDOG_FAILURES = 4
RESET_ATTEMPT_BACKOFF_TIME = 5
WATCHDOG_WAKE_PERIOD = 10

LOGGER = logging.getLogger(__name__)


class ControllerApplication(zigpy.application.ControllerApplication):
    direct = t.EmberOutgoingMessageType.OUTGOING_DIRECT

    def __init__(self, ezsp, database_file=None):
        super().__init__(database_file=database_file)
        self._ctrl_event = asyncio.Event()
        self._ezsp = ezsp
        self._multicast = bellows.multicast.Multicast(ezsp)
        self._pending = Requests()
        self._watchdog_task = None
        self._reset_task = None
        self._in_flight_msg = None

    @property
    def controller_event(self):
        """Return asyncio.Event for controller app."""
        return self._ctrl_event

    @property
    def is_controller_running(self):
        """Return True if controller was successfully initialized."""
        return self.controller_event.is_set() and self._ezsp.is_ezsp_running

    @property
    def multicast(self):
        """Return EZSP MulticastController."""
        return self._multicast

    async def initialize(self):
        """Perform basic NCP initialization steps"""
        e = self._ezsp

        await e.reset()
        await e.version()

        c = t.EzspConfigId
        await self._cfg(c.CONFIG_STACK_PROFILE, 2)
        await self._cfg(c.CONFIG_SECURITY_LEVEL, 5)
        await self._cfg(c.CONFIG_SUPPORTED_NETWORKS, 1)
        zdo = (
            t.EmberZdoConfigurationFlags.APP_RECEIVES_SUPPORTED_ZDO_REQUESTS |
            t.EmberZdoConfigurationFlags.APP_HANDLES_UNSUPPORTED_ZDO_REQUESTS
        )
        await self._cfg(c.CONFIG_APPLICATION_ZDO_FLAGS, zdo)
        await self._cfg(c.CONFIG_TRUST_CENTER_ADDRESS_CACHE_SIZE, 2)
        await self._cfg(c.CONFIG_ADDRESS_TABLE_SIZE, 16)
        await self._cfg(c.CONFIG_SOURCE_ROUTE_TABLE_SIZE, 8)
        await self._cfg(c.CONFIG_MAX_END_DEVICE_CHILDREN, 32)
        await self._cfg(c.CONFIG_INDIRECT_TRANSMISSION_TIMEOUT, 7680)
        await self._cfg(c.CONFIG_KEY_TABLE_SIZE, 1)
        await self._cfg(c.CONFIG_TRANSIENT_KEY_TIMEOUT_S, 180, True)
        await self._cfg(c.CONFIG_END_DEVICE_POLL_TIMEOUT, 60)
        await self._cfg(c.CONFIG_END_DEVICE_POLL_TIMEOUT_SHIFT, 8)
        await self._cfg(c.CONFIG_MULTICAST_TABLE_SIZE,
                        self.multicast.TABLE_SIZE)
        await self._cfg(c.CONFIG_PACKET_BUFFER_COUNT, 0xff)

        status, count = await e.getConfigurationValue(
            c.CONFIG_APS_UNICAST_MESSAGE_COUNT)
        assert status == t.EmberStatus.SUCCESS
        self._in_flight_msg = asyncio.Semaphore(count)
        LOGGER.debug("APS_UNICAST_MESSAGE_COUNT is set to %s", count)

        await self.add_endpoint(
            output_clusters=[zigpy.zcl.clusters.security.IasZone.cluster_id]
        )

    async def add_endpoint(self, endpoint=1,
                           profile_id=zigpy.profiles.zha.PROFILE_ID,
                           device_id=0xbeef,
                           app_flags=0x00,
                           input_clusters=[],
                           output_clusters=[]):
        """Add endpoint."""
        res = await self._ezsp.addEndpoint(
            endpoint, profile_id, device_id, app_flags,
            len(input_clusters), len(output_clusters),
            input_clusters, output_clusters
        )
        LOGGER.debug("Ezsp adding endpoint: %s", res)

    async def startup(self, auto_form=False):
        """Perform a complete application startup"""
        await self.initialize()
        e = self._ezsp

        v = await e.networkInit()
        if v[0] != t.EmberStatus.SUCCESS:
            if not auto_form:
                raise Exception("Could not initialize network")
            await self.form_network()

        v = await e.getNetworkParameters()
        assert v[0] == t.EmberStatus.SUCCESS  # TODO: Better check
        if v[1] != t.EmberNodeType.COORDINATOR:
            if not auto_form:
                raise Exception("Network not configured as coordinator")

            LOGGER.info("Forming network")
            await self._ezsp.leaveNetwork()
            await asyncio.sleep(1)  # TODO
            await self.form_network()

        await self._policy()
        nwk = await e.getNodeId()
        self._nwk = nwk[0]
        ieee = await e.getEui64()
        self._ieee = ieee[0]

        e.add_callback(self.ezsp_callback_handler)
        self.controller_event.set()
        self._watchdog_task = asyncio.ensure_future(self._watchdog())

        self.handle_join(self.nwk, self.ieee, 0)
        LOGGER.debug("EZSP nwk=0x%04x, IEEE=%s", self._nwk, str(self._ieee))
        await self.multicast.startup(self.get_device(self.ieee))

    async def shutdown(self):
        """Shutdown and cleanup ControllerApplication."""
        LOGGER.info("Shutting down ControllerApplication")
        self.controller_event.clear()
        if self._watchdog_task and not self._watchdog_task.done():
            LOGGER.debug("Cancelling watchdog")
            self._watchdog_task.cancel()
        if self._reset_task and not self._reset_task.done():
            self._reset_task.cancel()
        self._ezsp.close()

    async def form_network(self, channel=15, pan_id=None, extended_pan_id=None):
        channel = t.uint8_t(channel)

        if pan_id is None:
            pan_id = t.uint16_t.from_bytes(os.urandom(2), 'little')
        pan_id = t.uint16_t(pan_id)

        if extended_pan_id is None:
            extended_pan_id = t.fixed_list(8, t.uint8_t)([t.uint8_t(0)] * 8)

        initial_security_state = bellows.zigbee.util.zha_security(controller=True)
        v = await self._ezsp.setInitialSecurityState(initial_security_state)
        assert v[0] == t.EmberStatus.SUCCESS  # TODO: Better check

        parameters = t.EmberNetworkParameters()
        parameters.panId = pan_id
        parameters.extendedPanId = extended_pan_id
        parameters.radioTxPower = t.uint8_t(8)
        parameters.radioChannel = channel
        parameters.joinMethod = t.EmberJoinMethod.USE_MAC_ASSOCIATION
        parameters.nwkManagerId = t.EmberNodeId(0)
        parameters.nwkUpdateId = t.uint8_t(0)
        parameters.channels = t.uint32_t(0)

        await self._ezsp.formNetwork(parameters)
        await self._ezsp.setValue(t.EzspValueId.VALUE_STACK_TOKEN_WRITING, 1)

    async def _cfg(self, config_id, value, optional=False):
        v = await self._ezsp.setConfigurationValue(config_id, value)
        if not optional:
            assert v[0] == t.EmberStatus.SUCCESS  # TODO: Better check

    async def _policy(self):
        """Set up the policies for what the NCP should do"""
        e = self._ezsp
        v = await e.setPolicy(
            t.EzspPolicyId.TC_KEY_REQUEST_POLICY,
            t.EzspDecisionId.DENY_TC_KEY_REQUESTS,
        )
        assert v[0] == t.EmberStatus.SUCCESS  # TODO: Better check
        v = await e.setPolicy(
            t.EzspPolicyId.APP_KEY_REQUEST_POLICY,
            t.EzspDecisionId.ALLOW_APP_KEY_REQUESTS,
        )
        assert v[0] == t.EmberStatus.SUCCESS  # TODO: Better check
        v = await e.setPolicy(
            t.EzspPolicyId.TRUST_CENTER_POLICY,
            t.EzspDecisionId.ALLOW_PRECONFIGURED_KEY_JOINS,
        )
        assert v[0] == t.EmberStatus.SUCCESS  # TODO: Better check

    async def force_remove(self, dev):
        # This should probably be delivered to the parent device instead
        # of the device itself.
        await self._ezsp.removeDevice(dev.nwk, dev.ieee, dev.ieee)

    def ezsp_callback_handler(self, frame_name, args):
        LOGGER.debug("Received %s frame with %s", frame_name, args)
        if frame_name == 'incomingMessageHandler':
            self._handle_frame(*args)
        elif frame_name == 'messageSentHandler':
            if args[4] != t.EmberStatus.SUCCESS:
                self._handle_frame_failure(*args)
            else:
                self._handle_frame_sent(*args)
        elif frame_name == 'trustCenterJoinHandler':
            if args[2] == t.EmberDeviceUpdate.DEVICE_LEFT:
                self.handle_leave(args[0], args[1])
            else:
                self.handle_join(args[0], args[1], args[4])
        elif frame_name == '_reset_controller_application':
            self._handle_reset_request(*args)

    def _handle_frame(self, message_type, aps_frame, lqi, rssi, sender, binding_index, address_index, message):
        try:
            device = self.get_device(nwk=sender)
        except KeyError:
            LOGGER.debug("No such device %s", sender)
            return

        device.radio_details(lqi, rssi)
        try:
            tsn, command_id, is_reply, args = self.deserialize(device, aps_frame.sourceEndpoint, aps_frame.clusterId, message)
        except ValueError as e:
            LOGGER.error("Failed to parse message (%s) on cluster %d, because %s", binascii.hexlify(message), aps_frame.clusterId, e)
            return

        if is_reply:
            self._handle_reply(device, aps_frame, tsn, command_id, args)
        else:
            self.handle_message(device, False, aps_frame.profileId, aps_frame.clusterId, aps_frame.sourceEndpoint, aps_frame.destinationEndpoint, tsn, command_id, args)

    @staticmethod
    def _dst_pp(addr, aps):
        """Return format string and args."""
        ep, cluster = aps.destinationEndpoint, aps.clusterId
        return '[0x%04x:%s:0x%04x]: ', (addr, ep, cluster)

    def _handle_reply(self, sender, aps_frame, tsn, command_id, args):
        try:
            request = self._pending[tsn]
            if request.reply:
                request.reply.set_result(args)
            return
        except KeyError:
            hdr, hdr_args = self._dst_pp(sender.nwk, aps_frame)
            LOGGER.debug(hdr + "Unexpected response TSN=%s command=%s args=%s",
                         *(hdr_args + (tsn, command_id, args)))
        except asyncio.futures.InvalidStateError as exc:
            hdr, hdr_args = self._dst_pp(sender.nwk, aps_frame)
            LOGGER.debug(hdr + "Invalid state on future - probably duplicate response: %s",
                         *(hdr_args + (exc, )))
            # We've already handled, don't drop through to device handler
            return

        self.handle_message(sender, True, aps_frame.profileId, aps_frame.clusterId, aps_frame.sourceEndpoint, aps_frame.destinationEndpoint, tsn, command_id, args)

    def _handle_frame_failure(self, message_type, destination, aps_frame, message_tag, status, message):
        hdr, hdr_args = self._dst_pp(destination, aps_frame)
        try:
            request = self._pending[message_tag]
            msg = hdr + "message send failure: %s"
            msg_args = (hdr_args + (status, ))
            request.send.set_exception(DeliveryError(msg % msg_args))
        except KeyError:
            LOGGER.debug(hdr + "Unexpected message send failure", *hdr_args)
        except asyncio.futures.InvalidStateError as exc:
            LOGGER.debug(hdr + "Invalid state on future - probably duplicate response: %s",
                         *(hdr_args + (exc, )))

    def _handle_frame_sent(self, message_type, destination, aps_frame, message_tag, status, message):
        try:
            request = self._pending[message_tag]
            request.send.set_result(True)
        except KeyError:
            hdr, hdr_args = self._dst_pp(destination, aps_frame)
            LOGGER.debug(hdr + "Unexpected message send notification", *hdr_args)
        except asyncio.futures.InvalidStateError as exc:
            hdr, hdr_args = self._dst_pp(destination, aps_frame)
            LOGGER.debug(hdr + "Invalid state on future - probably duplicate response: %s",
                         *(hdr_args + (exc, )))

    def _handle_reset_request(self, error):
        """Reinitialize application controller."""
        LOGGER.debug("Resetting ControllerApplication. Cause: '%s'", error)
        self.controller_event.clear()
        if self._reset_task:
            LOGGER.debug("Preempting ControllerApplication reset")
            self._reset_task.cancel()

        self._reset_task = asyncio.ensure_future(self._reset_controller_loop())

    async def _reset_controller_loop(self):
        """Keep trying to reset controller until we succeed."""
        self._watchdog_task.cancel()
        while True:
            try:
                await self._reset_controller()
                break
            except (asyncio.TimeoutError, SerialException) as exc:
                LOGGER.debug(
                    "ControllerApplication reset unsuccessful: %s", str(exc))
            await asyncio.sleep(RESET_ATTEMPT_BACKOFF_TIME)

        self._reset_task = None
        LOGGER.debug("ControllerApplication successfully reset")

    async def _reset_controller(self):
        """Reset Controller."""
        self._ezsp.close()
        await asyncio.sleep(0.5)
        await self._ezsp.reconnect()
        await self.startup()

    @zigpy.util.retryable_request
    async def request(self, nwk, profile, cluster, src_ep, dst_ep, sequence, data, expect_reply=True,
                      timeout=APS_REPLY_TIMEOUT):
        if not self.is_controller_running:
            raise ControllerError("ApplicationController is not running")

        aps_frame = t.EmberApsFrame()
        aps_frame.profileId = t.uint16_t(profile)
        aps_frame.clusterId = t.uint16_t(cluster)
        aps_frame.sourceEndpoint = t.uint8_t(src_ep)
        aps_frame.destinationEndpoint = t.uint8_t(dst_ep)
        aps_frame.options = t.EmberApsOption(
            t.EmberApsOption.APS_OPTION_RETRY |
            t.EmberApsOption.APS_OPTION_ENABLE_ROUTE_DISCOVERY
        )
        aps_frame.groupId = t.uint16_t(0)
        aps_frame.sequence = t.uint8_t(sequence)

        try:
            dev = self.get_device(nwk=nwk)
            if expect_reply and dev.node_desc.is_end_device in (True, None):
                LOGGER.debug("Extending timeout for %s/0x%04x", dev.ieee, nwk)
                await self._ezsp.setExtendedTimeout(dev.ieee, True)
                timeout = APS_REPLY_TIMEOUT_EXTENDED
        except KeyError:
            pass
        with self._pending.new(sequence, expect_reply) as req:
            async with self._in_flight_msg:
                res = await self._ezsp.sendUnicast(self.direct, nwk, aps_frame,
                                                   sequence, data)
                if res[0] != t.EmberStatus.SUCCESS:
                    hdr, hdr_args = self._dst_pp(nwk, aps_frame)
                    msg = hdr + "message send failure: %s"
                    msg_args = (hdr_args + (res[0], ))
                    raise DeliveryError(msg % msg_args)

                res = await asyncio.wait_for(req.send, timeout=APS_ACK_TIMEOUT)

            if expect_reply:
                res = await asyncio.wait_for(req.reply, timeout)
        return res

    def permit_ncp(self, time_s=60):
        assert 0 <= time_s <= 254
        return self._ezsp.permitJoining(time_s)

    async def permit_with_key(self, node, code, time_s=60):
        if type(node) is not t.EmberEUI64:
            node = t.EmberEUI64([t.uint8_t(p) for p in node])

        key = zigpy.util.convert_install_code(code)
        if key is None:
            raise Exception("Invalid install code")

        v = await self._ezsp.addTransientLinkKey(node, key)
        if v[0] != t.EmberStatus.SUCCESS:
            raise Exception("Failed to set link key")

        v = await self._ezsp.setPolicy(
            t.EzspPolicyId.TC_KEY_REQUEST_POLICY,
            t.EzspDecisionId.GENERATE_NEW_TC_LINK_KEY,
        )
        if v[0] != t.EmberStatus.SUCCESS:
            raise Exception("Failed to change policy to allow generation of new trust center keys")

        return self._ezsp.permitJoining(time_s, True)

    async def broadcast(self, profile, cluster, src_ep, dst_ep, grpid, radius,
                        sequence, data,
                        broadcast_address=BroadcastAddress.RX_ON_WHEN_IDLE):
        if not self.is_controller_running:
            raise ControllerError("ApplicationController is not running")

        aps_frame = t.EmberApsFrame()
        aps_frame.profileId = t.uint16_t(profile)
        aps_frame.clusterId = t.uint16_t(cluster)
        aps_frame.sourceEndpoint = t.uint8_t(src_ep)
        aps_frame.destinationEndpoint = t.uint8_t(dst_ep)
        aps_frame.options = t.EmberApsOption(
            t.EmberApsOption.APS_OPTION_NONE
        )
        aps_frame.groupId = t.uint16_t(grpid)
        aps_frame.sequence = t.uint8_t(sequence)

        with self._pending.new(sequence) as req:
            async with self._in_flight_msg:
                res = await self._ezsp.sendBroadcast(broadcast_address,
                                                     aps_frame, radius,
                                                     sequence, data)
                if res[0] != t.EmberStatus.SUCCESS:
                    hdr, hdr_args = self._dst_pp(broadcast_address, aps_frame)
                    msg = hdr + "Broadcast failure: %s"
                    msg_args = (hdr_args + (res[0], ))
                    raise DeliveryError(msg % msg_args)

                # Wait for messageSentHandler message
                res = await asyncio.wait_for(req.send,
                                             timeout=APS_ACK_TIMEOUT)
        return res

    async def _watchdog(self):
        """Watchdog handler."""
        LOGGER.debug("Starting EZSP watchdog")
        failures = 0
        await asyncio.sleep(WATCHDOG_WAKE_PERIOD)
        while True:
            try:
                await asyncio.wait_for(self.controller_event.wait(),
                                       timeout=WATCHDOG_WAKE_PERIOD * 2)
                await self._ezsp.nop()
                failures = 0
            except (asyncio.TimeoutError, EzspError) as exc:
                LOGGER.warning("Watchdog heartbeat timeout: %s", str(exc))
                failures += 1
                if failures > MAX_WATCHDOG_FAILURES:
                    break
            await asyncio.sleep(WATCHDOG_WAKE_PERIOD)

        self._handle_reset_request(
            "Watchdog timeout. Heartbeat timeouts: {}".format(failures))


class Requests(dict):
    def new(self, sequence, expect_reply=False):
        """Wrap new request into a context manager."""
        return Request(self, sequence, expect_reply)


class Request:
    """Context manager."""

    def __init__(self, pending, sequence, expect_reply=False):
        """Init context manager for sendUnicast/sendBroadcast."""
        assert sequence not in pending
        self._pending = pending
        self._reply_fut = None
        if expect_reply:
            self._reply_fut = asyncio.Future()
        self._send_fut = asyncio.Future()
        self._sequence = sequence

    @property
    def reply(self):
        """Reply Future."""
        return self._reply_fut

    @property
    def sequence(self):
        """Send Future."""
        return self._sequence

    @property
    def send(self):
        return self._send_fut

    def __enter__(self):
        """Return context manager."""
        self._pending[self.sequence] = self
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        """Clean up pending on exit."""
        if not self.send.done():
            self.send.cancel()
        if self.reply and not self.reply.done():
            self.reply.cancel()
        self._pending.pop(self.sequence)

        return not exc_type


class EZSPCoordinator(CustomDevice):
    """Zigpy Device representing Coordinator."""

    class EZSPEndpoint(CustomEndpoint):
        async def add_to_group(self, grp_id: int,
                               name: str = None) -> t.EmberStatus:
            if grp_id in self.member_of:
                return t.EmberStatus.SUCCESS

            app = self.device.application
            status = await app.multicast.subscribe(grp_id)
            if status != t.EmberStatus.SUCCESS:
                self.debug("Couldn't subscribe to 0x%04x group", grp_id)
                return status

            group = app.groups.add_group(grp_id, name)
            group.add_member(self)
            return status

        async def remove_from_group(self, grp_id: int) -> t.EmberStatus:
            if grp_id not in self.member_of:
                return t.EmberStatus.SUCCESS

            app = self.device.application
            status = await app.multicast.unsubscribe(grp_id)
            if status != t.EmberStatus.SUCCESS:
                self.debug("Couldn't unsubscribe 0x%04x group", grp_id)
                return status

            app.groups[grp_id].remove_member(self)
            return status

    signature = {
        'endpoints': {
            1: {
                'profile_id': 0x0104,
                'device_type': 0xbeef,
                'input_clusters': [],
                'output_clusters': [zigpy.zcl.clusters.security.IasZone.cluster_id]
            },
        },
    }

    replacement = {
        'manufacturer': 'Silicon Labs',
        'model': 'EZSP',
        'endpoints': {
            1: (EZSPEndpoint, {})
        }
    }
