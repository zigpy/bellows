""""EZSP Protocol version 7 protocol handler."""
from __future__ import annotations

import logging
from typing import AsyncGenerator

import voluptuous

import bellows.config
import bellows.types as t

from . import commands, config
from ..v6 import EZSPv6

LOGGER = logging.getLogger(__name__)


class EZSPv7(EZSPv6):
    """EZSP Version 7 Protocol version handler."""

    VERSION = 7
    COMMANDS = commands.COMMANDS
    SCHEMAS = {
        bellows.config.CONF_EZSP_CONFIG: voluptuous.Schema(config.EZSP_SCHEMA),
        bellows.config.CONF_EZSP_POLICIES: voluptuous.Schema(config.EZSP_POLICIES_SCH),
    }

    async def read_child_data(
        self,
    ) -> AsyncGenerator[tuple[t.NWK, t.EUI64, t.EmberNodeType], None]:
        for idx in range(0, 255 + 1):
            (status, rsp) = await self.getChildData(index=idx)
            status = t.sl_Status.from_ember_status(status)

            if status == t.sl_Status.NOT_JOINED:
                continue

            yield rsp.id, rsp.eui64, rsp.type
