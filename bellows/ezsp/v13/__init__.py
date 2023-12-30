""""EZSP Protocol version 13 protocol handler."""
from __future__ import annotations

import voluptuous as vol

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
    ) -> t.EmberStatus:
        (status,) = await self.importTransientKey(
            ieee,
            key,
            v13_types.sl_zb_sec_man_flags_t.NONE,
        )

        return status
