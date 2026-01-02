""""EZSP Protocol version 18 protocol handler."""
from __future__ import annotations

import voluptuous as vol

import bellows.config

from . import commands, config
from ..v17 import EZSPv17


class EZSPv18(EZSPv17):
    """EZSP Version 18 Protocol version handler."""

    VERSION = 18
    COMMANDS = commands.COMMANDS
    SCHEMAS = {
        bellows.config.CONF_EZSP_CONFIG: vol.Schema(config.EZSP_SCHEMA),
        bellows.config.CONF_EZSP_POLICIES: vol.Schema(config.EZSP_POLICIES_SCH),
    }
