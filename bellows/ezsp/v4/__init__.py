""""EZSP Protocol version 4 command."""
import logging
from typing import Tuple

import voluptuous

from . import commands, config as v4_config, types as v4_types
from .. import protocol

EZSP_VERSION = 4
LOGGER = logging.getLogger(__name__)


class EZSPv4(protocol.ProtocolHandler):
    """EZSP Version 4 Protocol version handler."""

    COMMANDS = commands.COMMANDS
    SCHEMA = voluptuous.Schema(v4_config.EZSP_SCHEMA)
    types = v4_types

    def _ezsp_frame_tx(self, name: str) -> bytes:
        """Serialize the frame id."""
        c = self.COMMANDS[name]
        return bytes([self._seq & 0xFF, 0, c[0]])  # Frame control. TODO.  # Frame ID

    def _ezsp_frame_rx(self, data: bytes) -> Tuple[int, int, bytes]:
        """Handler for received data frame."""
        return data[0], data[2], data[3:]
