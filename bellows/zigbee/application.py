from __future__ import annotations

import asyncio
import logging
import os
from typing import Dict, Optional

import zigpy.application
import zigpy.config
import zigpy.device
import zigpy.endpoint
from zigpy.exceptions import FormationFailure, NetworkNotFormed
import zigpy.state
import zigpy.types
import zigpy.util
import zigpy.zdo.types as zdo_t

import bellows
from bellows.config import (
    CONF_PARAM_MAX_WATCHDOG_FAILURES,
    CONFIG_SCHEMA,
    SCHEMA_DEVICE,
)
from bellows.exception import ControllerError, EzspError
import bellows.ezsp
from bellows.ezsp.v8.types.named import EmberDeviceUpdate
import bellows.multicast
import bellows.types as t
from bellows.zigbee.device import EZSPCoordinator, EZSPEndpoint
import bellows.zigbee.util as util

APS_ACK_TIMEOUT = 120
RETRY_DELAYS = [0.5, 1.0, 1.5]
COUNTER_EZSP_BUFFERS = "EZSP_FREE_BUFFERS"
COUNTER_NWK_CONFLICTS = "nwk_conflicts"
COUNTER_RESET_REQ = "reset_requests"
COUNTER_RESET_SUCCESS = "reset_success"
COUNTER_RX_BCAST = "broadcast_rx"
COUNTER_RX_MCAST = "multicast_rx"
COUNTER_RX_UNICAST = "unicast_rx"
COUNTER_UNKNOWN_DEVICE = "unknown_device_rx"
COUNTER_WATCHDOG = "watchdog_reset_requests"
COUNTERS_EZSP = "ezsp_counters"
COUNTERS_CTRL = "controller_app_counters"
DEFAULT_MFG_ID = 0x1049
EZSP_COUNTERS_CLEAR_IN_WATCHDOG_PERIODS = 180
EZSP_DEFAULT_RADIUS = 0
EZSP_MULTICAST_NON_MEMBER_RADIUS = 3
MFG_ID_RESET_DELAY = 180
RESET_ATTEMPT_BACKOFF_TIME = 5
WATCHDOG_WAKE_PERIOD = 10
IEEE_PREFIX_MFG_ID = {
    "04:cf:fc": 0x115F,
    "54:ef:44": 0x115F,
}

LOGGER = logging.getLogger(__name__)


class ControllerApplication(zigpy.application.ControllerApplication):
    probe = bellows.ezsp.EZSP.probe
    SCHEMA = CONFIG_SCHEMA
    SCHEMA_DEVICE = SCHEMA_DEVICE

    def __init__(self, config: Dict):
        super().__init__(config)
        self._ctrl_event = asyncio.Event()
        self._ezsp = None
        self._multicast = None
        self._mfg_id_task: asyncio.Task | None = None
        self._pending = zigpy.util.Requests()
        self._watchdog_task = None
        self._reset_task = None

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

    async def add_endpoint(self, descriptor: zdo_t.SimpleDescriptor) -> None:
        """Add endpoint."""
        res = await self._ezsp.addEndpoint(
            descriptor.endpoint,
            descriptor.profile,
            descriptor.device_type,
            descriptor.device_version,
            len(descriptor.input_clusters),
            len(descriptor.output_clusters),
            descriptor.input_clusters,
            descriptor.output_clusters,
        )
        LOGGER.debug("Ezsp adding endpoint: %s", res)

    async def cleanup_tc_link_key(self, ieee: t.EmberEUI64) -> None:
        """Remove tc link_key for the given device."""
        (index,) = await self._ezsp.findKeyTableEntry(ieee, True)
        if index != 0xFF:
            # found a key
            status = await self._ezsp.eraseKeyTableEntry(index)
            LOGGER.debug("Cleaned up TC link key for %s device: %s", ieee, status)

    async def _get_board_info(self) -> tuple[str, str, str] | tuple[None, None, None]:
        """Get the board info, handling errors when `getMfgToken` is not supported."""
        try:
            return await self._ezsp.get_board_info()
        except EzspError as exc:
            LOGGER.info("EZSP Radio does not support getMfgToken command: %r", exc)

        return None, None, None

    async def connect(self):
        self._ezsp = await bellows.ezsp.EZSP.initialize(self.config)
        ezsp = self._ezsp

        self._multicast = bellows.multicast.Multicast(ezsp)

        status, count = await ezsp.getConfigurationValue(
            ezsp.types.EzspConfigId.CONFIG_APS_UNICAST_MESSAGE_COUNT
        )
        assert status == t.EmberStatus.SUCCESS
        self._concurrent_requests_semaphore.max_value = count
        LOGGER.debug("APS_UNICAST_MESSAGE_COUNT is set to %s", count)

        await self.register_endpoints()

        brd_manuf, brd_name, version = await self._get_board_info()
        LOGGER.info("EZSP Radio manufacturer: %s", brd_manuf)
        LOGGER.info("EZSP Radio board name: %s", brd_name)
        LOGGER.info("EmberZNet version: %s", version)

    async def _ensure_network_running(self) -> bool:
        """
        Ensures the network is currently running and returns whether or not the network
        was started.
        """
        (state,) = await self._ezsp.networkState()

        if state == self._ezsp.types.EmberNetworkStatus.JOINED_NETWORK:
            return False

        (init_status,) = await self._ezsp.networkInit()
        if init_status != t.EmberStatus.SUCCESS:
            raise NetworkNotFormed(f"Failed to init network: {init_status!r}")

        return True

    async def start_network(self):
        ezsp = self._ezsp

        await self._ensure_network_running()

        await ezsp.update_policies(self.config)
        await self.load_network_info(load_devices=False)

        for cnt_group in self.state.counters:
            cnt_group.reset()

        # Device relays are cleared on startup when "source routing" on newer EmberZNet
        # to enable route discovery when first sending requests
        if self.config[zigpy.config.CONF_SOURCE_ROUTING] and ezsp.ezsp_version >= 8:
            for device in self.devices.values():
                device.relays = None

        ezsp.add_callback(self.ezsp_callback_handler)
        self.controller_event.set()
        self._watchdog_task = asyncio.create_task(self._watchdog())

        try:
            db_device = self.get_device(ieee=self.state.node_info.ieee)
        except KeyError:
            db_device = None

        ezsp_device = EZSPCoordinator(
            application=self,
            ieee=self.state.node_info.ieee,
            nwk=self.state.node_info.nwk,
        )
        self.devices[self.state.node_info.ieee] = ezsp_device

        # The coordinator device does not respond to attribute reads
        ezsp_device.endpoints[1] = EZSPEndpoint(ezsp_device, 1)
        ezsp_device.model = ezsp_device.endpoints[1].model
        ezsp_device.manufacturer = ezsp_device.endpoints[1].manufacturer
        await ezsp_device.schedule_initialize()

        # Group membership is stored in the database for EZSP coordinators
        if db_device is not None and 1 in db_device.endpoints:
            ezsp_device.endpoints[1].member_of.update(db_device.endpoints[1].member_of)

        await self.multicast.startup(ezsp_device)

    async def load_network_info(self, *, load_devices=False) -> None:
        ezsp = self._ezsp

        await self._ensure_network_running()

        status, node_type, nwk_params = await ezsp.getNetworkParameters()
        assert status == t.EmberStatus.SUCCESS

        if node_type != t.EmberNodeType.COORDINATOR:
            raise NetworkNotFormed("Device not configured as coordinator")

        (nwk,) = await ezsp.getNodeId()
        (ieee,) = await ezsp.getEui64()

        self.state.node_info = zigpy.state.NodeInfo(
            nwk=zigpy.types.NWK(nwk),
            ieee=zigpy.types.EUI64(ieee),
            logical_type=node_type.zdo_logical_type,
        )

        (status, security_level) = await ezsp.getConfigurationValue(
            ezsp.types.EzspConfigId.CONFIG_SECURITY_LEVEL
        )
        assert status == t.EmberStatus.SUCCESS
        security_level = zigpy.types.uint8_t(security_level)

        (status, network_key) = await ezsp.getKey(
            ezsp.types.EmberKeyType.CURRENT_NETWORK_KEY
        )
        assert status == t.EmberStatus.SUCCESS

        (status, ezsp_tc_link_key) = await ezsp.getKey(
            ezsp.types.EmberKeyType.TRUST_CENTER_LINK_KEY
        )
        assert status == t.EmberStatus.SUCCESS
        tc_link_key = util.ezsp_key_to_zigpy_key(ezsp_tc_link_key, ezsp)

        (status, state) = await ezsp.getCurrentSecurityState()
        assert status == t.EmberStatus.SUCCESS

        stack_specific = {}

        if (
            ezsp.types.EmberCurrentSecurityBitmask.TRUST_CENTER_USES_HASHED_LINK_KEY
            in state.bitmask
        ):
            stack_specific["ezsp"] = {"hashed_tclk": tc_link_key.key.serialize().hex()}
            tc_link_key.key = zigpy.types.KeyData(b"ZigBeeAlliance09")

        # The TCLK IEEE address is returned as `FF:FF:FF:FF:FF:FF:FF:FF`
        if self.state.node_info.logical_type == zdo_t.LogicalType.Coordinator:
            tc_link_key.partner_ieee = self.state.node_info.ieee

        brd_manuf, brd_name, version = await self._get_board_info()
        can_write_custom_eui64 = await ezsp.can_write_custom_eui64()

        self.state.network_info = zigpy.state.NetworkInfo(
            source=f"bellows@{bellows.__version__}",
            extended_pan_id=zigpy.types.ExtendedPanId(nwk_params.extendedPanId),
            pan_id=zigpy.types.PanId(nwk_params.panId),
            nwk_update_id=zigpy.types.uint8_t(nwk_params.nwkUpdateId),
            nwk_manager_id=zigpy.types.NWK(nwk_params.nwkManagerId),
            channel=zigpy.types.uint8_t(nwk_params.radioChannel),
            channel_mask=zigpy.types.Channels(nwk_params.channels),
            security_level=zigpy.types.uint8_t(security_level),
            network_key=util.ezsp_key_to_zigpy_key(network_key, ezsp),
            tc_link_key=tc_link_key,
            key_table=[],
            children=[],
            nwk_addresses={},
            stack_specific=stack_specific,
            metadata={
                "ezsp": {
                    "manufacturer": brd_manuf,
                    "board": brd_name,
                    "version": version,
                    "stack_version": ezsp.ezsp_version,
                    "can_write_custom_eui64": can_write_custom_eui64,
                }
            },
        )

        if not load_devices:
            return

        for idx in range(0, 192):
            (status, key) = await ezsp.getKeyTableEntry(idx)

            if status == t.EmberStatus.INDEX_OUT_OF_RANGE:
                break
            elif status == t.EmberStatus.TABLE_ENTRY_ERASED:
                continue

            assert status == t.EmberStatus.SUCCESS

            self.state.network_info.key_table.append(
                util.ezsp_key_to_zigpy_key(key, ezsp)
            )

        for idx in range(0, 255 + 1):
            (status, *rsp) = await ezsp.getChildData(idx)

            if status == t.EmberStatus.NOT_JOINED:
                continue

            if ezsp.ezsp_version >= 7:
                nwk = rsp[0].id
                eui64 = rsp[0].eui64
                node_type = rsp[0].type
            else:
                nwk, eui64, node_type = rsp

            self.state.network_info.children.append(eui64)
            self.state.network_info.nwk_addresses[eui64] = nwk

        # v4 can crash when getAddressTableRemoteNodeId(32) is received
        # Error code: undefined_0x8a
        if ezsp.ezsp_version == 4:
            return

        for idx in range(0, 255 + 1):
            (nwk,) = await ezsp.getAddressTableRemoteNodeId(idx)
            (eui64,) = await ezsp.getAddressTableRemoteEui64(idx)

            # Ignore invalid NWK entries
            if nwk in t.EmberDistinguishedNodeId.__members__.values():
                continue
            elif eui64 == t.EmberEUI64.convert("00:00:00:00:00:00:00:00"):
                continue

            self.state.network_info.nwk_addresses[
                zigpy.types.EUI64(eui64)
            ] = zigpy.types.NWK(nwk)

    async def write_network_info(
        self, *, network_info: zigpy.state.NetworkInfo, node_info: zigpy.state.NodeInfo
    ) -> None:
        ezsp = self._ezsp

        await self.reset_network_info()

        can_write_custom_eui64 = await ezsp.can_write_custom_eui64()
        stack_specific = network_info.stack_specific.get("ezsp", {})
        (current_eui64,) = await ezsp.getEui64()

        if (
            node_info.ieee != zigpy.types.EUI64.UNKNOWN
            and node_info.ieee != current_eui64
        ):
            should_update_eui64 = stack_specific.get(
                "i_understand_i_can_update_eui64_only_once_and_i_still_want_to_do_it"
            )

            if should_update_eui64 and not can_write_custom_eui64:
                LOGGER.error(
                    "Current node's IEEE address has already been written once. It"
                    " cannot be written again without fully erasing the chip with JTAG."
                )
            elif should_update_eui64:
                new_ncp_eui64 = t.EmberEUI64(node_info.ieee)
                (status,) = await ezsp.setMfgToken(
                    t.EzspMfgTokenId.MFG_CUSTOM_EUI_64, new_ncp_eui64.serialize()
                )
                assert status == t.EmberStatus.SUCCESS
            else:
                LOGGER.warning(
                    "Current node's IEEE address (%s) does not match the backup's (%s)",
                    current_eui64,
                    node_info.ieee,
                )

        use_hashed_tclk = ezsp.ezsp_version > 4

        if use_hashed_tclk and not stack_specific.get("hashed_tclk"):
            # Generate a random default
            network_info.stack_specific.setdefault("ezsp", {})[
                "hashed_tclk"
            ] = os.urandom(16).hex()

        initial_security_state = util.zha_security(
            network_info=network_info,
            node_info=node_info,
            use_hashed_tclk=use_hashed_tclk,
        )
        (status,) = await ezsp.setInitialSecurityState(initial_security_state)
        assert status == t.EmberStatus.SUCCESS

        # Clear the key table
        (status,) = await ezsp.clearKeyTable()
        assert status == t.EmberStatus.SUCCESS

        # Write APS link keys
        for key in network_info.key_table:
            ember_key = util.zigpy_key_to_ezsp_key(key, ezsp)

            # XXX: is there no way to set the outgoing frame counter or seq?
            (status,) = await ezsp.addOrUpdateKeyTableEntry(
                ember_key.partnerEUI64, True, ember_key.key
            )
            if status != t.EmberStatus.SUCCESS:
                LOGGER.warning("Couldn't add %s key: %s", key, status)

        if ezsp.ezsp_version > 4:
            # Set NWK frame counter
            (status,) = await ezsp.setValue(
                ezsp.types.EzspValueId.VALUE_NWK_FRAME_COUNTER,
                t.uint32_t(network_info.network_key.tx_counter).serialize(),
            )
            assert status == t.EmberStatus.SUCCESS

            # Set APS frame counter
            (status,) = await ezsp.setValue(
                ezsp.types.EzspValueId.VALUE_APS_FRAME_COUNTER,
                t.uint32_t(network_info.tc_link_key.tx_counter).serialize(),
            )
            assert status == t.EmberStatus.SUCCESS

        # Set the network settings
        parameters = t.EmberNetworkParameters()
        parameters.panId = t.EmberPanId(network_info.pan_id)
        parameters.extendedPanId = t.EmberEUI64(network_info.extended_pan_id)
        parameters.radioTxPower = t.uint8_t(8)
        parameters.radioChannel = t.uint8_t(network_info.channel)
        parameters.joinMethod = t.EmberJoinMethod.USE_MAC_ASSOCIATION
        parameters.nwkManagerId = t.EmberNodeId(network_info.nwk_manager_id)
        parameters.nwkUpdateId = t.uint8_t(network_info.nwk_update_id)
        parameters.channels = t.Channels(network_info.channel_mask)

        await ezsp.formNetwork(parameters)
        await ezsp.setValue(ezsp.types.EzspValueId.VALUE_STACK_TOKEN_WRITING, 1)

    async def reset_network_info(self):
        try:
            (status,) = await self._ezsp.leaveNetwork()
        except bellows.exception.EzspError:
            pass
        else:
            if status != t.EmberStatus.NETWORK_DOWN:
                raise FormationFailure("Couldn't leave network")

    async def disconnect(self):
        # TODO: how do you shut down the stack?
        self.controller_event.clear()
        if self._watchdog_task and not self._watchdog_task.done():
            LOGGER.debug("Cancelling watchdog")
            self._watchdog_task.cancel()
        if self._reset_task and not self._reset_task.done():
            self._reset_task.cancel()
        if self._ezsp is not None:
            self._ezsp.close()
            self._ezsp = None

    async def force_remove(self, dev):
        # This should probably be delivered to the parent device instead
        # of the device itself.
        await self._ezsp.removeDevice(dev.nwk, dev.ieee, dev.ieee)

    def ezsp_callback_handler(self, frame_name, args):
        LOGGER.debug("Received %s frame with %s", frame_name, args)
        if frame_name == "incomingMessageHandler":
            self._handle_frame(*args)
        elif frame_name == "messageSentHandler":
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
        message_type: t.EmberIncomingMessageType,
        aps_frame: t.EmberApsFrame,
        lqi: t.uint8_t,
        rssi: t.int8s,
        sender: t.EmberNodeId,
        binding_index: t.uint8_t,
        address_index: t.uint8_t,
        message: bytes,
    ) -> None:
        if message_type == t.EmberIncomingMessageType.INCOMING_BROADCAST:
            dst = zigpy.types.AddrModeAddress(
                addr_mode=zigpy.types.AddrMode.Broadcast,
                address=zigpy.types.BroadcastAddress.ALL_ROUTERS_AND_COORDINATOR,
            )
            self.state.counters[COUNTERS_CTRL][COUNTER_RX_BCAST].increment()
        elif message_type == t.EmberIncomingMessageType.INCOMING_MULTICAST:
            dst = zigpy.types.AddrModeAddress(
                addr_mode=zigpy.types.AddrMode.Group, address=aps_frame.groupId
            )
            self.state.counters[COUNTERS_CTRL][COUNTER_RX_MCAST].increment()
        elif message_type == t.EmberIncomingMessageType.INCOMING_UNICAST:
            dst = zigpy.types.AddrModeAddress(
                addr_mode=zigpy.types.AddrMode.NWK, address=self.state.node_info.nwk
            )
            self.state.counters[COUNTERS_CTRL][COUNTER_RX_UNICAST].increment()
        else:
            LOGGER.debug("Ignoring message type: %r", message_type)
            return

        self.packet_received(
            zigpy.types.ZigbeePacket(
                src=zigpy.types.AddrModeAddress(
                    addr_mode=zigpy.types.AddrMode.NWK,
                    address=sender,
                ),
                src_ep=aps_frame.sourceEndpoint,
                dst=dst,
                dst_ep=aps_frame.destinationEndpoint,
                tsn=aps_frame.sequence,
                profile_id=aps_frame.profileId,
                cluster_id=aps_frame.clusterId,
                data=zigpy.types.SerializableBytes(message),
                lqi=lqi,
                rssi=rssi,
            )
        )

    def _handle_frame_sent(
        self,
        message_type: t.EmberIncomingMessageType,
        destination: t.EmberNodeId,
        aps_frame: t.EmberApsFrame,
        message_tag: int,
        status: t.EmberStatus,
        message: bytes,
    ):
        if status == t.EmberStatus.SUCCESS:
            msg = "success"
        else:
            msg = "failure"

        if message_type in (
            t.EmberOutgoingMessageType.OUTGOING_BROADCAST,
            t.EmberOutgoingMessageType.OUTGOING_BROADCAST_WITH_ALIAS,
        ):
            cnt_name = f"broadcast_tx_{msg}"
        elif message_type in (
            t.EmberOutgoingMessageType.OUTGOING_MULTICAST,
            t.EmberOutgoingMessageType.OUTGOING_MULTICAST_WITH_ALIAS,
        ):
            cnt_name = f"multicast_tx_{msg}"
        elif message_type in (
            t.EmberOutgoingMessageType.OUTGOING_DIRECT,
            t.EmberOutgoingMessageType.OUTGOING_VIA_ADDRESS_TABLE,
        ):
            cnt_name = f"unicast_tx_{msg}"
        elif message_type == t.EmberOutgoingMessageType.OUTGOING_VIA_BINDING:
            cnt_name = f"via_binding_tx_{msg}"
        else:
            cnt_name = f"unknown_msg_type_{msg}"

        try:
            request = self._pending[message_tag]
            request.result.set_result((status, f"message send {msg}"))
            self.state.counters[COUNTERS_CTRL][cnt_name].increment()
        except KeyError:
            self.state.counters[COUNTERS_CTRL][f"{cnt_name}_unexpected"].increment()
            LOGGER.debug("Unexpected message send notification tag: %s", message_tag)
        except asyncio.InvalidStateError as exc:
            self.state.counters[COUNTERS_CTRL][f"{cnt_name}_duplicate"].increment()
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

        mfg_id = next(
            (
                mfgid
                for prefix, mfgid in IEEE_PREFIX_MFG_ID.items()
                if str(ieee).startswith(prefix)
            ),
            None,
        )
        if mfg_id is not None:
            if self._mfg_id_task and not self._mfg_id_task.done():
                self._mfg_id_task.cancel()
            self._mfg_id_task = asyncio.create_task(self._reset_mfg_id(mfg_id))
        self.handle_join(nwk, ieee, parent_nwk)

    async def _reset_mfg_id(self, mfg_id: int) -> None:
        """Resets manufacturer id if was temporary overridden by a joining device."""
        await self._ezsp.setManufacturerCode(mfg_id)
        await asyncio.sleep(MFG_ID_RESET_DELAY)
        await self._ezsp.setManufacturerCode(DEFAULT_MFG_ID)

    def _handle_reset_request(self, error):
        """Reinitialize application controller."""
        LOGGER.debug("Resetting ControllerApplication. Cause: %r", error)
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
            except Exception as exc:
                LOGGER.warning(
                    "ControllerApplication reset unsuccessful: %r",
                    exc,
                    exc_info=exc,
                )
            await asyncio.sleep(RESET_ATTEMPT_BACKOFF_TIME)

        self._reset_task = None
        self.state.counters[COUNTERS_CTRL][COUNTER_RESET_SUCCESS].increment()
        LOGGER.debug("ControllerApplication successfully reset")

    async def _reset_controller(self):
        """Reset Controller."""
        if self._ezsp is not None:
            self._ezsp.close()
            self._ezsp = None

        await asyncio.sleep(0.5)
        await self.connect()
        await self.initialize()

    async def _set_source_route(
        self, nwk: zigpy.types.NWK, relays: list[zigpy.types.NWK]
    ) -> bool:
        if self._ezsp.ezsp_version >= 8:
            # Pretend EmberZNet knows about the device's relays if they are set (i.e. we
            # did not receive a routing error)
            try:
                device = self.get_device(nwk=nwk)
            except KeyError:
                return False
            else:
                return device.relays is not None

        (res,) = await self._ezsp.setSourceRoute(nwk, relays)
        return res == t.EmberStatus.SUCCESS

    async def send_packet(self, packet: zigpy.types.ZigbeePacket) -> None:
        if not self.is_controller_running:
            raise ControllerError("ApplicationController is not running")

        LOGGER.debug("Sending packet %r", packet)

        try:
            device = self.get_device_with_address(packet.dst)
        except (KeyError, ValueError):
            device = None

        if packet.dst.addr_mode == zigpy.types.AddrMode.IEEE:
            LOGGER.warning("IEEE addressing is not supported, falling back to NWK")

            if device is None:
                raise ValueError(f"Cannot find device with ieee {packet.dst.address}")

            packet = packet.replace(
                dst=zigpy.types.AddrModeAddress(
                    addr_mode=zigpy.types.AddrMode.NWK, address=device.nwk
                )
            )

        aps_frame = t.EmberApsFrame()
        aps_frame.profileId = t.uint16_t(packet.profile_id)
        aps_frame.clusterId = t.uint16_t(packet.cluster_id)
        aps_frame.sourceEndpoint = t.uint8_t(packet.src_ep)
        aps_frame.destinationEndpoint = t.uint8_t(packet.dst_ep or 0)
        aps_frame.options = t.EmberApsOption.APS_OPTION_RETRY
        aps_frame.sequence = t.uint8_t(packet.tsn)

        if packet.dst.addr_mode == zigpy.types.AddrMode.Group:
            aps_frame.groupId = t.uint16_t(packet.dst.address)
        else:
            aps_frame.groupId = t.uint16_t(0x0000)

        if not self.config[zigpy.config.CONF_SOURCE_ROUTING]:
            aps_frame.options |= t.EmberApsOption.APS_OPTION_ENABLE_ROUTE_DISCOVERY

        message_tag = self.get_sequence()

        with self._pending.new(message_tag) as req:
            async with self._limit_concurrency():
                for attempt, retry_delay in enumerate(RETRY_DELAYS):
                    async with self._req_lock:
                        if packet.dst.addr_mode == zigpy.types.AddrMode.NWK:
                            if packet.extended_timeout and device is not None:
                                await self._ezsp.setExtendedTimeout(device.ieee, True)

                            if (
                                packet.source_route is not None
                                and not await self._set_source_route(
                                    packet.dst.address, packet.source_route
                                )
                            ):
                                aps_frame.options |= (
                                    t.EmberApsOption.APS_OPTION_ENABLE_ROUTE_DISCOVERY
                                )

                            status, _ = await self._ezsp.sendUnicast(
                                t.EmberOutgoingMessageType.OUTGOING_DIRECT,
                                t.EmberNodeId(packet.dst.address),
                                aps_frame,
                                message_tag,
                                packet.data.serialize(),
                            )
                        elif packet.dst.addr_mode == zigpy.types.AddrMode.Group:
                            status, _ = await self._ezsp.sendMulticast(
                                aps_frame,
                                packet.radius,
                                packet.non_member_radius,
                                message_tag,
                                packet.data.serialize(),
                            )
                        elif packet.dst.addr_mode == zigpy.types.AddrMode.Broadcast:
                            status, _ = await self._ezsp.sendBroadcast(
                                t.EmberNodeId(packet.dst.address),
                                aps_frame,
                                packet.radius,
                                message_tag,
                                packet.data.serialize(),
                            )

                    if status == t.EmberStatus.SUCCESS:
                        break
                    elif status not in (
                        t.EmberStatus.MAX_MESSAGE_LIMIT_REACHED,
                        t.EmberStatus.NO_BUFFERS,
                        t.EmberStatus.NETWORK_BUSY,
                    ):
                        raise zigpy.exceptions.DeliveryError(
                            f"Failed to enqueue message: {status!r}", status
                        )
                    else:
                        if attempt < len(RETRY_DELAYS):
                            LOGGER.debug(
                                "Request %s failed to enqueue, retrying in %ss: %s",
                                message_tag,
                                retry_delay,
                                status,
                            )
                            await asyncio.sleep(retry_delay)
                else:
                    raise zigpy.exceptions.DeliveryError(
                        (
                            f"Failed to enqueue message after {len(RETRY_DELAYS)}"
                            f" attempts: {status!r}"
                        ),
                        status,
                    )

                # Wait for `messageSentHandler` message
                send_status, _ = await asyncio.wait_for(
                    req.result, timeout=APS_ACK_TIMEOUT
                )

                # Only throw a delivery exception for packets sent with NWK addressing
                # https://github.com/home-assistant/core/issues/79832
                if (
                    send_status != t.EmberStatus.SUCCESS
                    and packet.dst.addr_mode == zigpy.types.AddrMode.NWK
                ):
                    raise zigpy.exceptions.DeliveryError(
                        f"Failed to deliver message: {send_status!r}", send_status
                    )

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

        if self._ezsp.ezsp_version >= 8:
            mask_type = self._ezsp.types.EzspDecisionBitmask.ALLOW_JOINS
            bitmask = mask_type.ALLOW_JOINS | mask_type.JOINS_USE_INSTALL_CODE_KEY
            await self._ezsp.setPolicy(
                self._ezsp.types.EzspPolicyId.TRUST_CENTER_POLICY, bitmask
            )

        return await super().permit(time_s)

    def _handle_id_conflict(self, nwk: t.EmberNodeId) -> None:
        LOGGER.warning("NWK conflict is reported for 0x%04x", nwk)
        self.state.counters[COUNTERS_CTRL][COUNTER_NWK_CONFLICTS].increment()
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

    async def _watchdog(self):
        """Watchdog handler."""
        LOGGER.debug("Starting EZSP watchdog")
        failures = 0
        read_counter = 0
        await asyncio.sleep(WATCHDOG_WAKE_PERIOD)
        while True:
            try:
                await asyncio.wait_for(
                    self.controller_event.wait(), timeout=WATCHDOG_WAKE_PERIOD * 2
                )
                if self._ezsp.ezsp_version == 4:
                    await self._ezsp.nop()
                else:
                    counters = self.state.counters[COUNTERS_EZSP]
                    read_counter = (
                        read_counter + 1
                    ) % EZSP_COUNTERS_CLEAR_IN_WATCHDOG_PERIODS
                    if read_counter:
                        (res,) = await self._ezsp.readCounters()
                    else:
                        (res,) = await self._ezsp.readAndClearCounters()

                    for cnt_type, value in zip(self._ezsp.types.EmberCounterType, res):
                        counters[cnt_type.name[8:]].update(value)

                    if not read_counter:
                        counters.reset()

                    free_buffers = await self._get_free_buffers()
                    if free_buffers is not None:
                        cnt = counters[COUNTER_EZSP_BUFFERS]
                        cnt._raw_value = free_buffers
                        cnt._last_reset_value = 0

                    LOGGER.debug("%s", counters)

                failures = 0
            except (asyncio.TimeoutError, EzspError) as exc:
                LOGGER.warning("Watchdog heartbeat timeout: %s", repr(exc))
                failures += 1
                if failures > self.config[CONF_PARAM_MAX_WATCHDOG_FAILURES]:
                    break
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                LOGGER.error(
                    "Watchdog got an unexpected exception. Please report this issue: %s",
                    exc,
                )

            await asyncio.sleep(WATCHDOG_WAKE_PERIOD)

        self.state.counters[COUNTERS_CTRL][COUNTER_WATCHDOG].increment()
        self._handle_reset_request(f"Watchdog timeout. Heartbeat timeouts: {failures}")

    async def _get_free_buffers(self) -> Optional[int]:
        status, value = await self._ezsp.getValue(
            self._ezsp.types.EzspValueId.VALUE_FREE_BUFFERS
        )

        if status != t.EzspStatus.SUCCESS:
            return None

        buffers = int.from_bytes(value, byteorder="little")

        LOGGER.debug("Free buffers status %s, value: %s", status, buffers)
        return buffers

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
        self.handle_relays(nwk=nwk, relays=relays)

    def handle_route_error(self, status: t.EmberStatus, nwk: t.EmberNodeId) -> None:
        LOGGER.debug("Processing route error: status=%s, nwk=%s", status, nwk)
        self.handle_relays(nwk=nwk, relays=None)
