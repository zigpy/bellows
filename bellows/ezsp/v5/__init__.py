""""EZSP Protocol version 5 protocol handler."""
import logging
from typing import Tuple

import voluptuous

import bellows.config

from . import commands, config, types as v5_types
from ..v4 import EZSPv4

EZSP_VERSION = 5
LOGGER = logging.getLogger(__name__)


class EZSPv5(EZSPv4):
    """EZSP Version 5 Protocol version handler."""

    COMMANDS = commands.COMMANDS
    SCHEMAS = {
        bellows.config.CONF_EZSP_CONFIG: voluptuous.Schema(config.EZSP_SCHEMA),
        bellows.config.CONF_EZSP_POLICIES: voluptuous.Schema(config.EZSP_POLICIES_SCH),
    }
    types = v5_types

    def _ezsp_frame_tx(self, name: str) -> bytes:
        """Serialize the frame id."""
        cmd_id = self.COMMANDS[name][0]
        frame = [self._seq, 0x00, 0xFF, 0x00, cmd_id]
        return bytes(frame)

    def _ezsp_frame_rx(self, data: bytes) -> Tuple[int, int, bytes]:
        """Handler for received data frame."""
        return data[0], data[4], data[5:]

    async def pre_permit(self, time_s: int) -> None:
        """Add pre-shared TC Link key."""
        wild_card_ieee = v5_types.EmberEUI64([0xFF] * 8)
        tc_link_key = v5_types.EmberKeyData(b"ZigBeeAlliance09")
        await self.addTransientLinkKey(wild_card_ieee, tc_link_key)
