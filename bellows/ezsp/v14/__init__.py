""""EZSP Protocol version 14 protocol handler."""
from __future__ import annotations

from typing import AsyncGenerator

import voluptuous as vol
from zigpy.exceptions import NetworkNotFormed
import zigpy.state

import bellows.config
import bellows.types as t

from . import commands, config
from ..v13 import EZSPv13


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
