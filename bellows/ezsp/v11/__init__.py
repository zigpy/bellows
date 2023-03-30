""""EZSP Protocol version 11 protocol handler."""
import voluptuous as vol

import bellows.config

from . import commands, config, types as v11_types
from ..v10 import EZSPv10

EZSP_VERSION = 11


class EZSPv11(EZSPv10):
    """EZSP Version 11 Protocol version handler."""

    COMMANDS = commands.COMMANDS
    SCHEMAS = {
        bellows.config.CONF_EZSP_CONFIG: vol.Schema(config.EZSP_SCHEMA),
        bellows.config.CONF_EZSP_POLICIES: vol.Schema(config.EZSP_POLICIES_SCH),
    }
    types = v11_types
