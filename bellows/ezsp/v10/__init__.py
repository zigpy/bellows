""""EZSP Protocol version 10 protocol handler."""
from __future__ import annotations

import logging

import voluptuous

import bellows.config
from bellows.exception import InvalidCommandError
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

            # There is unfortunately an SDK bug with `setChildData`: some sort of
            # internal flag in the NVRAM child table is not correctly set (0x00). For
            # working coordinators, it holds the value 0x80. We need to carefully tweak
            # this value to ensure restoration works 100%.
            try:
                rsp = await self.getTokenData(
                    token=t.NV3KeyId.NVM3KEY_STACK_CHILD_TABLE, index=index
                )
                if t.sl_Status.from_ember_status(rsp.status) != t.sl_Status.OK:
                    LOGGER.warning(
                        "Failed to read NVRAM child info for %d: %r", index, rsp
                    )
                    continue
            except (InvalidCommandError, AttributeError):
                LOGGER.debug("NV3 interface not available, skipping")
                continue

            # We need to be careful and ensure that the value in NVRAM matches our
            # expected format (other than the flag byte)
            expected_entry = t.NV3ChildTableEntry(eui64=eui64, id=nwk, flags=0x80)

            if rsp.value != expected_entry.replace(flags=rsp.value[-1]).serialize():
                LOGGER.warning(
                    "Unexpected NVRAM child info for %d: %r, expected %r",
                    index,
                    rsp.value,
                    expected_entry.serialize(),
                )
                continue

            # Once we have it fully parsed, write in the correct value (if necessary).
            # The reason we do this roundabout read/write dance is because we can't be
            # sure the format in NVRAM will be static.
            entry, remaining = t.NV3ChildTableEntry.deserialize(rsp.value)
            assert not remaining

            if entry.flags != 0x80:
                (status,) = await self.setTokenData(
                    token=t.NV3KeyId.NVM3KEY_STACK_CHILD_TABLE,
                    index=index,
                    token_data=expected_entry.serialize(),
                )
                assert t.sl_Status.from_ember_status(status) == t.sl_Status.OK
