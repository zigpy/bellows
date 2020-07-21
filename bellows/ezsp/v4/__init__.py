""""EZSP Protocol version 4 command."""
import asyncio
import binascii
import logging
from typing import Any, Dict, Tuple

from .. import protocol
from . import config, commands, types as v4_types

EZSP_VERSION = 4
LOGGER = logging.getLogger(__name__)


class EZSPv4(protocol.ProtocolHandler):
    """EZSP Version 4 Protocol version handler."""

    COMMANDS = commands.COMMANDS
    SCHEMA = config.EZSP_SCHEMA
    types = v4_types

    def _ezsp_frame(self, name: str, *args: Tuple[Any, ...]) -> bytes:
        """Serialize the named frame and data."""
        c = self.COMMANDS[name]
        frame = bytes([self._seq & 0xFF, 0, c[0]])  # Frame control. TODO.  # Frame ID
        data = self.types.serialize(args, c[1])
        return frame + data

    async def initialize(self, ezsp_config: Dict) -> None:
        """Initialize EmberZNet per passed configuration."""

        ezsp_config = self.SCHEMA(ezsp_config)
        for config, value in ezsp_config.items():
            if config in (self.types.EzspConfigId.CONFIG_PACKET_BUFFER_COUNT.name,):
                # we want to set these last
                continue
            await self._cfg(self.types.EzspConfigId[config], value)

        c = self.types.EzspConfigId
        await self._cfg(c.CONFIG_END_DEVICE_POLL_TIMEOUT, 60)
        await self._cfg(c.CONFIG_END_DEVICE_POLL_TIMEOUT_SHIFT, 8)
        await self._cfg(
            self.types.EzspConfigId.CONFIG_PACKET_BUFFER_COUNT,
            ezsp_config[c.CONFIG_PACKET_BUFFER_COUNT.name],
        )

    def __call__(self, data: bytes) -> None:
        """Handler for received data frame."""
        sequence, frame_id, data = data[0], data[2], data[3:]
        frame_name = self.COMMANDS_BY_ID[frame_id][0]
        LOGGER.debug(
            "Application frame %s (%s) received: %s",
            frame_id,
            frame_name,
            binascii.hexlify(data),
        )

        if sequence in self._awaiting:
            expected_id, schema, future = self._awaiting.pop(sequence)
            assert expected_id == frame_id
            result, data = self.types.deserialize(data, schema)
            try:
                future.set_result(result)
            except asyncio.InvalidStateError:
                LOGGER.debug(
                    "Error processing %s response. %s command timed out?",
                    sequence,
                    self.COMMANDS_BY_ID.get(expected_id, [expected_id])[0],
                )
        else:
            schema = self.COMMANDS_BY_ID[frame_id][2]
            frame_name = self.COMMANDS_BY_ID[frame_id][0]
            result, data = self.types.deserialize(data, schema)
            self._handle_callback(frame_name, result)
