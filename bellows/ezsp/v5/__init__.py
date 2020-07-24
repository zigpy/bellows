""""EZSP Protocol version 5 protocol handler."""
import logging
from typing import Tuple

import voluptuous

from . import commands, config as v5_config, types as v5_types
from .. import protocol

EZSP_VERSION = 5
LOGGER = logging.getLogger(__name__)


class EZSPv5(protocol.ProtocolHandler):
    """EZSP Version 5 Protocol version handler."""

    COMMANDS = commands.COMMANDS
    SCHEMA = voluptuous.Schema(v5_config.EZSP_SCHEMA)
    types = v5_types

    def _ezsp_frame_tx(self, name: str) -> bytes:
        """Serialize the frame id."""
        c = self.COMMANDS[name]
        frame = [self._seq, 0x00, 0xFF, 0x00, c[0]]
        return bytes(frame)

    def _ezsp_frame_rx(self, data: bytes) -> Tuple[int, int, bytes]:
        """Handler for received data frame."""
        return data[0], data[4], data[5:]
