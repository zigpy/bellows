""""EZSP Protocol version 14 protocol handler."""
from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator
import logging

import voluptuous as vol
from zigpy.exceptions import NetworkNotFormed
import zigpy.state
import zigpy.types

import bellows.config
import bellows.types as t

from . import commands, config
from ..v13 import EZSPv13

LOGGER = logging.getLogger(__name__)


class EZSPv14(EZSPv13):
    """EZSP Version 14 Protocol version handler."""

    VERSION = 14
    COMMANDS = commands.COMMANDS
    SCHEMAS = {
        bellows.config.CONF_EZSP_CONFIG: vol.Schema(config.EZSP_SCHEMA),
        bellows.config.CONF_EZSP_POLICIES: vol.Schema(config.EZSP_POLICIES_SCH),
    }

    async def read_address_table(self) -> AsyncGenerator[tuple[t.NWK, t.EUI64], None]:
        (status, addr_table_size) = await self.getConfigurationValue(
            configId=t.EzspConfigId.CONFIG_ADDRESS_TABLE_SIZE
        )

        for idx in range(addr_table_size + 100):
            (status, nwk, eui64) = await self.getAddressTableInfo(index=idx)

            if status != t.sl_Status.OK:
                continue

            if eui64 in (
                t.EUI64.convert("00:00:00:00:00:00:00:00"),
                t.EUI64.convert("FF:FF:FF:FF:FF:FF:FF:FF"),
            ):
                continue

            yield nwk, eui64

    async def get_network_key(self) -> zigpy.state.Key:
        status, network_key_data, _ = await self.exportKey(
            context=t.SecurityManagerContextV13(
                core_key_type=t.SecurityManagerKeyType.NETWORK,
                key_index=0,
                derived_type=t.SecurityManagerDerivedKeyTypeV13.NONE,
                eui64=t.EUI64.convert("00:00:00:00:00:00:00:00"),
                multi_network_index=0,
                flags=t.SecurityManagerContextFlags.NONE,
                psa_key_alg_permission=0,
            )
        )

        assert status == t.sl_Status.OK

        (status, network_key_info) = await self.getNetworkKeyInfo()
        assert status == t.sl_Status.OK

        if not network_key_info.network_key_set:
            raise NetworkNotFormed("Network key is not set")

        return zigpy.state.Key(
            key=network_key_data,
            tx_counter=network_key_info.network_key_frame_counter,
            seq=network_key_info.network_key_sequence_number,
        )

    async def get_tc_link_key(self) -> zigpy.state.Key:
        status, tc_link_key_data, _ = await self.exportKey(
            context=t.SecurityManagerContextV13(
                core_key_type=t.SecurityManagerKeyType.TC_LINK,
                key_index=0,
                derived_type=t.SecurityManagerDerivedKeyTypeV13.NONE,
                eui64=t.EUI64.convert("00:00:00:00:00:00:00:00"),
                multi_network_index=0,
                flags=t.SecurityManagerContextFlags.NONE,
                psa_key_alg_permission=0,
            )
        )

        assert status == t.sl_Status.OK

        return zigpy.state.Key(key=tc_link_key_data)

    async def send_unicast(
        self,
        nwk: t.NWK,
        aps_frame: t.EmberApsFrame,
        message_tag: t.uint8_t,
        data: bytes,
    ) -> tuple[t.sl_Status, t.uint8_t]:
        status, sequence = await self.sendUnicast(
            message_type=t.EmberOutgoingMessageType.OUTGOING_DIRECT,
            nwk=nwk,
            aps_frame=aps_frame,
            message_tag=message_tag,
            message=data,
        )

        return status, sequence

    async def send_multicast(
        self,
        aps_frame: t.EmberApsFrame,
        radius: t.uint8_t,
        non_member_radius: t.uint8_t,
        message_tag: t.uint8_t,
        data: bytes,
    ) -> tuple[t.sl_Status, t.uint8_t]:
        status, sequence = await self.sendMulticast(
            aps_frame=aps_frame,
            hops=radius,
            broadcast_addr=t.BroadcastAddress.RX_ON_WHEN_IDLE,
            alias=0x0000,
            sequence=aps_frame.sequence,
            message_tag=message_tag,
            message=data,
        )

        return status, sequence

    async def send_broadcast(
        self,
        address: t.BroadcastAddress,
        aps_frame: t.EmberApsFrame,
        radius: t.uint8_t,
        message_tag: t.uint8_t,
        aps_sequence: t.uint8_t,
        data: bytes,
    ) -> tuple[t.sl_Status, t.uint8_t]:
        status, sequence = await self.sendBroadcast(
            alias=0x0000,
            destination=address,
            sequence=aps_sequence,
            aps_frame=aps_frame,
            radius=radius,
            message_tag=message_tag,
            message=data,
        )

        return status, sequence

    def _handle_incoming_message(self, args: list) -> bool:
        """Handle incomingMessageHandler callback and emit packet_received event.

        Returns True if message was fully handled, False if fragment is incomplete.
        """
        (
            message_type,
            aps_frame,
            sender,
            eui64,
            binding_index,
            address_index,
            lqi,
            rssi,
            timestamp,
            message,
        ) = args

        # Handle fragmented messages
        if aps_frame.options & t.EmberApsOption.APS_OPTION_FRAGMENT:
            fragment_count = (aps_frame.groupId >> 8) & 0xFF
            fragment_index = aps_frame.groupId & 0xFF

            (
                complete,
                reassembled,
                frag_count,
                frag_index,
            ) = self._fragment_manager.handle_incoming_fragment(
                sender_nwk=sender,
                aps_sequence=aps_frame.sequence,
                profile_id=aps_frame.profileId,
                cluster_id=aps_frame.clusterId,
                fragment_count=fragment_count,
                fragment_index=fragment_index,
                payload=message,
            )

            ack_task = asyncio.create_task(
                self._send_fragment_ack(sender, aps_frame, frag_count, frag_index)
            )
            self._fragment_ack_tasks.add(ack_task)
            ack_task.add_done_callback(lambda t: self._fragment_ack_tasks.discard(t))

            if not complete:
                LOGGER.debug("Fragment reassembly not complete, waiting for more data")
                return False

            LOGGER.debug("Reassembled fragmented message, proceeding with handling")
            message = reassembled

        # Determine destination address based on message type
        if message_type == t.EmberIncomingMessageType.INCOMING_BROADCAST:
            dst = zigpy.types.AddrModeAddress(
                addr_mode=zigpy.types.AddrMode.Broadcast,
                address=zigpy.types.BroadcastAddress.ALL_ROUTERS_AND_COORDINATOR,
            )
        elif message_type == t.EmberIncomingMessageType.INCOMING_MULTICAST:
            dst = zigpy.types.AddrModeAddress(
                addr_mode=zigpy.types.AddrMode.Group,
                address=aps_frame.groupId,
            )
        elif message_type == t.EmberIncomingMessageType.INCOMING_UNICAST:
            # We don't know our own NWK at this level, leave as None
            dst = None
        else:
            LOGGER.debug("Ignoring message type: %r", message_type)
            return True

        self.emit(
            "packet_received",
            zigpy.types.ZigbeePacket(
                src=zigpy.types.AddrModeAddress(
                    addr_mode=zigpy.types.AddrMode.NWK,
                    address=zigpy.types.NWK(sender),
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
            ),
        )

        return True

    def _handle_message_sent(self, args: list) -> None:
        """Handle messageSentHandler callback and emit message_sent event."""
        (
            status,
            message_type,
            destination,
            aps_frame,
            message_tag,
            message,
        ) = args

        self.emit(
            "message_sent",
            (
                status,  # Already sl_Status in v14
                message_type,
                destination,
                aps_frame,
                message_tag,
                message,
            ),
        )
