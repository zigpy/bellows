""""EZSP Protocol version 16 protocol handler."""
from __future__ import annotations

import voluptuous as vol

import bellows.config

from . import commands, config
from ..v14 import EZSPv14


class EZSPv16(EZSPv14):
    """EZSP Version 16 Protocol version handler."""

    VERSION = 16
    COMMANDS = commands.COMMANDS
    SCHEMAS = {
        bellows.config.CONF_EZSP_CONFIG: vol.Schema(config.EZSP_SCHEMA),
        bellows.config.CONF_EZSP_POLICIES: vol.Schema(config.EZSP_POLICIES_SCH),
    }
