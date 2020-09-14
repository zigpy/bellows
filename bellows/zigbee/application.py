import asyncio
import logging
import os
from typing import Dict

from bellows.config import (
    CONF_PARAM_SRC_RTG,
    CONF_PARAM_UNK_DEV,
    CONFIG_SCHEMA,
    SCHEMA_DEVICE,
)
from bellows.exception import ControllerError, EzspError
import bellows.ezsp
from bellows.ezsp.v8.types.named import EmberDeviceUpdate
import bellows.multicast
import bellows.types as t
import bellows.zigbee.util
from serial import SerialException
import zigpy.application
import zigpy.config
import zigpy.device
from zigpy.quirks import CustomDevice, CustomEndpoint
from zigpy.types import BroadcastAddress
import zigpy.util
import zigpy.zdo.types as zdo_t

APS_ACK_TIMEOUT = 120
EZSP_DEFAULT_RADIUS = 0
EZSP_MULTICAST_NON_MEMBER_RADIUS = 3
MAX_WATCHDOG_FAILURES = 4
RESET_ATTEMPT_BACKOFF_TIME = 5
WATCHDOG_WAKE_PERIOD = 10

LOGGER = logging.getLogger(__name__)


class ControllerApplication(zigpy.application.ControllerApplication):
    direct = t.EmberOutgoingMessageType.OUTGOING_DIRECT
    probe = bellows.ezsp.EZSP.probe
    SCHEMA = CONFIG_SCHEMA
    SCHEMA_DEVICE = SCHEMA_DEVICE

    def __init__(self, config: Dict):
        super().__init__(config)
        self._ctrl_event = asyncio.Event()
        self._ezsp = None
        self._multicast = None
        self._pending = zigpy.util.Requests()
        self._watchdog_task = None
        self._reset_task = None
        self._in_flight_msg = None
        self._tx_options = (
            t.EmberApsOption.APS_OPTION_RETRY
            | t.EmberApsOption.APS_OPTION_ENABLE_ROUTE_DISCOVERY
        )

        self.use_source_routing = self.config[CONF_PARAM_SRC_RTG]
        self._req_lock = asyncio.Lock()

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

    async def cleanup_tc_link_key(self, ieee: t.EmberEUI64) -> None:
        """Remove tc link_key for the given device."""
        (index,) = await self._ezsp.findKeyTableEntry(ieee, True)
        if index != 0xFF:
            # found a key
            status = await self._ezsp.eraseKeyTableEntry(index)
            LOGGER.debug("Cleaned up TC link key for %s device: %s", ieee, status)

    async def startup(self, auto_form=False):
        """Perform a complete application startup"""
        self._ezsp = await bellows.ezsp.EZSP.initialize(self.config)
        ezsp = self._ezsp

        self._multicast = bellows.multicast.Multicast(ezsp)

        status, count = await ezsp.getConfigurationValue(
            ezsp.types.EzspConfigId.CONFIG_APS_UNICAST_MESSAGE_COUNT
        )
        assert status == t.EmberStatus.SUCCESS
        self._in_flight_msg = asyncio.Semaphore(count)
        LOGGER.debug("APS_UNICAST_MESSAGE_COUNT is set to %s", count)

        await self.add_endpoint(
            output_clusters=[zigpy.zcl.clusters.security.IasZone.cluster_id]
        )

        brd_manuf, brd_name, version = await self._ezsp.get_board_info()
        LOGGER.info("EZSP Radio manufacturer: %s", brd_manuf)
        LOGGER.info("EZSP Radio board name: %s", brd_name)
        LOGGER.info("EmberZNet version: %s", version)

        v = await ezsp.networkInit()
        if v[0] != t.EmberStatus.SUCCESS:
            if not auto_form:
                raise Exception("Could not initialize network")
            await self.form_network()

        status, node_type, nwk_params = await ezsp.getNetworkParameters()
        assert status == t.EmberStatus.SUCCESS  # TODO: Better check
        if node_type != t.EmberNodeType.COORDINATOR:
            if not auto_form:
                raise Exception("Network not configured as coordinator")

            LOGGER.info("Forming network")
            await self._ezsp.leaveNetwork()
            await asyncio.sleep(1)  # TODO
            await self.form_network()
            status, node_type, nwk_params = await ezsp.getNetworkParameters()
            assert status == t.EmberStatus.SUCCESS

        LOGGER.info("Node type: %s, Network parameters: %s", node_type, nwk_params)

        await ezsp.update_policies(self.config)
        nwk = await ezsp.getNodeId()
        self._nwk = nwk[0]
        ieee = await ezsp.getEui64()
        self._ieee = ieee[0]

        ezsp.add_callback(self.ezsp_callback_handler)
        self.controller_event.set()
        self._watchdog_task = asyncio.create_task(self._watchdog())

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
        if self._ezsp is not None:
            self._ezsp.close()

    async def form_network(self):
        nwk = self.config[zigpy.config.CONF_NWK]

        pan_id = nwk[zigpy.config.CONF_NWK_PAN_ID]
        if pan_id is None:
            pan_id = int.from_bytes(os.urandom(2), byteorder="little")

        extended_pan_id = nwk[zigpy.config.CONF_NWK_EXTENDED_PAN_ID]
        if extended_pan_id is None:
            extended_pan_id = t.EmberEUI64([t.uint8_t(0)] * 8)

        hashed_tclk = self._ezsp.ezsp_version > 4
        initial_security_state = bellows.zigbee.util.zha_security(
            nwk, controller=True, hashed_tclk=hashed_tclk
        )
        v = await self._ezsp.setInitialSecurityState(initial_security_state)
        assert v[0] == t.EmberStatus.SUCCESS  # TODO: Better check
        parameters = t.EmberNetworkParameters()
        parameters.panId = t.EmberPanId(pan_id)
        parameters.extendedPanId = extended_pan_id
        parameters.radioTxPower = t.uint8_t(8)
        parameters.radioChannel = t.uint8_t(nwk[zigpy.config.CONF_NWK_CHANNEL])
        parameters.joinMethod = t.EmberJoinMethod.USE_MAC_ASSOCIATION
        parameters.nwkManagerId = t.EmberNodeId(0)
        parameters.nwkUpdateId = t.uint8_t(nwk[zigpy.config.CONF_NWK_UPDATE_ID])
        parameters.channels = nwk[zigpy.config.CONF_NWK_CHANNELS]

        await self._ezsp.formNetwork(parameters)
        await self._ezsp.setValue(
            self._ezsp.types.EzspValueId.VALUE_STACK_TOKEN_WRITING, 1
        )

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
            self._handle_tc_join_handler(*args)
        elif frame_name == "incomingRouteRecordHandler":
            self.handle_route_record(*args)
        elif frame_name == "incomingRouteErrorHandler":
            self.handle_route_error(*args)
        elif frame_name == "_reset_controller_application":
            self._handle_reset_request(*args)
        elif frame_name == "idConflictHandler":
            self._handle_id_conflict(*args)

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
            if self.config[CONF_PARAM_UNK_DEV]:
                asyncio.create_task(self._handle_no_such_device(sender))
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

    async def _handle_no_such_device(self, sender: int) -> None:
        """Try to match unknown device by its EUI64 address."""
        status, ieee = await self._ezsp.lookupEui64ByNodeId(sender)
        if status == t.EmberStatus.SUCCESS:
            LOGGER.debug("Found %s ieee for %s sender", ieee, sender)
            self.handle_join(sender, ieee, 0)
            return
        LOGGER.debug("Couldn't look up ieee for %s", sender)

    def _handle_tc_join_handler(
        self,
        nwk: t.EmberNodeId,
        ieee: t.EmberEUI64,
        device_update_status: EmberDeviceUpdate,
        decision: t.EmberJoinDecision,
        parent_nwk: t.EmberNodeId,
    ) -> None:
        """Trust Center Join handler."""
        if device_update_status == EmberDeviceUpdate.DEVICE_LEFT:
            self.handle_leave(nwk, ieee)
            return

        if device_update_status == EmberDeviceUpdate.STANDARD_SECURITY_UNSECURED_JOIN:
            asyncio.create_task(self.cleanup_tc_link_key(ieee))

        if decision == t.EmberJoinDecision.DENY_JOIN:
            # no point in handling the join if it was denied
            return

        self.handle_join(nwk, ieee, parent_nwk)

    def _handle_reset_request(self, error):
        """Reinitialize application controller."""
        LOGGER.debug("Resetting ControllerApplication. Cause: '%s'", error)
        self.controller_event.clear()
        if self._reset_task:
            LOGGER.debug("Preempting ControllerApplication reset")
            self._reset_task.cancel()

        self._reset_task = asyncio.create_task(self._reset_controller_loop())

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
        non_member_radius=EZSP_MULTICAST_NON_MEMBER_RADIUS,
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
        aps_frame.options = t.EmberApsOption.APS_OPTION_ENABLE_ROUTE_DISCOVERY
        aps_frame.groupId = t.uint16_t(group_id)
        aps_frame.sequence = t.uint8_t(sequence)
        message_tag = self.get_sequence()

        with self._pending.new(message_tag) as req:
            async with self._in_flight_msg:
                async with self._req_lock:
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
                delays = [0.5, 1.0, 1.5]
                while True:
                    async with self._req_lock:
                        if expect_reply and device.node_desc.is_end_device in (
                            True,
                            None,
                        ):
                            LOGGER.debug(
                                "Extending timeout for %s/0x%04x",
                                device.ieee,
                                device.nwk,
                            )
                            await self._ezsp.setExtendedTimeout(device.ieee, True)
                        if self.use_source_routing and self._ezsp.ezsp_version < 8:
                            (res,) = await self._ezsp.set_source_route(device)
                            if res == t.EmberStatus.SUCCESS:
                                aps_frame.options ^= (
                                    t.EmberApsOption.APS_OPTION_ENABLE_ROUTE_DISCOVERY
                                )
                                LOGGER.debug(
                                    "Set source route for %s to %s: %s",
                                    device.nwk,
                                    device.relays,
                                    res,
                                )
                            else:
                                LOGGER.debug(
                                    "using route discovery for %s device",
                                    device.nwk,
                                )

                        status, _ = await self._ezsp.sendUnicast(
                            self.direct, device.nwk, aps_frame, message_tag, data
                        )
                    if not (
                        status == t.EmberStatus.MAX_MESSAGE_LIMIT_REACHED and delays
                    ):
                        # retry only on MAX_MESSAGE_LIMIT_REACHED if tries are left
                        break

                    delay = delays.pop(0)
                    LOGGER.debug("retrying request %s tag in %ss", message_tag, delay)
                    await asyncio.sleep(delay)

                if status != t.EmberStatus.SUCCESS:
                    return status, f"EZSP sendUnicast failure: {str(status)}"

                res = await asyncio.wait_for(req.result, APS_ACK_TIMEOUT)
        return res

    async def permit(self, time_s: int = 60, node: t.EmberNodeId = None) -> None:
        """Permit joining."""
        asyncio.create_task(self._ezsp.pre_permit(time_s))
        await super().permit(time_s, node)

    def permit_ncp(self, time_s=60):
        assert 0 <= time_s <= 254
        return self._ezsp.permitJoining(time_s)

    async def permit_with_key(self, node, code, time_s=60):
        if type(node) is not t.EmberEUI64:
            node = t.EmberEUI64([t.uint8_t(p) for p in node])

        key = zigpy.util.convert_install_code(code)
        if key is None:
            raise Exception("Invalid install code")

        link_key = t.EmberKeyData(key)
        v = await self._ezsp.addTransientLinkKey(node, link_key)

        if v[0] != t.EmberStatus.SUCCESS:
            raise Exception("Failed to set link key")

        v = await self._ezsp.setPolicy(
            self._ezsp.types.EzspPolicyId.TC_KEY_REQUEST_POLICY,
            self._ezsp.types.EzspDecisionId.GENERATE_NEW_TC_LINK_KEY,
        )
        if v[0] != t.EmberStatus.SUCCESS:
            raise Exception(
                "Failed to change policy to allow generation of new trust center keys"
            )

        return await self.permit(time_s)

    def _handle_id_conflict(self, nwk: t.EmberNodeId) -> None:
        LOGGER.warning("NWK conflict is reported for 0x%04x", nwk)
        for device in self.devices.values():
            if device.nwk != nwk:
                continue
            LOGGER.warning(
                "Found %s device for 0x%04x NWK conflict: %s %s",
                device.ieee,
                nwk,
                device.manufacturer,
                device.model,
            )
            self.handle_leave(nwk, device.ieee)

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
        aps_frame.options = t.EmberApsOption.APS_OPTION_NONE
        aps_frame.groupId = t.uint16_t(grpid)
        aps_frame.sequence = t.uint8_t(sequence)
        message_tag = self.get_sequence()

        with self._pending.new(message_tag) as req:
            async with self._in_flight_msg:
                async with self._req_lock:
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
                if LOGGER.level < logging.DEBUG:
                    await self._ezsp.nop()
                else:
                    (res,) = await self._ezsp.readCounters()
                    counters = (
                        f"{counter.name}: {value}"
                        for counter, value in zip(
                            self._ezsp.types.EmberCounterType, res
                        )
                    )
                    LOGGER.debug("EZSP Counters: %s", ",".join(counters))
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
        @property
        def manufacturer(self) -> str:
            """Manufacturer."""
            return "Silicon Labs"

        @property
        def model(self) -> str:
            """Model."""
            return "EZSP"

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
        "endpoints": {1: (EZSPEndpoint, {})},
        "manufacturer": "Silicon Labs",
        "model": "EZSP",
    }
