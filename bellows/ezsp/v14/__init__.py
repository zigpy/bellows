""""EZSP Protocol version 14 protocol handler."""
from __future__ import annotations

from typing import AsyncGenerator

import voluptuous as vol

import bellows.config
import bellows.types as t

from . import commands, config, types as v14_types
from ..v13 import EZSPv13


class EZSPv14(EZSPv13):
    """EZSP Version 14 Protocol version handler."""

    VERSION = 14
    COMMANDS = commands.COMMANDS
    SCHEMAS = {
        bellows.config.CONF_EZSP_CONFIG: vol.Schema(config.EZSP_SCHEMA),
        bellows.config.CONF_EZSP_POLICIES: vol.Schema(config.EZSP_POLICIES_SCH),
    }
    types = v14_types

    async def read_address_table(self) -> AsyncGenerator[tuple[t.NWK, t.EUI64], None]:
        (status, addr_table_size) = await self.getConfigurationValue(
            self.types.EzspConfigId.CONFIG_ADDRESS_TABLE_SIZE
        )

        for idx in range(addr_table_size):
            (status, nwk, eui64) = await self.getAddressTableInfo(idx)

            if status != t.sl_Status.OK:
                continue

            if eui64 in (
                t.EUI64.convert("00:00:00:00:00:00:00:00"),
                t.EUI64.convert("FF:FF:FF:FF:FF:FF:FF:FF"),
            ):
                continue

            yield nwk, eui64
