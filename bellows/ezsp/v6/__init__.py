""""EZSP Protocol version 6 protocol handler."""
import logging

import voluptuous

import bellows.config
import bellows.types as t

from . import commands, config
from ..v5 import EZSPv5

LOGGER = logging.getLogger(__name__)


class EZSPv6(EZSPv5):
    """EZSP Version 6 Protocol version handler."""

    VERSION = 6
    COMMANDS = commands.COMMANDS
    SCHEMAS = {
        bellows.config.CONF_EZSP_CONFIG: voluptuous.Schema(config.EZSP_SCHEMA),
        bellows.config.CONF_EZSP_POLICIES: voluptuous.Schema(config.EZSP_POLICIES_SCH),
    }

    async def initialize_network(self) -> t.sl_Status:
        (init_status,) = await self.networkInit(
            networkInitBitmask=t.EmberNetworkInitBitmask.NETWORK_INIT_NO_OPTIONS
        )
        return t.sl_Status.from_ember_status(init_status)
