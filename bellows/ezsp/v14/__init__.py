""""EZSP Protocol version 14 protocol handler."""
from __future__ import annotations

import voluptuous as vol

import bellows.config

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
