""""EZSP Protocol version 6 protocol handler."""
import logging

import voluptuous

import bellows.config
from bellows.exception import InvalidCommandError
import bellows.types as t

from . import commands, config
from ..v5 import EZSPv5

LOGGER = logging.getLogger(__name__)


class EZSPv6(EZSPv5):
    """EZSP Version 6 Protocol version handler."""

    VERSION = 6
    COMMANDS = commands.COMMANDS
    SCHEMAS = {
        bellows.config.CONF_EZSP_CONFIG: voluptuous.Schema(config.EZSP_SCHEMA),
        bellows.config.CONF_EZSP_POLICIES: voluptuous.Schema(config.EZSP_POLICIES_SCH),
    }

    async def initialize_network(self) -> t.sl_Status:
        (init_status,) = await self.networkInit(
            networkInitBitmask=t.EmberNetworkInitBitmask.NETWORK_INIT_NO_OPTIONS
        )
        return t.sl_Status.from_ember_status(init_status)

    async def clear_gp_tables(self) -> None:
        # The proxy table has no bulk clear before EZSPv17
        try:
            await self.gpClearSinkTable()
        except InvalidCommandError:
            LOGGER.debug("The NCP has no Green Power sink table")

    async def send_multicast(
        self,
        aps_frame: t.EmberApsFrame,
        radius: t.uint8_t,
        non_member_radius: t.uint8_t,
        message_tag: t.uint8_t,
        data: bytes,
        alias: t.NWK | None = None,
        alias_seq: t.uint8_t | None = None,
    ) -> tuple[t.sl_Status, t.uint8_t]:
        if alias is None:
            return await super().send_multicast(
                aps_frame=aps_frame,
                radius=radius,
                non_member_radius=non_member_radius,
                message_tag=message_tag,
                data=data,
            )

        status, sequence = await self.sendMulticastWithAlias(
            apsFrame=aps_frame,
            hops=radius,
            nonmemberRadius=non_member_radius,
            alias=t.EmberNodeId(alias),
            nwkSequence=t.uint8_t(0 if alias_seq is None else alias_seq),
            messageTag=message_tag,
            messageContents=data,
        )

        return t.sl_Status.from_ember_status(status), sequence
