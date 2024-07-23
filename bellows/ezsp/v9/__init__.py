""""EZSP Protocol version 9 protocol handler."""
from __future__ import annotations

import logging

import voluptuous as vol

import bellows.config
import bellows.types as t

from . import commands, config
from ..v8 import EZSPv8

LOGGER = logging.getLogger(__name__)


class EZSPv9(EZSPv8):
    """EZSP Version 9 Protocol version handler."""

    VERSION = 9
    COMMANDS = commands.COMMANDS
    SCHEMAS = {
        bellows.config.CONF_EZSP_CONFIG: vol.Schema(config.EZSP_SCHEMA),
        bellows.config.CONF_EZSP_POLICIES: vol.Schema(config.EZSP_POLICIES_SCH),
    }

    async def write_child_data(self, children: dict[t.EUI64, t.NWK]) -> None:
        for index, (eui64, nwk) in enumerate(children.items()):
            await self.setChildData(
                index=index,
                child_data=t.EmberChildDataV7(
                    eui64=eui64,
                    type=t.EmberNodeType.SLEEPY_END_DEVICE,
                    id=nwk,
                    # The rest are unused when setting child data
                    phy=0,
                    power=0,
                    timeout=0,
                ),
            )

    async def set_source_route(self, nwk: t.NWK, relays: list[t.NWK]) -> t.sl_Status:
        # While the command may succeed, it does absolutely nothing
        return t.sl_Status.OK
