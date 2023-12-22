""""EZSP Protocol version 13 protocol handler."""
import voluptuous as vol

import bellows.config

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
