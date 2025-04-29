from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import logging
import os
import statistics
import sys
from typing import AsyncGenerator

if sys.version_info[:2] < (3, 11):
    from async_timeout import timeout as asyncio_timeout  # pragma: no cover
else:
    from asyncio import timeout as asyncio_timeout  # pragma: no cover

import importlib.metadata

import zigpy.application
import zigpy.config
import zigpy.device
import zigpy.endpoint
from zigpy.exceptions import NetworkNotFormed
import zigpy.state
import zigpy.types
import zigpy.util
import zigpy.zdo.types as zdo_t

import bellows
from bellows.config import (
    CONF_BELLOWS_CONFIG,
    CONF_EZSP_CONFIG,
    CONF_EZSP_POLICIES,
    CONF_MANUAL_SOURCE_ROUTING,
    CONF_USE_THREAD,
    CONFIG_SCHEMA,
)
from bellows.exception import ControllerError, EzspError, StackAlreadyRunning
import bellows.ezsp
from bellows.ezsp.xncp import FirmwareFeatures
import bellows.multicast
import bellows.types as t
from bellows.zigbee import repairs
from bellows.zigbee.device import EZSPEndpoint, EZSPGroupEndpoint
import bellows.zigbee.util as util

MESSAGE_SEND_TIMEOUT_MAINS = 3
MESSAGE_SEND_TIMEOUT_BATTERY = 8

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
NETWORK_UP_TIMEOUT_S = 10
MAX_WATCHDOG_FAILURES = 4
IEEE_PREFIX_MFG_ID = {
    "04:CF:8C": 0x115F,  # Xiaomi
    "54:EF:44": 0x115F,  # Lumi
}

LIB_VERSION = importlib.metadata.version("bellows")
LOGGER = logging.getLogger(__name__)


class ControllerApplication(zigpy.application.ControllerApplication):
    SCHEMA = CONFIG_SCHEMA

    _watchdog_period = 10
    _probe_configs = [
        {zigpy.config.CONF_DEVICE_BAUDRATE: 115200},
        {zigpy.config.CONF_DEVICE_BAUDRATE: 57600},
    ]

    def __init__(self, config: dict) -> None:
        super().__init__(config)
        self._ctrl_event = asyncio.Event()
        self._created_device_endpoints: list[zdo_t.SimpleDescriptor] = []
        self._ezsp = None
        self._multicast = None
        self._mfg_id_task: asyncio.Task | None = None
        self._pending = zigpy.util.Requests()
        self._watchdog_failures = 0
        self._watchdog_feed_counter = 0

        self._req_lock = asyncio.Lock()
        self._packet_capture_channel: int | None = None

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
        (status,) = await self._ezsp.addEndpoint(
            endpoint=descriptor.endpoint,
            profileId=descriptor.profile,
            deviceId=descriptor.device_type,
            deviceVersion=descriptor.device_version,
            inputClusterCount=len(descriptor.input_clusters),
            outputClusterCount=len(descriptor.output_clusters),
            inputClusterList=descriptor.input_clusters,
            outputClusterList=descriptor.output_clusters,
        )

        if t.sl_Status.from_ember_status(status) != t.sl_Status.OK:
            raise StackAlreadyRunning()

        self._created_device_endpoints.append(descriptor)

    async def cleanup_tc_link_key(self, ieee: t.EUI64) -> None:
        """Remove tc link_key for the given device."""
        (index,) = await self._ezsp.findKeyTableEntry(address=ieee, linkKey=True)
        if index != 0xFF:
            # found a key
            status = await self._ezsp.eraseKeyTableEntry(index=index)
            LOGGER.debug("Cleaned up TC link key for %s device: %s", ieee, status)

    async def _get_board_info(self) -> tuple[str, str, str] | tuple[None, None, None]:
        """Get the board info, handling errors when `getMfgToken` is not supported."""
        try:
            return await self._ezsp.get_board_info()
        except EzspError as exc:
            LOGGER.info("EZSP Radio does not support getMfgToken command: %r", exc)

        return None, None, None

    async def connect(self) -> None:
        self._ezsp = bellows.ezsp.EZSP(self.config[zigpy.config.CONF_DEVICE], self)

        try:
            await self._ezsp.connect(use_thread=self.config[CONF_USE_THREAD])

            # Writing config is required here because network info can't be loaded
            await self._ezsp.write_config(self.config[CONF_EZSP_CONFIG])

            self._created_device_endpoints.clear()
            await self.register_endpoints()
        except Exception:
            if self._ezsp is not None:
                await self._ezsp.disconnect()
                self._ezsp = None
            raise

    async def _ensure_network_running(self) -> bool:
        """Ensures the network is currently running and returns whether or not the network
        was started.
        """
        (state,) = await self._ezsp.networkState()

        if state == t.EmberNetworkStatus.JOINED_NETWORK:
            return False

        with self._ezsp.wait_for_stack_status(t.sl_Status.NETWORK_UP) as stack_status:
            init_status = await self._ezsp.initialize_network()

            if init_status == t.sl_Status.NOT_JOINED:
                raise NetworkNotFormed("Node is not part of a network")
            elif init_status != t.sl_Status.OK:
                raise ControllerError(f"Failed to initialize network: {init_status!r}")

            async with asyncio_timeout(NETWORK_UP_TIMEOUT_S):
                await stack_status

        return True

    async def start_network(self):
        ezsp = self._ezsp

        await self._ensure_network_running()

        if await repairs.fix_invalid_tclk_partner_ieee(ezsp):
            await self._reset()
            await self._ensure_network_running()

        if self.config[zigpy.config.CONF_SOURCE_ROUTING]:
            await ezsp.set_source_routing()

        await ezsp._protocol.update_policies(self.config[CONF_EZSP_POLICIES])
        await self.load_network_info(load_devices=False)

        for cnt_group in self.state.counters:
            cnt_group.reset()

        ezsp.add_callback(self.ezsp_callback_handler)
        self.controller_event.set()

        group_membership = {}

        if FirmwareFeatures.MEMBER_OF_ALL_GROUPS in self._ezsp._xncp_features:
            # If the firmware passes through all incoming group messages, do nothing
            endpoint_cls = EZSPEndpoint
        else:
            endpoint_cls = EZSPGroupEndpoint

            try:
                db_device = self.get_device(ieee=self.state.node_info.ieee)
            except KeyError:
                pass
            else:
                if 1 in db_device.endpoints:
                    group_membership = db_device.endpoints[1].member_of

        ezsp_device = zigpy.device.Device(
            application=self,
            ieee=self.state.node_info.ieee,
            nwk=self.state.node_info.nwk,
        )
        self.devices[self.state.node_info.ieee] = ezsp_device

        # The coordinator device does not respond to attribute reads so we have to
        # divine the internal NCP state.
        for zdo_desc in self._created_device_endpoints:
            ep = endpoint_cls.from_descriptor(ezsp_device, zdo_desc.endpoint, zdo_desc)
            ezsp_device.endpoints[zdo_desc.endpoint] = ep
            ezsp_device.model = ep.model
            ezsp_device.manufacturer = ep.manufacturer

        await ezsp_device.schedule_initialize()

        if FirmwareFeatures.MEMBER_OF_ALL_GROUPS not in self._ezsp._xncp_features:
            ezsp_device.endpoints[1].member_of.update(group_membership)
            self._multicast = bellows.multicast.Multicast(ezsp)
            await self._multicast.startup(ezsp_device)

    async def load_network_info(self, *, load_devices=False) -> None:
        ezsp = self._ezsp

        await self._ensure_network_running()

        status, node_type, nwk_params = await ezsp.getNetworkParameters()
        assert t.sl_Status.from_ember_status(status) == t.sl_Status.OK

        if node_type != t.EmberNodeType.COORDINATOR:
            raise NetworkNotFormed("Device not configured as coordinator")

        (nwk,) = await ezsp.getNodeId()
        (ieee,) = await ezsp.getEui64()

        brd_manuf, brd_name, version = await self._get_board_info()

        self.state.node_info = zigpy.state.NodeInfo(
            nwk=zigpy.types.NWK(nwk),
            ieee=zigpy.types.EUI64(ieee),
            logical_type=node_type.zdo_logical_type,
            manufacturer=brd_manuf,
            model=brd_name,
            version=version,
        )

        (status, security_level) = await ezsp.getConfigurationValue(
            configId=t.EzspConfigId.CONFIG_SECURITY_LEVEL
        )
        assert t.sl_Status.from_ember_status(status) == t.sl_Status.OK
        security_level = zigpy.types.uint8_t(security_level)

        network_key = await ezsp.get_network_key()
        tc_link_key = await ezsp.get_tc_link_key()

        (status, state) = await ezsp.getCurrentSecurityState()
        assert t.sl_Status.from_ember_status(status) == t.sl_Status.OK

        stack_specific = {}

        if (
            t.EmberCurrentSecurityBitmask.TRUST_CENTER_USES_HASHED_LINK_KEY
            in state.bitmask
        ):
            stack_specific["ezsp"] = {"hashed_tclk": tc_link_key.key.serialize().hex()}
            tc_link_key.key = zigpy.types.KeyData(b"ZigBeeAlliance09")

        # The TCLK IEEE address is returned as `FF:FF:FF:FF:FF:FF:FF:FF`
        if self.state.node_info.logical_type == zdo_t.LogicalType.Coordinator:
            tc_link_key.partner_ieee = self.state.node_info.ieee

        can_burn_userdata_custom_eui64 = await ezsp.can_burn_userdata_custom_eui64()
        can_rewrite_custom_eui64 = await ezsp.can_rewrite_custom_eui64()

        if FirmwareFeatures.FLOW_CONTROL_TYPE in ezsp._xncp_features:
            flow_control = await ezsp.xncp_get_flow_control_type()
        else:
            flow_control = None

        self.state.network_info = zigpy.state.NetworkInfo(
            source=f"bellows@{LIB_VERSION}",
            extended_pan_id=zigpy.types.ExtendedPanId(nwk_params.extendedPanId),
            pan_id=zigpy.types.PanId(nwk_params.panId),
            nwk_update_id=zigpy.types.uint8_t(nwk_params.nwkUpdateId),
            nwk_manager_id=zigpy.types.NWK(nwk_params.nwkManagerId),
            channel=zigpy.types.uint8_t(nwk_params.radioChannel),
            channel_mask=zigpy.types.Channels(nwk_params.channels),
            security_level=zigpy.types.uint8_t(security_level),
            network_key=network_key,
            tc_link_key=tc_link_key,
            key_table=[],
            children=[],
            nwk_addresses={},
            stack_specific=stack_specific,
            metadata={
                "ezsp": {
                    "stack_version": ezsp.ezsp_version,
                    "can_burn_userdata_custom_eui64": can_burn_userdata_custom_eui64,
                    "can_rewrite_custom_eui64": can_rewrite_custom_eui64,
                    "flow_control": (
                        flow_control.name.lower() if flow_control is not None else None
                    ),
                }
            },
        )

        if not load_devices:
            return

        async for link_key in ezsp.read_link_keys():
            self.state.network_info.key_table.append(link_key)

        async for nwk, eui64, _node_type in ezsp.read_child_data():
            self.state.network_info.children.append(eui64)
            self.state.network_info.nwk_addresses[eui64] = nwk

        async for nwk, eui64 in ezsp.read_address_table():
            self.state.network_info.nwk_addresses[eui64] = nwk

    async def write_network_info(
        self, *, network_info: zigpy.state.NetworkInfo, node_info: zigpy.state.NodeInfo
    ) -> None:
        ezsp = self._ezsp

        await self.reset_network_info()

        stack_specific = network_info.stack_specific.get("ezsp", {})
        (current_eui64,) = await ezsp.getEui64()
        wrote_eui64 = False

        if (
            node_info.ieee != zigpy.types.EUI64.UNKNOWN
            and node_info.ieee != current_eui64
        ):
            if await ezsp.can_rewrite_custom_eui64():
                await ezsp.write_custom_eui64(node_info.ieee)
                wrote_eui64 = True
            elif not stack_specific.get(
                "i_understand_i_can_update_eui64_only_once_and_i_still_want_to_do_it"
            ):
                _, _, version = await self._get_board_info()
                raise ControllerError(
                    f"Please upgrade your adapter firmware. The adapter IEEE address"
                    f" needs to be replaced and firmware {version!r} does not support"
                    f" writing it multiple times."
                )
            elif not await ezsp.can_burn_userdata_custom_eui64():
                _, _, version = await self._get_board_info()
                raise ControllerError(
                    f"Please upgrade your adapter firmware. The adapter IEEE address"
                    f" has been overwritten and firmware {version!r} does not support"
                    f" writing it a second time."
                )
            else:
                await ezsp.write_custom_eui64(node_info.ieee, burn_into_userdata=True)
                wrote_eui64 = True

        if wrote_eui64:
            # Reset after writing the EUI64, as it touches NVRAM
            await self._reset()
        else:
            # If we cannot write the new EUI64, don't mess up key entries with the
            # unwritten EUI64 address
            node_info.ieee = current_eui64
            network_info.tc_link_key.partner_ieee = current_eui64

        await self._ezsp.write_nwk_frame_counter(network_info.network_key.tx_counter)
        await self._ezsp.write_aps_frame_counter(network_info.tc_link_key.tx_counter)

        use_hashed_tclk = ezsp.ezsp_version > 4

        if use_hashed_tclk and not stack_specific.get("hashed_tclk"):
            # Generate a random default
            network_info.stack_specific.setdefault("ezsp", {})[
                "hashed_tclk"
            ] = os.urandom(16).hex()

        initial_security_state = util.zha_security(
            network_info=network_info,
            use_hashed_tclk=use_hashed_tclk,
        )
        (status,) = await ezsp.setInitialSecurityState(state=initial_security_state)
        assert t.sl_Status.from_ember_status(status) == t.sl_Status.OK

        await ezsp.write_link_keys(network_info.key_table)

        children_with_nwk_addresses = {
            eui64: network_info.nwk_addresses[eui64]
            for eui64 in network_info.children
            if eui64 in network_info.nwk_addresses
        }

        await ezsp.write_child_data(children_with_nwk_addresses)

        # Set the network settings
        parameters = t.EmberNetworkParameters()
        parameters.panId = t.EmberPanId(network_info.pan_id)
        parameters.extendedPanId = t.EUI64(network_info.extended_pan_id)
        parameters.radioTxPower = t.uint8_t(8)
        parameters.radioChannel = t.uint8_t(network_info.channel)
        parameters.joinMethod = t.EmberJoinMethod.USE_MAC_ASSOCIATION
        parameters.nwkManagerId = t.EmberNodeId(network_info.nwk_manager_id)
        parameters.nwkUpdateId = t.uint8_t(network_info.nwk_update_id)
        parameters.channels = t.Channels(network_info.channel_mask)

        await ezsp.formNetwork(parameters=parameters)
        await self._ensure_network_running()

    async def reset_network_info(self):
        await self._ezsp.factory_reset()

        # Reset the custom EUI64
        await self._ezsp.reset_custom_eui64()

        # We must reset when NV3 has changed
        await self._reset()

        # The network must be running before we can leave it
        try:
            await self._ensure_network_running()
        except zigpy.exceptions.NetworkNotFormed:
            pass
        else:
            await self._ezsp.leaveNetwork()

    async def _reset(self):
        self._ezsp.stop_ezsp()
        await self._ezsp.startup_reset()
        await self._ezsp.write_config(self.config[CONF_EZSP_CONFIG])

    async def disconnect(self):
        # TODO: how do you shut down the stack?
        self.controller_event.clear()
        if self._ezsp is not None:
            await self._ezsp.disconnect()
            self._ezsp = None

    async def force_remove(self, dev):
        # This should probably be delivered to the parent device instead
        # of the device itself.
        await self._ezsp.removeDevice(dev.nwk, dev.ieee, dev.ieee)

    def ezsp_callback_handler(self, frame_name, args):
        LOGGER.debug("Received %s frame with %s", frame_name, args)
        if frame_name == "incomingMessageHandler":
            if self._ezsp.ezsp_version >= 14:
                (
                    message_type,
                    aps_frame,
                    nwk,
                    _eui64,
                    binding_index,
                    address_index,
                    lqi,
                    rssi,
                    _timestamp,
                    message,
                ) = args
            else:
                (
                    message_type,
                    aps_frame,
                    lqi,
                    rssi,
                    nwk,
                    binding_index,
                    address_index,
                    message,
                ) = args

            self._handle_frame(
                message_type=message_type,
                aps_frame=aps_frame,
                lqi=lqi,
                rssi=rssi,
                sender=nwk,
                binding_index=binding_index,
                address_index=address_index,
                message=message,
            )
        elif frame_name == "messageSentHandler":
            if self._ezsp.ezsp_version >= 14:
                (
                    status,
                    message_type,
                    destination,
                    aps_frame,
                    message_tag,
                    message,
                ) = args
            else:
                (
                    message_type,
                    destination,
                    aps_frame,
                    message_tag,
                    status,
                    message,
                ) = args
                status = t.sl_Status.from_ember_status(status)

            self._handle_frame_sent(
                message_type=message_type,
                destination=destination,
                aps_frame=aps_frame,
                message_tag=message_tag,
                status=status,
                message=message,
            )
        elif frame_name == "trustCenterJoinHandler":
            self._handle_tc_join_handler(*args)
        elif frame_name == "incomingRouteRecordHandler":
            self.handle_route_record(*args)
        elif frame_name == "incomingRouteErrorHandler":
            status, nwk = args
            status = t.sl_Status.from_ember_status(status)
            self.handle_route_error(status, nwk)
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
        status: t.sl_Status,
        message: bytes,
    ):
        if status == t.sl_Status.OK:
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
            pending_tag = (destination, message_tag)
            request = self._pending[pending_tag]
            request.result.set_result((status, f"message send {msg}"))
            self.state.counters[COUNTERS_CTRL][cnt_name].increment()
        except KeyError:
            self.state.counters[COUNTERS_CTRL][f"{cnt_name}_unexpected"].increment()
            LOGGER.debug("Unexpected message send notification tag: %s", pending_tag)
        except asyncio.InvalidStateError as exc:
            self.state.counters[COUNTERS_CTRL][f"{cnt_name}_duplicate"].increment()
            LOGGER.debug(
                (
                    "Invalid state on future for message tag %s "
                    "- probably duplicate response: %s"
                ),
                pending_tag,
                exc,
            )

    async def _handle_no_such_device(self, sender: int) -> None:
        """Try to match unknown device by its EUI64 address."""
        status, ieee = await self._ezsp.lookupEui64ByNodeId(nodeId=sender)
        status = t.sl_Status.from_ember_status(status)

        if status == t.sl_Status.OK:
            LOGGER.debug("Found %s ieee for %s sender", ieee, sender)
            self.handle_join(sender, ieee, 0)
            return
        LOGGER.debug("Couldn't look up ieee for %s", sender)

    def _handle_tc_join_handler(
        self,
        nwk: t.EmberNodeId,
        ieee: t.EUI64,
        device_update_status: t.EmberDeviceUpdate,
        decision: t.EmberJoinDecision,
        parent_nwk: t.EmberNodeId,
    ) -> None:
        """Trust Center Join handler."""
        if device_update_status == t.EmberDeviceUpdate.DEVICE_LEFT:
            self.handle_leave(nwk, ieee)
            return

        if device_update_status == t.EmberDeviceUpdate.STANDARD_SECURITY_UNSECURED_JOIN:
            self.create_task(self.cleanup_tc_link_key(ieee), "cleanup_tc_link_key")

        if decision == t.EmberJoinDecision.DENY_JOIN:
            # no point in handling the join if it was denied
            return

        mfg_id = IEEE_PREFIX_MFG_ID.get(str(ieee)[:8].upper())

        if mfg_id is not None:
            if self._mfg_id_task and not self._mfg_id_task.done():
                self._mfg_id_task.cancel()
            self._mfg_id_task = asyncio.create_task(self._reset_mfg_id(mfg_id))
        self.handle_join(nwk, ieee, parent_nwk)

    async def _reset_mfg_id(self, mfg_id: int) -> None:
        """Resets manufacturer id if was temporary overridden by a joining device."""
        await self._ezsp.setManufacturerCode(code=mfg_id)
        await asyncio.sleep(MFG_ID_RESET_DELAY)
        await self._ezsp.setManufacturerCode(code=DEFAULT_MFG_ID)

    async def energy_scan(
        self, channels: t.Channels, duration_exp: int, count: int
    ) -> dict[int, float]:
        all_results = {}

        for _ in range(count):
            channels_to_scan = set(channels)

            # XXX: RCP firmware sometimes performs a partial scan and returns early
            # XXX: NCP firmware sometimes returns scan results twice
            while channels_to_scan:
                results = await self._ezsp.startScan(
                    scanType=t.EzspNetworkScanType.ENERGY_SCAN,
                    channelMask=t.Channels.from_channel_list(channels_to_scan),
                    duration=duration_exp,
                )

                for channel, rssi in results:
                    all_results.setdefault(channel, []).append(rssi)
                    channels_to_scan.discard(channel)

        # Remap RSSI to Energy
        return {
            channel: util.map_rssi_to_energy(statistics.mean(all_results[channel]))
            for channel in list(channels)
        }

    async def _network_scan(
        self, channels: t.Channels, duration_exp: int
    ) -> AsyncGenerator[zigpy.types.NetworkBeacon]:
        """Scans for networks and yields network beacons."""
        queue = asyncio.Queue()

        with self._ezsp.callback_for_commands(
            {"networkFoundHandler", "scanCompleteHandler"},
            callback=lambda command, response: queue.put_nowait((command, response)),
        ):
            # XXX: replace with normal command invocation once overload is removed
            (status,) = await self._ezsp._command(
                "startScan",
                scanType=t.EzspNetworkScanType.ACTIVE_SCAN,
                channelMask=channels,
                duration=duration_exp,
            )

            if t.sl_Status.from_ember_status(status) != t.sl_Status.OK:
                raise ControllerError(f"Failed to start scan: {status!r}")

            while True:
                command, response = await queue.get()

                if command == "scanCompleteHandler":
                    break

                (networkFound, lastHopLqi, lastHopRssi) = response

                yield zigpy.types.NetworkBeacon(
                    pan_id=networkFound.panId,
                    extended_pan_id=networkFound.extendedPanId,
                    channel=networkFound.channel,
                    nwk_update_id=networkFound.nwkUpdateId,
                    permit_joining=bool(networkFound.allowingJoin),
                    stack_profile=networkFound.stackProfile,
                    lqi=lastHopLqi,
                    rssi=lastHopRssi,
                )

    def _check_status(self, status: t.sl_Status | t.EmberStatus) -> None:
        if t.sl_Status.from_ember_status(status) != t.sl_Status.OK:
            raise ControllerError(f"Command failed: {status!r}")

    async def _packet_capture(self, channel: int):
        (status,) = await self._ezsp.mfglibStart(rxCallback=True)
        self._check_status(status)

        try:
            await self._packet_capture_change_channel(channel=channel)
            assert self._packet_capture_channel is not None

            queue = asyncio.Queue()

            with self._ezsp.callback_for_commands(
                {"mfglibRxHandler"},
                callback=lambda _, response: queue.put_nowait(
                    (datetime.now(timezone.utc), response)
                ),
            ):
                while True:
                    timestamp, (linkQuality, rssi, packetContents) = await queue.get()

                    # The last two bytes are not a FCS
                    packetContents = packetContents[:-2]

                    yield zigpy.types.CapturedPacket(
                        timestamp=timestamp,
                        rssi=rssi,
                        lqi=linkQuality,
                        channel=self._packet_capture_channel,
                        data=packetContents,
                    )
        finally:
            (status,) = await self._ezsp.mfglibEnd()
            self._check_status(status)

    async def _packet_capture_change_channel(self, channel: int):
        (status,) = await self._ezsp.mfglibSetChannel(channel=channel)
        self._check_status(status)
        self._packet_capture_channel = channel

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
        aps_frame.sequence = t.uint8_t(packet.tsn)
        aps_frame.profileId = t.uint16_t(packet.profile_id)
        aps_frame.clusterId = t.uint16_t(packet.cluster_id)
        aps_frame.sourceEndpoint = t.uint8_t(packet.src_ep)
        aps_frame.destinationEndpoint = t.uint8_t(packet.dst_ep or 0)
        aps_frame.options = t.EmberApsOption.APS_OPTION_NONE

        if packet.dst.addr_mode == zigpy.types.AddrMode.Group:
            aps_frame.groupId = t.uint16_t(packet.dst.address)
        else:
            aps_frame.groupId = t.uint16_t(0x0000)

        if self.config[zigpy.config.CONF_SOURCE_ROUTING]:
            # Source routing uses address discovery to discover routes
            aps_frame.options |= t.EmberApsOption.APS_OPTION_ENABLE_ADDRESS_DISCOVERY
        elif zigpy.types.TransmitOptions.FORCE_ROUTE_DISCOVERY in packet.tx_options:
            # Forcing route discovery requires retrying
            aps_frame.options |= t.EmberApsOption.APS_OPTION_FORCE_ROUTE_DISCOVERY
            aps_frame.options |= t.EmberApsOption.APS_OPTION_RETRY
        else:
            aps_frame.options |= t.EmberApsOption.APS_OPTION_ENABLE_ROUTE_DISCOVERY

        extended_timeout = packet.extended_timeout

        # EmberZNet requires retrying to enable APS ACKs
        if (
            zigpy.types.TransmitOptions.ACK in packet.tx_options
            and packet.dst.addr_mode == zigpy.types.AddrMode.NWK
        ):
            aps_frame.options |= t.EmberApsOption.APS_OPTION_RETRY

            # We disable extended timeout if we enable ACKs
            extended_timeout = False

        async with self._limit_concurrency(priority=packet.priority):
            message_tag = self.get_sequence()
            pending_tag = (packet.dst.address, message_tag)
            with self._pending.new(pending_tag) as req:
                async with self._req_lock:
                    if packet.dst.addr_mode == zigpy.types.AddrMode.NWK:
                        if device is not None:
                            await self._ezsp.set_extended_timeout(
                                nwk=device.nwk,
                                ieee=device.ieee,
                                extended_timeout=extended_timeout,
                            )

                        if packet.source_route is not None:
                            if (
                                FirmwareFeatures.MANUAL_SOURCE_ROUTE
                                in self._ezsp._xncp_features
                                and self.config[CONF_BELLOWS_CONFIG][
                                    CONF_MANUAL_SOURCE_ROUTING
                                ]
                            ):
                                await self._ezsp.xncp_set_manual_source_route(
                                    nwk=packet.dst.address,
                                    relays=packet.source_route,
                                )
                            else:
                                await self._ezsp.set_source_route(
                                    nwk=packet.dst.address,
                                    relays=packet.source_route,
                                )

                        status, _ = await self._ezsp.send_unicast(
                            nwk=packet.dst.address,
                            aps_frame=aps_frame,
                            message_tag=message_tag,
                            data=packet.data.serialize(),
                        )
                    elif packet.dst.addr_mode == zigpy.types.AddrMode.Group:
                        status, _ = await self._ezsp.send_multicast(
                            aps_frame=aps_frame,
                            radius=packet.radius,
                            non_member_radius=packet.non_member_radius,
                            message_tag=message_tag,
                            data=packet.data.serialize(),
                        )
                    elif packet.dst.addr_mode == zigpy.types.AddrMode.Broadcast:
                        status, _ = await self._ezsp.send_broadcast(
                            address=packet.dst.address,
                            aps_frame=aps_frame,
                            radius=packet.radius,
                            message_tag=message_tag,
                            aps_sequence=packet.tsn,
                            data=packet.data.serialize(),
                        )

                if status != t.sl_Status.OK:
                    raise zigpy.exceptions.DeliveryError(
                        f"Failed to enqueue message: {status!r}", status
                    )

                # Only throw a delivery exception for packets sent with NWK addressing.
                # https://github.com/home-assistant/core/issues/79832
                # Broadcasts/multicasts don't have ACKs or confirmations either.
                if packet.dst.addr_mode != zigpy.types.AddrMode.NWK:
                    return

                # Wait for `messageSentHandler` message
                async with asyncio_timeout(
                    MESSAGE_SEND_TIMEOUT_MAINS
                    if not packet.extended_timeout
                    else MESSAGE_SEND_TIMEOUT_BATTERY
                ):
                    send_status, _ = await req.result

                if t.sl_Status.from_ember_status(send_status) != t.sl_Status.OK:
                    raise zigpy.exceptions.DeliveryError(
                        f"Failed to deliver message: {send_status!r}", send_status
                    )

    async def permit(self, time_s: int = 60, node: t.EmberNodeId = None) -> None:
        """Permit joining."""
        self.create_task(self._ezsp.pre_permit(time_s), "pre_permit")
        await super().permit(time_s, node)

    def permit_ncp(self, time_s=60):
        assert 0 <= time_s <= 254
        return self._ezsp.permitJoining(time_s)

    async def permit_with_link_key(
        self, node: t.EUI64, link_key: t.KeyData, time_s: int = 60
    ) -> None:
        """Permits a new device to join with the given IEEE and link key."""

        status = await self._ezsp.add_transient_link_key(node, link_key)

        if t.sl_Status.from_ember_status(status) != t.sl_Status.OK:
            raise ControllerError("Failed to set link key")

        if self._ezsp.ezsp_version >= 8:
            await self._ezsp.setPolicy(
                policyId=t.EzspPolicyId.TRUST_CENTER_POLICY,
                decisionId=(
                    t.EzspDecisionBitmask.ALLOW_JOINS
                    | t.EzspDecisionBitmask.JOINS_USE_INSTALL_CODE_KEY
                ),
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

    async def _watchdog_loop(self):
        self._watchdog_failures = 0
        self._watchdog_feed_counter = 0
        await super()._watchdog_loop()

    async def _watchdog_feed(self):
        try:
            if self._ezsp.ezsp_version == 4:
                await self._ezsp.nop()
            else:
                counters = self.state.counters[COUNTERS_EZSP]
                self._watchdog_feed_counter += 1

                remainder = (
                    self._watchdog_feed_counter
                    % EZSP_COUNTERS_CLEAR_IN_WATCHDOG_PERIODS
                )

                if remainder > 0:
                    current_counters = await self._ezsp.read_counters()
                else:
                    current_counters = await self._ezsp.read_and_clear_counters()

                for cnt_type, value in current_counters.items():
                    counters[cnt_type.name[8:]].update(value)

                if remainder == 0:
                    counters.reset()

                free_buffers = await self._get_free_buffers()
                if free_buffers is not None:
                    cnt = counters[COUNTER_EZSP_BUFFERS]
                    cnt._raw_value = free_buffers
                    cnt._last_reset_value = 0

                LOGGER.debug("%s", counters)
        except (asyncio.TimeoutError, EzspError) as exc:
            # TODO: converted Silvercrest gateways break without this
            LOGGER.warning("Watchdog heartbeat timeout: %s", repr(exc))
            self._watchdog_failures += 1
            if self._watchdog_failures > MAX_WATCHDOG_FAILURES:
                self.state.counters[COUNTERS_CTRL][COUNTER_WATCHDOG].increment()
                raise
        else:
            self._watchdog_failures = 0

    async def _get_free_buffers(self) -> int | None:
        status, value = await self._ezsp.getValue(
            valueId=t.EzspValueId.VALUE_FREE_BUFFERS
        )

        if status != t.EzspStatus.SUCCESS:
            return None

        buffers = int.from_bytes(value, byteorder="little")

        LOGGER.debug("Free buffers status %s, value: %s", status, buffers)
        return buffers

    def handle_route_record(
        self,
        nwk: t.EmberNodeId,
        ieee: t.EUI64,
        lqi: t.uint8_t,
        rssi: t.int8s,
        relays: t.LVList[t.EmberNodeId],
    ) -> None:
        LOGGER.debug(
            "Processing route record request: %s", (nwk, ieee, lqi, rssi, relays)
        )
        self.handle_relays(nwk=nwk, relays=relays)

    def handle_route_error(self, status: t.sl_Status, nwk: t.EmberNodeId) -> None:
        LOGGER.debug("Processing route error: status=%s, nwk=%s", status, nwk)
