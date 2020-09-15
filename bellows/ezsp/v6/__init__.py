""""EZSP Protocol version 6 protocol handler."""
import logging

import voluptuous

import bellows.config

from . import commands, config, types as v6_types
from ..v5 import EZSPv5

EZSP_VERSION = 6
LOGGER = logging.getLogger(__name__)


class EZSPv6(EZSPv5):
    """EZSP Version 6 Protocol version handler."""

    COMMANDS = commands.COMMANDS
    SCHEMAS = {
        bellows.config.CONF_EZSP_CONFIG: voluptuous.Schema(config.EZSP_SCHEMA),
        bellows.config.CONF_EZSP_POLICIES: voluptuous.Schema(config.EZSP_POLICIES_SCH),
    }
    types = v6_types
