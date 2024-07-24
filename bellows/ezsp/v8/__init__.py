""""EZSP Protocol version 8 protocol handler."""
import asyncio
import logging
from typing import Tuple

import voluptuous

import bellows.config
import bellows.types as t

from . import commands, config
from ..v7 import EZSPv7

LOGGER = logging.getLogger(__name__)


class EZSPv8(EZSPv7):
    """EZSP Version 8 Protocol version handler."""

    VERSION = 8
    COMMANDS = commands.COMMANDS
    SCHEMAS = {
        bellows.config.CONF_EZSP_CONFIG: voluptuous.Schema(config.EZSP_SCHEMA),
        bellows.config.CONF_EZSP_POLICIES: voluptuous.Schema(config.EZSP_POLICIES_SCH),
    }

    def _ezsp_frame_tx(self, name: str) -> bytes:
        """Serialize the frame id."""
        cmd_id = self.COMMANDS[name][0]
        hdr = [self._seq, 0x00, 0x01]
        return bytes(hdr) + t.uint16_t(cmd_id).serialize()

    def _ezsp_frame_rx(self, data: bytes) -> Tuple[int, int, bytes]:
        """Handler for received data frame."""
        seq, data = data[0], data[3:]
        frame_id, data = t.uint16_t.deserialize(data)

        return seq, frame_id, data

    async def pre_permit(self, time_s: int) -> None:
        """Temporarily change TC policy while allowing new joins."""
        await super().pre_permit(time_s)
        await self.setPolicy(
            policyId=t.EzspPolicyId.TRUST_CENTER_POLICY,
            decisionId=(
                t.EzspDecisionBitmask.ALLOW_JOINS
                | t.EzspDecisionBitmask.ALLOW_UNSECURED_REJOINS
            ),
        )
        await asyncio.sleep(time_s + 2)
        await self.setPolicy(
            policyId=t.EzspPolicyId.TRUST_CENTER_POLICY,
            decisionId=self.tc_policy,
        )
