""""EZSP Protocol version 4 command."""
from __future__ import annotations

import logging
from typing import AsyncGenerator, Iterable

import voluptuous as vol
import zigpy.state

import bellows.config
from bellows.ezsp.config import DEFAULT_CONFIG_LEGACY
import bellows.types as t
from bellows.zigbee.util import ezsp_key_to_zigpy_key

from . import commands, config
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
    CONFIG = DEFAULT_CONFIG_LEGACY

    def _ezsp_frame_tx(self, name: str) -> bytes:
        """Serialize the frame id."""
        c = self.COMMANDS[name]
        return bytes([self._seq & 0xFF, 0, c[0]])

    def _ezsp_frame_rx(self, data: bytes) -> tuple[int, int, bytes]:
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
            t.EzspConfigId.CONFIG_KEY_TABLE_SIZE
        )

        for index in range(key_table_size):
            (status, key) = await self.getKeyTableEntry(index)
            status = t.sl_Status.from_ember_status(status)

            if status == t.sl_Status.INVALID_INDEX:
                break
            elif status == t.sl_Status.NOT_FOUND:
                continue

            assert t.sl_Status.from_ember_status(status) == t.sl_Status.OK
            yield ezsp_key_to_zigpy_key(key)

    async def read_address_table(self) -> AsyncGenerator[tuple[t.NWK, t.EUI64], None]:
        # v4 can crash when getAddressTableRemoteNodeId(32) is received: undefined_0x8a
        # We need this function to be an async generator even if it does nothing
        if False:
            yield

    async def get_network_key(self) -> zigpy.state.Key:
        (status, ezsp_network_key) = await self.getKey(
            t.EmberKeyType.CURRENT_NETWORK_KEY
        )
        assert t.sl_Status.from_ember_status(status) == t.sl_Status.OK
        return ezsp_key_to_zigpy_key(ezsp_network_key)

    async def get_tc_link_key(self) -> zigpy.state.Key:
        (status, ezsp_tc_link_key) = await self.getKey(
            t.EmberKeyType.TRUST_CENTER_LINK_KEY
        )
        assert t.sl_Status.from_ember_status(status) == t.sl_Status.OK
        return ezsp_key_to_zigpy_key(ezsp_tc_link_key)

    async def write_nwk_frame_counter(self, frame_counter: t.uint32_t) -> None:
        # Not supported in EZSPv4
        pass

    async def write_aps_frame_counter(self, frame_counter: t.uint32_t) -> None:
        # Not supported in EZSPv4
        pass

    async def write_link_keys(self, keys: Iterable[zigpy.state.Key]) -> None:
        for key in keys:
            # XXX: is there no way to set the outgoing frame counter or seq?
            (status,) = await self.addOrUpdateKeyTableEntry(
                key.partner_ieee, True, key.key
            )

            if t.sl_Status.from_ember_status(status) != t.sl_Status.OK:
                LOGGER.warning("Couldn't add %s key: %s", key, status)

    async def write_child_data(self, children: dict[t.EUI64, t.NWK]) -> None:
        # Not supported in EZSPv4
        pass

    async def initialize_network(self) -> t.sl_Status:
        (init_status,) = await self.networkInitExtended(0x0000)
        return t.sl_Status.from_ember_status(init_status)

    async def factory_reset(self) -> None:
        await self.clearKeyTable()

    async def send_unicast(
        self,
        nwk: t.NWK,
        aps_frame: t.EmberApsFrame,
        message_tag: t.uint8_t,
        data: bytes,
    ) -> tuple[t.sl_Status, t.uint8_t]:
        status, sequence = await self.sendUnicast(
            t.EmberOutgoingMessageType.OUTGOING_DIRECT,
            t.EmberNodeId(nwk),
            aps_frame,
            message_tag,
            data,
        )

        return t.sl_Status.from_ember_status(status), sequence

    async def send_multicast(
        self,
        aps_frame: t.EmberApsFrame,
        radius: t.uint8_t,
        non_member_radius: t.uint8_t,
        message_tag: t.uint8_t,
        data: bytes,
    ) -> tuple[t.sl_Status, t.uint8_t]:
        status, sequence = await self.sendMulticast(
            aps_frame,
            radius,
            non_member_radius,
            message_tag,
            data,
        )

        return t.sl_Status.from_ember_status(status), sequence

    async def send_broadcast(
        self,
        address: t.BroadcastAddress,
        aps_frame: t.EmberApsFrame,
        radius: t.uint8_t,
        message_tag: t.uint8_t,
        aps_sequence: t.uint8_t,
        data: bytes,
    ) -> tuple[t.sl_Status, t.uint8_t]:
        # `aps_sequence` is not used

        status, sequence = await self.sendBroadcast(
            address,
            aps_frame,
            radius,
            message_tag,
            data,
        )

        return t.sl_Status.from_ember_status(status), sequence
