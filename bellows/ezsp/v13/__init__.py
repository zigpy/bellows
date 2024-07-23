""""EZSP Protocol version 13 protocol handler."""
from __future__ import annotations

import logging
from typing import AsyncGenerator, Iterable

import voluptuous as vol
from zigpy.exceptions import NetworkNotFormed
import zigpy.state

import bellows.config
import bellows.types as t

from . import commands, config
from ..v12 import EZSPv12

LOGGER = logging.getLogger(__name__)


class EZSPv13(EZSPv12):
    """EZSP Version 13 Protocol version handler."""

    VERSION = 13
    COMMANDS = commands.COMMANDS
    SCHEMAS = {
        bellows.config.CONF_EZSP_CONFIG: vol.Schema(config.EZSP_SCHEMA),
        bellows.config.CONF_EZSP_POLICIES: vol.Schema(config.EZSP_POLICIES_SCH),
    }

    # TODO: does this command go in v12 or here?
    async def add_transient_link_key(
        self, ieee: t.EUI64, key: t.KeyData
    ) -> t.sl_Status:
        (status,) = await self.importTransientKey(
            eui64=ieee,
            plaintext_key=key,
            flags=t.SecurityManagerContextFlags.NONE,
        )

        return t.sl_Status.from_ember_status(status)

    async def read_link_keys(self) -> AsyncGenerator[zigpy.state.Key, None]:
        (status, key_table_size) = await self.getConfigurationValue(
            configId=t.EzspConfigId.CONFIG_KEY_TABLE_SIZE
        )

        for index in range(key_table_size):
            (
                eui64,
                plaintext_key,
                key_data,
                status,
            ) = await self.exportLinkKeyByIndex(index=index)

            if status != t.sl_Status.OK:
                continue

            yield zigpy.state.Key(
                key=plaintext_key,
                tx_counter=key_data.outgoing_frame_counter,
                rx_counter=key_data.incoming_frame_counter,
                partner_ieee=eui64,
            )

    async def get_network_key(self) -> zigpy.state.Key:
        network_key_data, status = await self.exportKey(
            context=t.SecurityManagerContextV13(
                core_key_type=t.SecurityManagerKeyType.NETWORK,
                key_index=0,
                derived_type=t.SecurityManagerDerivedKeyTypeV13.NONE,
                eui64=t.EUI64.convert("00:00:00:00:00:00:00:00"),
                multi_network_index=0,
                flags=t.SecurityManagerContextFlags.NONE,
                psa_key_alg_permission=0,
            )
        )

        assert t.sl_Status.from_ember_status(status) == t.sl_Status.OK

        (status, network_key_info) = await self.getNetworkKeyInfo()
        assert t.sl_Status.from_ember_status(status) == t.sl_Status.OK

        if not network_key_info.network_key_set:
            raise NetworkNotFormed("Network key is not set")

        return zigpy.state.Key(
            key=network_key_data,
            tx_counter=network_key_info.network_key_frame_counter,
            seq=network_key_info.network_key_sequence_number,
        )

    async def get_tc_link_key(self) -> zigpy.state.Key:
        tc_link_key_data, status = await self.exportKey(
            context=t.SecurityManagerContextV13(
                core_key_type=t.SecurityManagerKeyType.TC_LINK,
                key_index=0,
                derived_type=t.SecurityManagerDerivedKeyTypeV13.NONE,
                eui64=t.EUI64.convert("00:00:00:00:00:00:00:00"),
                multi_network_index=0,
                flags=t.SecurityManagerContextFlags.NONE,
                psa_key_alg_permission=0,
            )
        )

        assert t.sl_Status.from_ember_status(status) == t.sl_Status.OK

        return zigpy.state.Key(key=tc_link_key_data)

    async def write_link_keys(self, keys: Iterable[zigpy.state.Key]) -> None:
        for index, key in enumerate(keys):
            (status,) = await self.importLinkKey(
                index=index, address=key.partner_ieee, key=key.key
            )

            if t.sl_Status.from_ember_status(status) != t.sl_Status.OK:
                LOGGER.warning("Couldn't add %s key: %s", key, status)

    async def factory_reset(self) -> None:
        await self.tokenFactoryReset(excludeOutgoingFC=False, excludeBootCounter=False)
        await self.clearKeyTable()
