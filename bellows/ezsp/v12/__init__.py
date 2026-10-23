"""EZSP Protocol version 12 protocol handler."""

import voluptuous as vol

import bellows.config

from ..v11 import EZSPv11
from . import commands, config


class EZSPv12(EZSPv11):
    """EZSP Version 12 Protocol version handler."""

    VERSION = 12
    COMMANDS = commands.COMMANDS
    SCHEMAS = {
        bellows.config.CONF_EZSP_CONFIG: vol.Schema(config.EZSP_SCHEMA),
        bellows.config.CONF_EZSP_POLICIES: vol.Schema(config.EZSP_POLICIES_SCH),
    }
