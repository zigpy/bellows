""""EZSP Protocol version 4 command."""
import logging
from typing import Tuple

import bellows.config
import voluptuous
from zigpy.typing import DeviceType

from . import commands, config, types as v4_types
from .. import protocol

EZSP_VERSION = 4
LOGGER = logging.getLogger(__name__)
MTOR_MIN_INTERVAL = 600
MTOR_MAX_INTERVAL = 1800


class EZSPv4(protocol.ProtocolHandler):
    """EZSP Version 4 Protocol version handler."""

    COMMANDS = commands.COMMANDS
    SCHEMAS = {
        bellows.config.CONF_EZSP_CONFIG: voluptuous.Schema(config.EZSP_SCHEMA),
        bellows.config.CONF_EZSP_POLICIES: voluptuous.Schema(config.EZSP_POLICIES_SCH),
    }
    types = v4_types

    def _ezsp_frame_tx(self, name: str) -> bytes:
        """Serialize the frame id."""
        c = self.COMMANDS[name]
        return bytes([self._seq & 0xFF, 0, c[0]])  # Frame control. TODO.  # Frame ID

    def _ezsp_frame_rx(self, data: bytes) -> Tuple[int, int, bytes]:
        """Handler for received data frame."""
        return data[0], data[2], data[3:]

    def set_source_route(self, device: DeviceType) -> v4_types.EmberStatus:
        """Set source route to the device if known."""
        if device.relays is None:
            return v4_types.EmberStatus.ERR_FATAL

        return self.setSourceRoute(device.nwk, device.relays)

    async def set_source_routing(self) -> None:
        """Enable source routing on NCP."""
        res = await self.setConcentrator(
            True,
            v4_types.EmberConcentratorType.HIGH_RAM_CONCENTRATOR,
            MTOR_MIN_INTERVAL,
            MTOR_MAX_INTERVAL,
            2,
            5,
            0,
        )
        LOGGER.debug("Set concentrator type: %s", res)
        if res[0] != v4_types.EmberStatus.SUCCESS:
            LOGGER.warning("Couldn't set concentrator type %s: %s", True, res)
