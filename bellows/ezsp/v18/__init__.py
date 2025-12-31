""""EZSP Protocol version 18 protocol handler."""
from __future__ import annotations

import voluptuous as vol

import bellows.config
import bellows.types as t

from . import commands, config
from ..v17 import EZSPv17


class EZSPv18(EZSPv17):
    """EZSP Version 18 Protocol version handler."""

    VERSION = 18
    COMMANDS = commands.COMMANDS
    SCHEMAS = {
        bellows.config.CONF_EZSP_CONFIG: vol.Schema(config.EZSP_SCHEMA),
        bellows.config.CONF_EZSP_POLICIES: vol.Schema(config.EZSP_POLICIES_SCH),
    }

    async def send_unicast(
        self,
        nwk: t.NWK,
        aps_frame: t.EmberApsFrame,
        message_tag: t.uint8_t,
        data: bytes,
    ) -> tuple[t.sl_Status, t.uint8_t]:
        status, sequence = await self.sendUnicast(
            message_type=t.EmberOutgoingMessageType.OUTGOING_DIRECT,
            nwk=nwk,
            aps_frame=t.EmberApsFrameV18(
                profileId=aps_frame.profileId,
                clusterId=aps_frame.clusterId,
                sourceEndpoint=aps_frame.sourceEndpoint,
                destinationEndpoint=aps_frame.destinationEndpoint,
                options=aps_frame.options,
                groupId=aps_frame.groupId,
                sequence=aps_frame.sequence,
                radius=0,
            ),
            message_tag=message_tag,
            message=data,
        )

        return status, sequence

    async def send_multicast(
        self,
        aps_frame: t.EmberApsFrame,
        radius: t.uint8_t,
        non_member_radius: t.uint8_t,
        message_tag: t.uint8_t,
        data: bytes,
    ) -> tuple[t.sl_Status, t.uint8_t]:
        status, sequence = await self.sendMulticast(
            aps_frame=t.EmberApsFrameV18(
                profileId=aps_frame.profileId,
                clusterId=aps_frame.clusterId,
                sourceEndpoint=aps_frame.sourceEndpoint,
                destinationEndpoint=aps_frame.destinationEndpoint,
                options=aps_frame.options,
                groupId=aps_frame.groupId,
                sequence=aps_frame.sequence,
                radius=radius,
            ),
            hops=radius,
            broadcast_addr=t.BroadcastAddress.RX_ON_WHEN_IDLE,
            alias=0x0000,
            sequence=aps_frame.sequence,
            message_tag=message_tag,
            message=data,
        )

        return status, sequence

    async def send_broadcast(
        self,
        address: t.BroadcastAddress,
        aps_frame: t.EmberApsFrame,
        radius: t.uint8_t,
        message_tag: t.uint8_t,
        aps_sequence: t.uint8_t,
        data: bytes,
    ) -> tuple[t.sl_Status, t.uint8_t]:
        status, sequence = await self.sendBroadcast(
            alias=0x0000,
            destination=address,
            sequence=aps_sequence,
            aps_frame=t.EmberApsFrameV18(
                profileId=aps_frame.profileId,
                clusterId=aps_frame.clusterId,
                sourceEndpoint=aps_frame.sourceEndpoint,
                destinationEndpoint=aps_frame.destinationEndpoint,
                options=aps_frame.options,
                groupId=aps_frame.groupId,
                sequence=aps_frame.sequence,
                radius=radius,
            ),
            radius=radius,
            message_tag=message_tag,
            message=data,
        )

        return status, sequence
