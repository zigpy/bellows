""""EZSP Protocol version 17 protocol handler."""
from __future__ import annotations

import voluptuous as vol

import bellows.config

from . import commands, config
from ..v16 import EZSPv16


class EZSPv17(EZSPv16):
    """EZSP Version 17 Protocol version handler."""

    VERSION = 17
    COMMANDS = commands.COMMANDS
    SCHEMAS = {
        bellows.config.CONF_EZSP_CONFIG: vol.Schema(config.EZSP_SCHEMA),
        bellows.config.CONF_EZSP_POLICIES: vol.Schema(config.EZSP_POLICIES_SCH),
    }
