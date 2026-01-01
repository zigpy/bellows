import asyncio
import logging
from unittest.mock import AsyncMock, MagicMock, call, patch

import pytest
import zigpy.types

from bellows.ezsp import EZSP
from bellows.ezsp.protocol import PacketReceivedEvent
import bellows.ezsp.v4
import bellows.ezsp.v9
from bellows.ezsp.v9.commands import GetTokenDataRsp
import bellows.types as t
from bellows.types import NV3KeyId
from bellows.uart import Gateway


@pytest.fixture
def prot_hndl():
    """Protocol handler mock."""
    app = MagicMock()
    gateway = Gateway(app)
    gateway._transport = AsyncMock()

    callback_handler = MagicMock()
    return bellows.ezsp.v4.EZSPv4(callback_handler, gateway)


@pytest.fixture
def prot_hndl_v9():
    """Protocol handler mock."""
    app = MagicMock()
    gateway = Gateway(app)
    gateway._transport = AsyncMock()

    callback_handler = MagicMock()
    return bellows.ezsp.v9.EZSPv9(callback_handler, gateway)


async def test_command(prot_hndl):
    with patch.object(prot_hndl._gw, "send_data") as mock_send_data:
        coro = prot_hndl.command("nop")
        asyncio.get_running_loop().call_soon(
            lambda: prot_hndl._awaiting[prot_hndl._seq - 1][2].set_result(True)
        )

        await coro

    assert mock_send_data.mock_calls == [call(b"\x00\x00\x05")]


def test_receive_reply(prot_hndl):
    callback_mock = MagicMock(spec_set=asyncio.Future)
    prot_hndl._awaiting[0] = (0, prot_hndl.COMMANDS["version"][2], callback_mock)
    prot_hndl(b"\x00\xff\x00\x04\x05\x06\x00")

    assert 0 not in prot_hndl._awaiting
    assert callback_mock.set_exception.call_count == 0
    assert callback_mock.set_result.call_count == 1
    callback_mock.set_result.assert_called_once_with([4, 5, 6])
    assert prot_hndl._handle_callback.call_count == 0


def test_receive_reply_after_timeout(prot_hndl):
    callback_mock = MagicMock(spec_set=asyncio.Future)
    callback_mock.set_result.side_effect = asyncio.InvalidStateError()
    prot_hndl._awaiting[0] = (0, prot_hndl.COMMANDS["version"][2], callback_mock)
    prot_hndl(b"\x00\xff\x00\x04\x05\x06\x00")

    assert 0 not in prot_hndl._awaiting
    assert callback_mock.set_exception.call_count == 0
    assert callback_mock.set_result.call_count == 1
    callback_mock.set_result.assert_called_once_with([4, 5, 6])
    assert prot_hndl._handle_callback.call_count == 0


def test_receive_reply_invalid_command(prot_hndl):
    callback_mock = MagicMock(spec_set=asyncio.Future)
    prot_hndl._awaiting[0] = (0, prot_hndl.COMMANDS["invalidCommand"][2], callback_mock)
    prot_hndl(b"\x00\xff\x58\x31")

    assert 0 not in prot_hndl._awaiting
    assert callback_mock.set_exception.call_count == 1
    assert callback_mock.set_result.call_count == 0
    assert prot_hndl._handle_callback.call_count == 0


async def test_update_policies(prot_hndl):
    """Test update_policies."""

    with patch.object(prot_hndl, "setPolicy", new=AsyncMock()) as pol_mock:
        pol_mock.return_value = (t.EzspStatus.SUCCESS,)
        await prot_hndl.update_policies({})

    with patch.object(prot_hndl, "setPolicy", new=AsyncMock()) as pol_mock:
        pol_mock.return_value = (t.EzspStatus.ERROR_OUT_OF_MEMORY,)
        with pytest.raises(AssertionError):
            await prot_hndl.update_policies({})


async def test_unknown_command(prot_hndl, caplog):
    """Test receiving an unknown command."""

    unregistered_command = 0x04

    with caplog.at_level(logging.WARNING):
        prot_hndl(bytes([0x00, 0x00, unregistered_command, 0xAB, 0xCD]))

        assert "0x0004 received: b'abcd' (b'000004abcd')" in caplog.text


async def test_logging_frame_parsing_failure(prot_hndl, caplog) -> None:
    """Test logging when frame parsing fails."""

    with caplog.at_level(logging.WARNING):
        with pytest.raises(ValueError):
            prot_hndl(b"\xAA\xAA\x71\x22")

        assert "Failed to parse frame getKeyTableEntry: b'22'" in caplog.text


async def test_parsing_schema_response(prot_hndl_v9):
    """Test parsing data with a struct schema."""

    coro = prot_hndl_v9.command(
        "getTokenData", NV3KeyId.CREATOR_STACK_RESTORED_EUI64, 0
    )
    asyncio.get_running_loop().call_soon(
        lambda: prot_hndl_v9(
            bytes([prot_hndl_v9._seq - 1, 0x00, 0x00])
            + t.uint16_t(prot_hndl_v9.COMMANDS["getTokenData"][0]).serialize()
            + bytes([0xB5])
        )
    )

    rsp = await coro
    assert rsp == GetTokenDataRsp(status=t.EmberStatus.LIBRARY_NOT_PRESENT)


async def test_send_fragment_ack(prot_hndl, caplog):
    """Test the _send_fragment_ack method."""
    sender = 0x1D6F
    incoming_aps = t.EmberApsFrame(
        profileId=260,
        clusterId=65281,
        sourceEndpoint=2,
        destinationEndpoint=2,
        options=33088,
        groupId=512,
        sequence=238,
    )
    fragment_count = 2
    fragment_index = 0

    expected_ack_frame = t.EmberApsFrame(
        profileId=260,
        clusterId=65281,
        sourceEndpoint=2,
        destinationEndpoint=2,
        options=33088,
        groupId=((0xFF00) | (fragment_index & 0xFF)),
        sequence=238,
    )

    with patch.object(prot_hndl, "sendReply", new=AsyncMock()) as mock_send_reply:
        mock_send_reply.return_value = (t.EmberStatus.SUCCESS,)

        caplog.set_level(logging.DEBUG)
        status = await prot_hndl._send_fragment_ack(
            sender, incoming_aps, fragment_count, fragment_index
        )

        # Assertions
        assert status == t.EmberStatus.SUCCESS
        assert (
            "Sending fragment ack to 0x1d6f for fragment index=1/2".lower()
            in caplog.text.lower()
        )
        mock_send_reply.assert_called_once_with(sender, expected_ack_frame, b"")


async def test_incoming_fragmented_message_incomplete(prot_hndl, caplog):
    """Test handling of an incomplete fragmented message."""
    packet = b"\x90\x01\x45\x00\x05\x01\x01\xff\x02\x02\x40\x81\x00\x02\xee\xff\xf8\x6f\x1d\xff\xff\x01\xdd"

    # Parse packet manually to extract parameters for assertions
    sender = 0x1D6F
    aps_frame = t.EmberApsFrame(
        profileId=261,  # 0x0105
        clusterId=65281,  # 0xFF01
        sourceEndpoint=2,  # 0x02
        destinationEndpoint=2,  # 0x02
        options=33088,  # 0x8140 (APS_OPTION_FRAGMENT + others)
        groupId=512,  # 0x0002 (fragment_count=2, fragment_index=0)
        sequence=238,  # 0xEE
    )

    with patch.object(prot_hndl, "_send_fragment_ack", new=AsyncMock()) as mock_ack:
        mock_ack.return_value = None

        caplog.set_level(logging.DEBUG)
        prot_hndl(packet)

        assert len(prot_hndl._fragment_ack_tasks) == 1
        ack_task = next(iter(prot_hndl._fragment_ack_tasks))
        await asyncio.gather(ack_task)  # Ensure task completes and triggers callback
        assert (
            len(prot_hndl._fragment_ack_tasks) == 0
        ), "Done callback should have removed task"

        assert len(prot_hndl._handle_callback.mock_calls) == 1
        assert "Fragment reassembly not complete, waiting for more data" in caplog.text
        assert mock_ack.mock_calls == [call(sender, aps_frame, 2, 0)]


async def test_incoming_fragmented_message_complete(prot_hndl, caplog):
    """Test handling of a complete fragmented message."""
    packet1 = (
        b"\x90\x01\x45\x00\x04\x01\x01\xff\x02\x02\x40\x81\x00\x02\xee\xff\xf8\x6f\x1d\xff\xff\x09"
        + b"complete "
    )  # fragment index 0
    packet2 = (
        b"\x90\x01\x45\x00\x04\x01\x01\xff\x02\x02\x40\x81\x01\x02\xee\xff\xf8\x6f\x1d\xff\xff\x07"
        + b"message"
    )  # fragment index 1

    aps_frame_1 = t.EmberApsFrame(
        profileId=260,
        clusterId=0xFF01,
        sourceEndpoint=2,
        destinationEndpoint=2,
        options=(
            t.EmberApsOption.APS_OPTION_RETRY
            | t.EmberApsOption.APS_OPTION_ENABLE_ROUTE_DISCOVERY
            | t.EmberApsOption.APS_OPTION_FRAGMENT
        ),
        groupId=0x0200,  # fragment_count=2, fragment_index=0
        sequence=238,
    )

    aps_frame_2 = t.EmberApsFrame(
        profileId=260,
        clusterId=0xFF01,
        sourceEndpoint=2,
        destinationEndpoint=2,
        options=(
            t.EmberApsOption.APS_OPTION_RETRY
            | t.EmberApsOption.APS_OPTION_ENABLE_ROUTE_DISCOVERY
            | t.EmberApsOption.APS_OPTION_FRAGMENT
        ),
        groupId=0x0201,  # fragment_count=2, fragment_index=1
        sequence=238,
    )

    with patch.object(prot_hndl, "_send_fragment_ack", new=AsyncMock()) as mock_ack:
        mock_ack.return_value = None
        caplog.set_level(logging.DEBUG)

        # Packet 1
        prot_hndl(packet1)
        assert len(prot_hndl._fragment_ack_tasks) == 1
        await asyncio.gather(
            *prot_hndl._fragment_ack_tasks
        )  # Ensure task completes and triggers callback
        assert len(prot_hndl._fragment_ack_tasks) == 0

        # Packet 2
        prot_hndl(packet2)
        assert len(prot_hndl._fragment_ack_tasks) == 1
        await asyncio.gather(
            *prot_hndl._fragment_ack_tasks
        )  # Ensure task completes and triggers callback
        assert len(prot_hndl._fragment_ack_tasks) == 0

        assert "Reassembled fragmented message, proceeding with handling" in caplog.text
        assert mock_ack.mock_calls == [
            call(0x1D6F, aps_frame_1, 2, 0),
            call(0x1D6F, aps_frame_2, 2, 1),
        ]


def test_incoming_message_broadcast(prot_hndl) -> None:
    """Test handling of incoming broadcast message."""
    handler = MagicMock()
    prot_hndl.on_event(PacketReceivedEvent.event_type, handler)

    aps_frame = t.EmberApsFrame(
        profileId=0x0104,
        clusterId=0x0006,
        sourceEndpoint=1,
        destinationEndpoint=2,
        options=t.EmberApsOption.APS_OPTION_NONE,
        groupId=0x0000,
        sequence=0x42,
    )

    # v4 field order: type, apsFrame, lqi, rssi, sender, bindingIndex, addressIndex, message
    prot_hndl.handle_parsed_callback(
        "incomingMessageHandler",
        [
            t.EmberIncomingMessageType.INCOMING_BROADCAST,
            aps_frame,
            200,  # lqi
            -40,  # rssi
            t.EmberNodeId(0x1234),  # sender
            0,  # binding_index
            0,  # address_index
            b"broadcast message",
        ],
    )

    assert handler.mock_calls == [
        call(
            PacketReceivedEvent(
                packet=zigpy.types.ZigbeePacket(
                    src=zigpy.types.AddrModeAddress(
                        addr_mode=zigpy.types.AddrMode.NWK,
                        address=zigpy.types.NWK(0x1234),
                    ),
                    src_ep=1,
                    dst=zigpy.types.AddrModeAddress(
                        addr_mode=zigpy.types.AddrMode.Broadcast,
                        address=zigpy.types.BroadcastAddress.ALL_ROUTERS_AND_COORDINATOR,
                    ),
                    dst_ep=2,
                    tsn=0x42,
                    profile_id=0x0104,
                    cluster_id=0x0006,
                    data=zigpy.types.SerializableBytes(b"broadcast message"),
                    lqi=200,
                    rssi=-40,
                )
            )
        )
    ]


def test_incoming_message_multicast(prot_hndl) -> None:
    """Test handling of incoming multicast message."""
    handler = MagicMock()
    prot_hndl.on_event(PacketReceivedEvent.event_type, handler)

    aps_frame = t.EmberApsFrame(
        profileId=0x0104,
        clusterId=0x0006,
        sourceEndpoint=1,
        destinationEndpoint=2,
        options=t.EmberApsOption.APS_OPTION_NONE,
        groupId=0x5678,
        sequence=0x42,
    )

    prot_hndl.handle_parsed_callback(
        "incomingMessageHandler",
        [
            t.EmberIncomingMessageType.INCOMING_MULTICAST,
            aps_frame,
            200,
            -40,
            t.EmberNodeId(0x1234),
            0,
            0,
            b"multicast message",
        ],
    )

    assert handler.mock_calls == [
        call(
            PacketReceivedEvent(
                packet=zigpy.types.ZigbeePacket(
                    src=zigpy.types.AddrModeAddress(
                        addr_mode=zigpy.types.AddrMode.NWK,
                        address=zigpy.types.NWK(0x1234),
                    ),
                    src_ep=1,
                    dst=zigpy.types.AddrModeAddress(
                        addr_mode=zigpy.types.AddrMode.Group,
                        address=0x5678,
                    ),
                    dst_ep=2,
                    tsn=0x42,
                    profile_id=0x0104,
                    cluster_id=0x0006,
                    data=zigpy.types.SerializableBytes(b"multicast message"),
                    lqi=200,
                    rssi=-40,
                )
            )
        )
    ]


def test_incoming_message_ignored_type(prot_hndl, caplog) -> None:
    """Test that unknown message types are ignored."""
    handler = MagicMock()
    prot_hndl.on_event(PacketReceivedEvent.event_type, handler)

    aps_frame = t.EmberApsFrame(
        profileId=0x0104,
        clusterId=0x0006,
        sourceEndpoint=1,
        destinationEndpoint=2,
        options=t.EmberApsOption.APS_OPTION_NONE,
        groupId=0x0000,
        sequence=0x42,
    )

    caplog.set_level(logging.DEBUG)
    prot_hndl.handle_parsed_callback(
        "incomingMessageHandler",
        [
            t.EmberIncomingMessageType.INCOMING_MANY_TO_ONE_ROUTE_REQUEST,
            aps_frame,
            200,
            -40,
            t.EmberNodeId(0x1234),
            0,
            0,
            b"ignored message",
        ],
    )

    # No event should be emitted for ignored message types
    assert len(handler.mock_calls) == 0
    assert "Ignoring message type" in caplog.text
