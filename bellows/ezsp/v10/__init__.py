""""EZSP Protocol version 10 protocol handler."""
import asyncio
import logging
from typing import Tuple

import voluptuous

import bellows.config

from . import commands, config, types as v10_types
from .. import protocol

LOGGER = logging.getLogger(__name__)


class EZSPv10(protocol.ProtocolHandler):
    """EZSP Version 10 Protocol version handler."""

    VERSION = 10
    COMMANDS = commands.COMMANDS
    SCHEMAS = {
        bellows.config.CONF_EZSP_CONFIG: voluptuous.Schema(config.EZSP_SCHEMA),
        bellows.config.CONF_EZSP_POLICIES: voluptuous.Schema(config.EZSP_POLICIES_SCH),
    }
    types = v10_types

    def _ezsp_frame_tx(self, name: str) -> bytes:
        """Serialize the frame id."""
        cmd_id = self.COMMANDS[name][0]
        hdr = [self._seq, 0x00, 0x01]
        return bytes(hdr) + self.types.uint16_t(cmd_id).serialize()

    def _ezsp_frame_rx(self, data: bytes) -> Tuple[int, int, bytes]:
        """Handler for received data frame."""
        seq, data = data[0], data[3:]
        frame_id, data = self.types.uint16_t.deserialize(data)

        return seq, frame_id, data

    async def pre_permit(self, time_s: int) -> None:
        """Temporarily change TC policy while allowing new joins."""
        wild_card_ieee = v10_types.EmberEUI64([0xFF] * 8)
        tc_link_key = v10_types.EmberKeyData(b"ZigBeeAlliance09")
        await self.addTransientLinkKey(wild_card_ieee, tc_link_key)
        await self.setPolicy(
            v10_types.EzspPolicyId.TRUST_CENTER_POLICY,
            v10_types.EzspDecisionBitmask.ALLOW_JOINS
            | v10_types.EzspDecisionBitmask.ALLOW_UNSECURED_REJOINS,
        )
        await asyncio.sleep(time_s + 2)
        await self.setPolicy(
            v10_types.EzspPolicyId.TRUST_CENTER_POLICY,
            self.tc_policy,
        )

    async def set_source_routing(self) -> None:
        """Enable source routing on NCP."""
        await self.setSourceRouteDiscoveryMode(1)
