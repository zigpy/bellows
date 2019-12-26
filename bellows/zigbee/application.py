import asyncio
import logging
import os

from bellows.exception import ControllerError, EzspError
import bellows.multicast
import bellows.types as t
import bellows.zigbee.util
from serial import SerialException
import voluptuous as vol
import zigpy.application
import zigpy.device
from zigpy.quirks import CustomDevice, CustomEndpoint
from zigpy.types import BroadcastAddress
import zigpy.util
import zigpy.zdo
import zigpy.zdo.types as zdo_t

APS_ACK_TIMEOUT = 120
CONF_PARAM_SRC_RTG = "source_routing"
CONFIG_SCHEMA = zigpy.application.CONFIG_SCHEMA.extend(
    {vol.Optional(CONF_PARAM_SRC_RTG, default=False): bellows.zigbee.util.cv_boolean}
)
EZSP_DEFAULT_RADIUS = 0
EZSP_MULTICAST_NON_MEMBER_RADIUS = 3
MAX_WATCHDOG_FAILURES = 4
MTOR_MIN_INTERVAL = 600
MTOR_MAX_INTERVAL = 1800
RESET_ATTEMPT_BACKOFF_TIME = 5
WATCHDOG_WAKE_PERIOD = 10

LOGGER = logging.getLogger(__name__)


class ControllerApplication(zigpy.application.ControllerApplication):
    direct = t.EmberOutgoingMessageType.OUTGOING_DIRECT

    def __init__(self, ezsp, database_file=None, config={}):
        super().__init__(database_file=database_file, config=CONFIG_SCHEMA(config))
        self._ctrl_event = asyncio.Event()
        self._ezsp = ezsp
        self._multicast = bellows.multicast.Multicast(ezsp)
        self._pending = zigpy.util.Requests()
        self._watchdog_task = None
        self._reset_task = None
        self._in_flight_msg = None
        self._tx_options = t.EmberApsOption(
            t.EmberApsOption.APS_OPTION_RETRY
            | t.EmberApsOption.APS_OPTION_ENABLE_ROUTE_DISCOVERY
        )
        self.use_source_routing = self.config[CONF_PARAM_SRC_RTG]

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
            t.EmberZdoConfigurationFlags.APP_RECEIVES_SUPPORTED_ZDO_REQUESTS
            | t.EmberZdoConfigurationFlags.APP_HANDLES_UNSUPPORTED_ZDO_REQUESTS
        )
        await self._cfg(c.CONFIG_APPLICATION_ZDO_FLAGS, zdo)
        await self._cfg(c.CONFIG_PAN_ID_CONFLICT_REPORT_THRESHOLD, 2)
        await self._cfg(c.CONFIG_TRUST_CENTER_ADDRESS_CACHE_SIZE, 2)
        await self._cfg(c.CONFIG_ADDRESS_TABLE_SIZE, 16)
        await self._cfg(c.CONFIG_SOURCE_ROUTE_TABLE_SIZE, 8)
        await self._cfg(c.CONFIG_MAX_END_DEVICE_CHILDREN, 32)
        await self._cfg(c.CONFIG_INDIRECT_TRANSMISSION_TIMEOUT, 7680)
        await self._cfg(c.CONFIG_KEY_TABLE_SIZE, 1)
        await self._cfg(c.CONFIG_TRANSIENT_KEY_TIMEOUT_S, 180, True)
        if self._ezsp.ezsp_version >= 7:
            await self._cfg(c.CONFIG_END_DEVICE_POLL_TIMEOUT, 8)
        else:
            await self._cfg(c.CONFIG_END_DEVICE_POLL_TIMEOUT, 60)
            await self._cfg(c.CONFIG_END_DEVICE_POLL_TIMEOUT_SHIFT, 8)
        await self._cfg(c.CONFIG_MULTICAST_TABLE_SIZE, self.multicast.TABLE_SIZE)
        await self._cfg(c.CONFIG_PACKET_BUFFER_COUNT, 0xFF)

        status, count = await e.getConfigurationValue(
            c.CONFIG_APS_UNICAST_MESSAGE_COUNT
        )
        assert status == t.EmberStatus.SUCCESS
        self._in_flight_msg = asyncio.Semaphore(count)
        LOGGER.debug("APS_UNICAST_MESSAGE_COUNT is set to %s", count)

        await self.add_endpoint(
            output_clusters=[zigpy.zcl.clusters.security.IasZone.cluster_id]
        )

    async def add_endpoint(
        self,
        endpoint=1,
        profile_id=zigpy.profiles.zha.PROFILE_ID,
        device_id=0xBEEF,
        app_flags=0x00,
        input_clusters=[],
        output_clusters=[],
    ):
        """Add endpoint."""
        res = await self._ezsp.addEndpoint(
            endpoint,
            profile_id,
            device_id,
            app_flags,
            len(input_clusters),
            len(output_clusters),
            input_clusters,
            output_clusters,
        )
        LOGGER.debug("Ezsp adding endpoint: %s", res)

    async def startup(self, auto_form=False):
        """Perform a complete application startup"""
        await self.initialize()
        e = self._ezsp

        await self.set_source_routing()
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

    async def set_source_routing(self) -> None:
        res = await self._ezsp.setConcentrator(
            self.use_source_routing,
            t.EmberConcentratorType.HIGH_RAM_CONCENTRATOR,
            MTOR_MIN_INTERVAL,
            MTOR_MAX_INTERVAL,
            2,
            5,
            0,
        )
        LOGGER.debug("Set concentrator type: %s", res)
        if res[0] != t.EmberStatus.SUCCESS:
            LOGGER.warning(
                "Couldn't set concentrator type %s: %s", self.use_source_routing, res
            )

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
            pan_id = t.uint16_t.from_bytes(os.urandom(2), "little")
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
            t.EzspPolicyId.TC_KEY_REQUEST_POLICY, t.EzspDecisionId.DENY_TC_KEY_REQUESTS
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
        if frame_name == "incomingMessageHandler":
            self._handle_frame(*args)
        elif frame_name == "messageSentHandler":
            if args[4] != t.EmberStatus.SUCCESS:
                self._handle_frame_failure(*args)
            else:
                self._handle_frame_sent(*args)
        elif frame_name == "trustCenterJoinHandler":
            if args[2] == t.EmberDeviceUpdate.DEVICE_LEFT:
                self.handle_leave(args[0], args[1])
            else:
                self.handle_join(args[0], args[1], args[4])
        elif frame_name == "incomingRouteRecordHandler":
            self.handle_route_record(*args)
        elif frame_name == "incomingRouteErrorHandler":
            self.handle_route_error(*args)
        elif frame_name == "_reset_controller_application":
            self._handle_reset_request(*args)

    def _handle_frame(
        self,
        message_type,
        aps_frame,
        lqi,
        rssi,
        sender,
        binding_index,
        address_index,
        message,
    ):
        if (
            aps_frame.clusterId == zdo_t.ZDOCmd.Device_annce
            and aps_frame.destinationEndpoint == 0
        ):
            nwk, rest = t.uint16_t.deserialize(message[1:])
            ieee, _ = t.EmberEUI64.deserialize(rest)
            LOGGER.info("ZDO Device announce: 0x%04x, %s", nwk, ieee)
            self.handle_join(nwk, ieee, 0)
        try:
            device = self.get_device(nwk=sender)
        except KeyError:
            LOGGER.debug("No such device %s", sender)
            return

        device.radio_details(lqi, rssi)
        self.handle_message(
            device,
            aps_frame.profileId,
            aps_frame.clusterId,
            aps_frame.sourceEndpoint,
            aps_frame.destinationEndpoint,
            message,
        )

    def _handle_frame_failure(
        self, message_type, destination, aps_frame, message_tag, status, message
    ):
        try:
            request = self._pending[message_tag]
            request.result.set_result((status, "message send failure"))
        except KeyError:
            LOGGER.debug(
                "Unexpected message send failure for message tag %s", message_tag
            )
        except asyncio.InvalidStateError as exc:
            LOGGER.debug(
                (
                    "Invalid state on future for message tag %s "
                    "- probably duplicate response: %s"
                ),
                message_tag,
                exc,
            )

    def _handle_frame_sent(
        self, message_type, destination, aps_frame, message_tag, status, message
    ):
        try:
            request = self._pending[message_tag]
            request.result.set_result(
                (t.EmberStatus.SUCCESS, "message sent successfully")
            )
        except KeyError:
            LOGGER.debug("Unexpected message send notification tag: %s", message_tag)
        except asyncio.InvalidStateError as exc:
            LOGGER.debug(
                (
                    "Invalid state on future for message tag %s "
                    "- probably duplicate response: %s"
                ),
                message_tag,
                exc,
            )

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
                LOGGER.debug("ControllerApplication reset unsuccessful: %s", str(exc))
            await asyncio.sleep(RESET_ATTEMPT_BACKOFF_TIME)

        self._reset_task = None
        LOGGER.debug("ControllerApplication successfully reset")

    async def _reset_controller(self):
        """Reset Controller."""
        self._ezsp.close()
        await asyncio.sleep(0.5)
        await self._ezsp.reconnect()
        await self.startup()

    async def mrequest(
        self,
        group_id,
        profile,
        cluster,
        src_ep,
        sequence,
        data,
        *,
        hops=EZSP_DEFAULT_RADIUS,
        non_member_radius=EZSP_MULTICAST_NON_MEMBER_RADIUS
    ):
        """Submit and send data out as a multicast transmission.

        :param group_id: destination multicast address
        :param profile: Zigbee Profile ID to use for outgoing message
        :param cluster: cluster id where the message is being sent
        :param src_ep: source endpoint id
        :param sequence: transaction sequence number of the message
        :param data: Zigbee message payload
        :param hops: the message will be delivered to all nodes within this number of
                     hops of the sender. A value of zero is converted to MAX_HOPS
        :param non_member_radius: the number of hops that the message will be forwarded
                                  by devices that are not members of the group. A value
                                  of 7 or greater is treated as infinite
        :returns: return a tuple of a status and an error_message. Original requestor
                  has more context to provide a more meaningful error message
        """
        if not self.is_controller_running:
            raise ControllerError("ApplicationController is not running")

        aps_frame = t.EmberApsFrame()
        aps_frame.profileId = t.uint16_t(profile)
        aps_frame.clusterId = t.uint16_t(cluster)
        aps_frame.sourceEndpoint = t.uint8_t(src_ep)
        aps_frame.destinationEndpoint = t.uint8_t(src_ep)
        aps_frame.options = t.EmberApsOption(
            t.EmberApsOption.APS_OPTION_ENABLE_ROUTE_DISCOVERY
        )
        aps_frame.groupId = t.uint16_t(group_id)
        aps_frame.sequence = t.uint8_t(sequence)
        message_tag = self.get_sequence()

        with self._pending.new(message_tag) as req:
            async with self._in_flight_msg:
                res = await self._ezsp.sendMulticast(
                    aps_frame, hops, non_member_radius, message_tag, data
                )
                if res[0] != t.EmberStatus.SUCCESS:
                    return res[0], "EZSP sendMulticast failure: %s" % (res[0],)

                res = await asyncio.wait_for(req.result, APS_ACK_TIMEOUT)
        return res

    async def request(
        self,
        device,
        profile,
        cluster,
        src_ep,
        dst_ep,
        sequence,
        data,
        expect_reply=True,
        use_ieee=False,
    ):
        """Submit and send data out as an unicast transmission.

        :param device: destination device
        :param profile: Zigbee Profile ID to use for outgoing message
        :param cluster: cluster id where the message is being sent
        :param src_ep: source endpoint id
        :param dst_ep: destination endpoint id
        :param sequence: transaction sequence number of the message
        :param data: Zigbee message payload
        :param expect_reply: True if this is essentially a request
        :param use_ieee: use EUI64 for destination addressing
        :returns: return a tuple of a status and an error_message. Original requestor
                  has more context to provide a more meaningful error message
        """
        if not self.is_controller_running:
            raise ControllerError("ApplicationController is not running")

        aps_frame = t.EmberApsFrame()
        aps_frame.profileId = t.uint16_t(profile)
        aps_frame.clusterId = t.uint16_t(cluster)
        aps_frame.sourceEndpoint = t.uint8_t(src_ep)
        aps_frame.destinationEndpoint = t.uint8_t(dst_ep)
        aps_frame.options = self._tx_options
        aps_frame.groupId = t.uint16_t(0)
        aps_frame.sequence = t.uint8_t(sequence)
        message_tag = self.get_sequence()

        if use_ieee:
            LOGGER.warning(
                ("EUI64 addressing is not currently supported, " "reverting to NWK")
            )
        with self._pending.new(message_tag) as req:
            async with self._in_flight_msg:
                if expect_reply and device.node_desc.is_end_device in (True, None):
                    LOGGER.debug(
                        "Extending timeout for %s/0x%04x", device.ieee, device.nwk
                    )
                    await self._ezsp.setExtendedTimeout(device.ieee, True)
                if self.use_source_routing and device.relays is not None:
                    res = await self._ezsp.setSourceRoute(device.nwk, device.relays)
                    if res[0] != t.EmberStatus.SUCCESS:
                        LOGGER.warning(
                            "Couldn't set source route for %s: %s", device.nwk, res
                        )
                    else:
                        aps_frame.options = t.EmberApsOption(
                            aps_frame.options
                            ^ t.EmberApsOption.APS_OPTION_ENABLE_ROUTE_DISCOVERY
                        )
                        LOGGER.debug(
                            "Set source route for %s to %s: %s",
                            device.nwk,
                            device.relays,
                            res,
                        )
                res = await self._ezsp.sendUnicast(
                    self.direct, device.nwk, aps_frame, message_tag, data
                )
                if res[0] != t.EmberStatus.SUCCESS:
                    return res[0], "EZSP sendUnicast failure: %s" % (res[0],)

                res = await asyncio.wait_for(req.result, APS_ACK_TIMEOUT)
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

        link_key = t.EmberKeyData()
        link_key.contents = key
        v = await self._ezsp.addTransientLinkKey(node, link_key)

        if v[0] != t.EmberStatus.SUCCESS:
            raise Exception("Failed to set link key")

        v = await self._ezsp.setPolicy(
            t.EzspPolicyId.TC_KEY_REQUEST_POLICY,
            t.EzspDecisionId.GENERATE_NEW_TC_LINK_KEY,
        )
        if v[0] != t.EmberStatus.SUCCESS:
            raise Exception(
                "Failed to change policy to allow generation of new trust center keys"
            )

        return await self.permit(time_s)

    async def broadcast(
        self,
        profile,
        cluster,
        src_ep,
        dst_ep,
        grpid,
        radius,
        sequence,
        data,
        broadcast_address=BroadcastAddress.RX_ON_WHEN_IDLE,
    ):
        """Submit and send data out as an unicast transmission.

        :param profile: Zigbee Profile ID to use for outgoing message
        :param cluster: cluster id where the message is being sent
        :param src_ep: source endpoint id
        :param dst_ep: destination endpoint id
        :param: grpid: group id to address the broadcast to
        :param radius: max radius of the broadcast
        :param sequence: transaction sequence number of the message
        :param data: zigbee message payload
        :param timeout: how long to wait for transmission ACK
        :param broadcast_address: broadcast address.
        :returns: return a tuple of a status and an error_message. Original requestor
                  has more context to provide a more meaningful error message
        """
        if not self.is_controller_running:
            raise ControllerError("ApplicationController is not running")

        aps_frame = t.EmberApsFrame()
        aps_frame.profileId = t.uint16_t(profile)
        aps_frame.clusterId = t.uint16_t(cluster)
        aps_frame.sourceEndpoint = t.uint8_t(src_ep)
        aps_frame.destinationEndpoint = t.uint8_t(dst_ep)
        aps_frame.options = t.EmberApsOption(t.EmberApsOption.APS_OPTION_NONE)
        aps_frame.groupId = t.uint16_t(grpid)
        aps_frame.sequence = t.uint8_t(sequence)
        message_tag = self.get_sequence()

        with self._pending.new(message_tag) as req:
            async with self._in_flight_msg:
                res = await self._ezsp.sendBroadcast(
                    broadcast_address, aps_frame, radius, message_tag, data
                )
                if res[0] != t.EmberStatus.SUCCESS:
                    return res[0], "broadcast send failure"

                # Wait for messageSentHandler message
                res = await asyncio.wait_for(req.result, timeout=APS_ACK_TIMEOUT)
        return res

    async def _watchdog(self):
        """Watchdog handler."""
        LOGGER.debug("Starting EZSP watchdog")
        failures = 0
        await asyncio.sleep(WATCHDOG_WAKE_PERIOD)
        while True:
            try:
                await asyncio.wait_for(
                    self.controller_event.wait(), timeout=WATCHDOG_WAKE_PERIOD * 2
                )
                await self._ezsp.nop()
                failures = 0
            except (asyncio.TimeoutError, EzspError) as exc:
                LOGGER.warning("Watchdog heartbeat timeout: %s", str(exc))
                failures += 1
                if failures > MAX_WATCHDOG_FAILURES:
                    break
            await asyncio.sleep(WATCHDOG_WAKE_PERIOD)

        self._handle_reset_request(
            "Watchdog timeout. Heartbeat timeouts: {}".format(failures)
        )

    def handle_route_record(
        self,
        nwk: t.EmberNodeId,
        ieee: t.EmberEUI64,
        lqi: t.uint8_t,
        rssi: t.int8s,
        relays: t.LVList(t.EmberNodeId),
    ) -> None:
        LOGGER.debug(
            "Processing route record request: %s", (nwk, ieee, lqi, rssi, relays)
        )
        try:
            dev = self.get_device(ieee=ieee)
        except KeyError:
            LOGGER.debug("Why we don't have a device for %s ieee and %s NWK", ieee, nwk)
            self.handle_join(nwk, ieee, 0)
            return
        dev.relays = relays

    def handle_route_error(self, status: t.EmberStatus, nwk: t.EmberNodeId) -> None:
        LOGGER.debug("Processing route error: status=%s, nwk=%s", status, nwk)
        try:
            dev = self.get_device(nwk=nwk)
        except KeyError:
            LOGGER.debug("No %s device found", nwk)
            return
        dev.relays = None


class EZSPCoordinator(CustomDevice):
    """Zigpy Device representing Coordinator."""

    class EZSPEndpoint(CustomEndpoint):
        async def add_to_group(self, grp_id: int, name: str = None) -> t.EmberStatus:
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
        "endpoints": {
            1: {
                "profile_id": 0x0104,
                "device_type": 0xBEEF,
                "input_clusters": [],
                "output_clusters": [zigpy.zcl.clusters.security.IasZone.cluster_id],
            }
        }
    }

    replacement = {
        "manufacturer": "Silicon Labs",
        "model": "EZSP",
        "endpoints": {1: (EZSPEndpoint, {})},
    }
