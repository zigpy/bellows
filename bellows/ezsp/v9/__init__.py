""""EZSP Protocol version 9 protocol handler."""
import logging

import voluptuous

import bellows.config

from . import commands, config, types as v9_types
from ..v8 import EZSPv8

LOGGER = logging.getLogger(__name__)


class EZSPv9(EZSPv8):
    """EZSP Version 9 Protocol version handler."""

    VERSION = 9
    COMMANDS = commands.COMMANDS
    SCHEMAS = {
        bellows.config.CONF_EZSP_CONFIG: voluptuous.Schema(config.EZSP_SCHEMA),
        bellows.config.CONF_EZSP_POLICIES: voluptuous.Schema(config.EZSP_POLICIES_SCH),
    }
    types = v9_types
