""""EZSP Protocol version 19 protocol handler."""
from __future__ import annotations

import voluptuous as vol

import bellows.config

from . import commands, config
from ..v18 import EZSPv18


class EZSPv19(EZSPv18):
    """EZSP Version 19 Protocol version handler."""

    VERSION = 19
    COMMANDS = commands.COMMANDS
    SCHEMAS = {
        bellows.config.CONF_EZSP_CONFIG: vol.Schema(config.EZSP_SCHEMA),
        bellows.config.CONF_EZSP_POLICIES: vol.Schema(config.EZSP_POLICIES_SCH),
    }
