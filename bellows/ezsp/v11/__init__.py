""""EZSP Protocol version 11 protocol handler."""
import voluptuous as vol

import bellows.config

from . import commands, config
from ..v10 import EZSPv10


class EZSPv11(EZSPv10):
    """EZSP Version 11 Protocol version handler."""

    VERSION = 11
    COMMANDS = commands.COMMANDS
    SCHEMAS = {
        bellows.config.CONF_EZSP_CONFIG: vol.Schema(config.EZSP_SCHEMA),
        bellows.config.CONF_EZSP_POLICIES: vol.Schema(config.EZSP_POLICIES_SCH),
    }
