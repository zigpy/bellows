""""EZSP Protocol version 13 protocol handler."""
from __future__ import annotations

from typing import AsyncGenerator

import voluptuous as vol
import zigpy.state

import bellows.config
import bellows.types as t

from . import commands, config, types as v13_types
from ..v12 import EZSPv12


class EZSPv13(EZSPv12):
    """EZSP Version 13 Protocol version handler."""

    VERSION = 13
    COMMANDS = commands.COMMANDS
    SCHEMAS = {
        bellows.config.CONF_EZSP_CONFIG: vol.Schema(config.EZSP_SCHEMA),
        bellows.config.CONF_EZSP_POLICIES: vol.Schema(config.EZSP_POLICIES_SCH),
    }
    types = v13_types

    async def add_transient_link_key(
        self, ieee: t.EUI64, key: t.KeyData
    ) -> t.sl_Status:
        (status,) = await self.importTransientKey(
            ieee,
            key,
            self.types.sl_zb_sec_man_flags_t.NONE,
        )

        return t.sl_Status.from_ember_status(status)

    async def read_link_keys(self) -> AsyncGenerator[zigpy.state.Key, None]:
        (status, key_table_size) = await self.getConfigurationValue(
            self.types.EzspConfigId.CONFIG_KEY_TABLE_SIZE
        )

        for index in range(key_table_size):
            (
                eui64,
                plaintext_key,
                key_data,
                status,
            ) = await self.exportLinkKeyByIndex(index)

            if status != t.sl_Status.OK:
                continue

            yield zigpy.state.Key(
                key=plaintext_key,
                tx_counter=key_data.outgoing_frame_counter,
                rx_counter=key_data.incoming_frame_counter,
                partner_ieee=eui64,
            )
