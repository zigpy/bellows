""""EZSP Protocol version 7 protocol handler."""
import logging

import bellows.config
import voluptuous

from . import commands, config, types as v7_types
from ..v5 import EZSPv5

EZSP_VERSION = 7
LOGGER = logging.getLogger(__name__)


class EZSPv7(EZSPv5):
    """EZSP Version 7 Protocol version handler."""

    COMMANDS = commands.COMMANDS
    SCHEMAS = {bellows.config.CONF_EZSP_CONFIG: voluptuous.Schema(config.EZSP_SCHEMA)}
    types = v7_types
