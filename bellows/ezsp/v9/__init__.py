""""EZSP Protocol version 9 protocol handler."""
import logging

import voluptuous

import bellows.config
import bellows.types as t

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

    async def write_child_table(self, children: dict[t.EUI64, t.NWK]) -> None:
        for index, (eui64, nwk) in enumerate(children.items()):
            await self.setChildData(
                index,
                self.types.EmberChildData(
                    eui64=eui64,
                    type=t.EmberNodeType.SLEEPY_END_DEVICE,
                    id=nwk,
                    # The rest are unused when setting child data
                    phy=0,
                    power=0,
                    timeout=0,
                ),
            )
