""""EZSP Protocol version 10 protocol handler."""
import logging

import voluptuous

import bellows.config

from . import commands, config, types as v10_types
from ..v9 import EZSPv9

LOGGER = logging.getLogger(__name__)


class EZSPv10(EZSPv9):
    """EZSP Version 10 Protocol version handler."""

    VERSION = 10
    COMMANDS = commands.COMMANDS
    SCHEMAS = {
        bellows.config.CONF_EZSP_CONFIG: voluptuous.Schema(config.EZSP_SCHEMA),
        bellows.config.CONF_EZSP_POLICIES: voluptuous.Schema(config.EZSP_POLICIES_SCH),
    }
    types = v10_types
