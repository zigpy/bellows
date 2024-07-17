""""EZSP Protocol version 4 command."""
import logging
from typing import AsyncGenerator, Tuple

import voluptuous as vol
import zigpy.state

import bellows.config
import bellows.types as t
from bellows.zigbee.util import ezsp_key_to_zigpy_key

from . import commands, config, types as v4_types
from .. import protocol

LOGGER = logging.getLogger(__name__)


class EZSPv4(protocol.ProtocolHandler):
    """EZSP Version 4 Protocol version handler."""

    VERSION = 4
    COMMANDS = commands.COMMANDS
    SCHEMAS = {
        bellows.config.CONF_EZSP_CONFIG: vol.Schema(config.EZSP_SCHEMA),
        bellows.config.CONF_EZSP_POLICIES: vol.Schema(config.EZSP_POLICIES_SCH),
    }
    types = v4_types

    def _ezsp_frame_tx(self, name: str) -> bytes:
        """Serialize the frame id."""
        c = self.COMMANDS[name]
        return bytes([self._seq & 0xFF, 0, c[0]])

    def _ezsp_frame_rx(self, data: bytes) -> Tuple[int, int, bytes]:
        """Handler for received data frame."""
        return data[0], data[2], data[3:]

    async def pre_permit(self, time_s: int) -> None:
        pass

    async def read_child_data(
        self,
    ) -> AsyncGenerator[tuple[t.NWK, t.EUI64, t.EmberNodeType], None]:
        for idx in range(0, 255 + 1):
            (status, nwk, eui64, node_type) = await self.getChildData(idx)
            status = t.sl_Status.from_ember_status(status)

            if status == t.sl_Status.NOT_JOINED:
                continue

            yield nwk, eui64, node_type

    async def read_link_keys(self) -> AsyncGenerator[zigpy.state.Key, None]:
        (status, key_table_size) = await self.getConfigurationValue(
            self.types.EzspConfigId.CONFIG_KEY_TABLE_SIZE
        )

        for index in range(key_table_size):
            (status, key) = await self.getKeyTableEntry(index)
            status = t.sl_Status.from_ember_status(status)

            if status == t.sl_Status.INVALID_INDEX:
                break
            elif status == t.sl_Status.NOT_FOUND:
                continue

            assert t.sl_Status.from_ember_status(status) == t.sl_Status.OK
            yield ezsp_key_to_zigpy_key(key, self)

    async def read_address_table(self) -> AsyncGenerator[tuple[t.NWK, t.EUI64], None]:
        # v4 can crash when getAddressTableRemoteNodeId(32) is received: undefined_0x8a
        # We need this function to be an async generator even if it does nothing
        if False:
            yield
