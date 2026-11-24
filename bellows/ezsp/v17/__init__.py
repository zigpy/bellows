""""EZSP Protocol version 17 protocol handler."""
from __future__ import annotations

import logging

import voluptuous as vol

import bellows.config
from bellows.exception import InvalidCommandError

from . import commands, config
from ..v16 import EZSPv16

LOGGER = logging.getLogger(__name__)


class EZSPv17(EZSPv16):
    """EZSP Version 17 Protocol version handler."""

    VERSION = 17
    COMMANDS = commands.COMMANDS
    SCHEMAS = {
        bellows.config.CONF_EZSP_CONFIG: vol.Schema(config.EZSP_SCHEMA),
        bellows.config.CONF_EZSP_POLICIES: vol.Schema(config.EZSP_POLICIES_SCH),
    }

    async def clear_gp_tables(self) -> None:
        try:
            await self.gpSinkTableClearAll()
            await self.gpClearProxyTable()
        except InvalidCommandError:
            LOGGER.debug("The NCP has no Green Power tables")
