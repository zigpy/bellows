""""EZSP Protocol version 7 protocol handler."""
import logging

import voluptuous

from . import commands, config as v7_config, types as v7_types
from ..v5 import EZSPv5

EZSP_VERSION = 7
LOGGER = logging.getLogger(__name__)


class EZSPv7(EZSPv5):
    """EZSP Version 7 Protocol version handler."""

    COMMANDS = commands.COMMANDS
    SCHEMA = voluptuous.Schema(v7_config.EZSP_SCHEMA)
    types = v7_types
