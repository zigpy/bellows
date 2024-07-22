""""EZSP Protocol version 5 protocol handler."""
from __future__ import annotations

import logging
from typing import AsyncGenerator

import voluptuous as vol

import bellows.config
import bellows.types as t

from . import commands, config
from ..v4 import EZSPv4

LOGGER = logging.getLogger(__name__)


class EZSPv5(EZSPv4):
    """EZSP Version 5 Protocol version handler."""

    VERSION = 5
    COMMANDS = commands.COMMANDS
    SCHEMAS = {
        bellows.config.CONF_EZSP_CONFIG: vol.Schema(config.EZSP_SCHEMA),
        bellows.config.CONF_EZSP_POLICIES: vol.Schema(config.EZSP_POLICIES_SCH),
    }

    def _ezsp_frame_tx(self, name: str) -> bytes:
        """Serialize the frame id."""
        cmd_id = self.COMMANDS[name][0]
        frame = [self._seq, 0x00, 0xFF, 0x00, cmd_id]
        return bytes(frame)

    def _ezsp_frame_rx(self, data: bytes) -> tuple[int, int, bytes]:
        """Handler for received data frame."""
        return data[0], data[4], data[5:]

    async def add_transient_link_key(
        self, ieee: t.EUI64, key: t.KeyData
    ) -> t.sl_Status:
        (status,) = await self.addTransientLinkKey(partner=ieee, transientKey=key)
        return t.sl_Status.from_ember_status(status)

    async def pre_permit(self, time_s: int) -> None:
        """Add pre-shared TC Link key."""
        wild_card_ieee = t.EUI64.convert("FF:FF:FF:FF:FF:FF:FF:FF")
        tc_link_key = t.KeyData(b"ZigBeeAlliance09")
        await self.add_transient_link_key(wild_card_ieee, tc_link_key)

    async def read_address_table(self) -> AsyncGenerator[tuple[t.NWK, t.EUI64], None]:
        (status, addr_table_size) = await self.getConfigurationValue(
            t.EzspConfigId.CONFIG_ADDRESS_TABLE_SIZE
        )

        for idx in range(addr_table_size):
            (nwk,) = await self.getAddressTableRemoteNodeId(addressTableIndex=idx)

            # Ignore invalid NWK entries
            if nwk in t.EmberDistinguishedNodeId.__members__.values():
                continue

            (eui64,) = await self.getAddressTableRemoteEui64(addressTableIndex=idx)

            if eui64 in (
                t.EUI64.convert("00:00:00:00:00:00:00:00"),
                t.EUI64.convert("FF:FF:FF:FF:FF:FF:FF:FF"),
            ):
                continue

            yield nwk, eui64

    async def write_nwk_frame_counter(self, frame_counter: t.uint32_t) -> None:
        # Frame counters can only be set *before* we have joined a network
        (state,) = await self.networkState()
        assert state == t.EmberNetworkStatus.NO_NETWORK

        (status,) = await self.setValue(
            valueId=t.EzspValueId.VALUE_NWK_FRAME_COUNTER,
            value=t.uint32_t(frame_counter).serialize(),
        )
        assert t.sl_Status.from_ember_status(status) == t.sl_Status.OK

    async def write_aps_frame_counter(self, frame_counter: t.uint32_t) -> None:
        # Frame counters can only be set *before* we have joined a network
        (state,) = await self.networkState()
        assert state == t.EmberNetworkStatus.NO_NETWORK

        (status,) = await self.setValue(
            valueId=t.EzspValueId.VALUE_APS_FRAME_COUNTER,
            value=t.uint32_t(frame_counter).serialize(),
        )
        assert t.sl_Status.from_ember_status(status) == t.sl_Status.OK
