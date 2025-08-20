""""EZSP Protocol version 10 protocol handler."""
from __future__ import annotations

import logging

import voluptuous

import bellows.config
import bellows.types as t

from . import commands, config
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

    async def write_child_data(self, children: dict[t.EUI64, t.NWK]) -> None:
        for index, (eui64, nwk) in enumerate(children.items()):
            await self.setChildData(
                index=index,
                child_data=t.EmberChildDataV10(
                    eui64=eui64,
                    type=t.EmberNodeType.SLEEPY_END_DEVICE,
                    id=nwk,
                    # The rest are unused when setting child data
                    phy=0,
                    power=0,
                    timeout=0,
                    timeout_remaining=0,
                ),
            )

            rsp = await self.getTokenData(
                token=t.NV3KeyId.NVM3KEY_STACK_CHILD_TABLE, index=index
            )
            assert t.sl_Status.from_ember_status(rsp.status) == t.sl_Status.OK

            entry, remaining = t.NV3ChildTableEntry.deserialize(rsp.value)
            assert not remaining
            assert entry.eui64 == eui64
            assert entry.id == nwk

            if entry.flags != 0x80:
                entry.flags = 0x80

                (status,) = await self.setTokenData(
                    token=t.NV3KeyId.NVM3KEY_STACK_CHILD_TABLE,
                    index=index,
                    token_data=entry.replace(flags=0x80).serialize(),
                )
                assert t.sl_Status.from_ember_status(status) == t.sl_Status.OK
