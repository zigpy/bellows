""""EZSP Protocol version 8 protocol handler."""
import logging
from typing import Tuple

import voluptuous

from . import commands, config as v8_config, types as v8_types
from .. import protocol

EZSP_VERSION = 8
LOGGER = logging.getLogger(__name__)


class EZSPv8(protocol.ProtocolHandler):
    """EZSP Version 8 Protocol version handler."""

    COMMANDS = commands.COMMANDS
    SCHEMA = voluptuous.Schema(v8_config.EZSP_SCHEMA)
    types = v8_types

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

    async def update_policies(self, zigpy_config: dict) -> None:
        """Set up the policies for what the NCP should do."""

        v = await self.setPolicy(
            self.types.EzspPolicyId.TC_KEY_REQUEST_POLICY,
            self.types.EzspDecisionId.GENERATE_NEW_TC_LINK_KEY,
        )
        assert v[0] == self.types.EmberStatus.SUCCESS  # TODO: Better check
        v = await self.setPolicy(
            self.types.EzspPolicyId.APP_KEY_REQUEST_POLICY,
            self.types.EzspDecisionId.DENY_APP_KEY_REQUESTS,
        )
        assert v[0] == self.types.EmberStatus.SUCCESS  # TODO: Better check
        v = await self.setPolicy(
            self.types.EzspPolicyId.TRUST_CENTER_POLICY,
            v8_types.EzspDecisionBitmask.ALLOW_JOINS
            | v8_types.EzspDecisionBitmask.JOINS_USE_INSTALL_CODE_KEY
            | v8_types.EzspDecisionBitmask.IGNORE_UNSECURED_REJOINS,
        )
        assert v[0] == self.types.EmberStatus.SUCCESS  # TODO: Better check
