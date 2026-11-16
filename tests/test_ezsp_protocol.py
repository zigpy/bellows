import asyncio
import logging
from unittest.mock import AsyncMock, MagicMock, call, patch

import pytest

from bellows.ezsp import EZSP
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


async def test_command_timeout_includes_transport_send(prot_hndl):
    """A stuck transport must release the command semaphore and pending reply."""
    send_started = asyncio.Event()

    async def blocked_send(data):
        send_started.set()
        await asyncio.Event().wait()

    with (
        patch.object(prot_hndl._gw, "send_data", side_effect=blocked_send),
        patch("bellows.ezsp.protocol.EZSP_CMD_TIMEOUT", 0.01),
    ):
        # The outer bound makes the regression fail instead of hanging the suite.
        async with asyncio.timeout(1):
            task = asyncio.create_task(prot_hndl.command("nop"))
            await send_started.wait()
            with pytest.raises(TimeoutError):
                await task
    assert not prot_hndl._awaiting
    assert not prot_hndl._send_semaphore.locked()

    with patch.object(prot_hndl._gw, "send_data"):
        asyncio.get_running_loop().call_soon(
            lambda: prot_hndl._awaiting[prot_hndl._seq - 1][2].set_result(True)
        )
        assert await prot_hndl.command("nop") is True
    assert not prot_hndl._awaiting


@pytest.mark.parametrize("cancel", [False, True])
async def test_command_cleans_up_failed_transport(prot_hndl, cancel):
    """Send failures and caller cancellation must not retain pending replies."""
    send_started = asyncio.Event()

    async def send(data):
        send_started.set()
        if not cancel:
            raise RuntimeError("closed worker")
        await asyncio.Event().wait()

    with patch.object(prot_hndl._gw, "send_data", side_effect=send):
        task = asyncio.create_task(prot_hndl.command("nop"))
        await send_started.wait()
        future = next(iter(prot_hndl._awaiting.values()))[2] if cancel else None
        if cancel:
            task.cancel()
        with pytest.raises(asyncio.CancelledError if cancel else RuntimeError):
            await task
        if cancel:
            assert future.cancelled()
    assert not prot_hndl._awaiting
    assert not prot_hndl._send_semaphore.locked()


async def test_command_cleans_up_response_timeout(prot_hndl):
    """A response timeout must remove its pending-reply entry."""
    with (
        patch.object(prot_hndl._gw, "send_data"),
        patch("bellows.ezsp.protocol.EZSP_CMD_TIMEOUT", 0.01),
        pytest.raises(TimeoutError),
    ):
        await prot_hndl.command("nop")
    assert not prot_hndl._awaiting
    assert not prot_hndl._send_semaphore.locked()


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

        prot_hndl._handle_callback.assert_not_called()
        assert "Fragment reassembly not complete. waiting for more data." in caplog.text
        mock_ack.assert_called_once_with(sender, aps_frame, 2, 0)


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
    sender = 0x1D6F

    aps_frame_1 = t.EmberApsFrame(
        profileId=260,
        clusterId=65281,
        sourceEndpoint=2,
        destinationEndpoint=2,
        options=33088,  # Includes APS_OPTION_FRAGMENT
        groupId=512,  # fragment_count=2, fragment_index=0
        sequence=238,
    )
    aps_frame_2 = t.EmberApsFrame(
        profileId=260,
        clusterId=65281,
        sourceEndpoint=2,
        destinationEndpoint=2,
        options=33088,
        groupId=513,  # fragment_count=2, fragment_index=1
        sequence=238,
    )
    reassembled = b"complete message"

    with patch.object(prot_hndl, "_send_fragment_ack", new=AsyncMock()) as mock_ack:
        mock_ack.return_value = None
        caplog.set_level(logging.DEBUG)

        # Packet 1
        prot_hndl(packet1)
        assert len(prot_hndl._fragment_ack_tasks) == 1
        ack_task = next(iter(prot_hndl._fragment_ack_tasks))
        await asyncio.gather(ack_task)  # Ensure task completes and triggers callback
        assert (
            len(prot_hndl._fragment_ack_tasks) == 0
        ), "Done callback should have removed task"

        prot_hndl._handle_callback.assert_not_called()
        assert (
            "Reassembled fragmented message. Proceeding with normal handling."
            not in caplog.text
        )
        mock_ack.assert_called_with(sender, aps_frame_1, 2, 0)

        # Packet 2
        prot_hndl(packet2)
        assert len(prot_hndl._fragment_ack_tasks) == 1
        ack_task = next(iter(prot_hndl._fragment_ack_tasks))
        await asyncio.gather(ack_task)  # Ensure task completes and triggers callback
        assert (
            len(prot_hndl._fragment_ack_tasks) == 0
        ), "Done callback should have removed task"

        prot_hndl._handle_callback.assert_called_once_with(
            "incomingMessageHandler",
            [
                t.EmberIncomingMessageType.INCOMING_UNICAST,  # 0x00
                aps_frame_2,  # Parsed APS frame
                255,  # lastHopLqi: 0xFF
                -8,  # lastHopRssi: 0xF8
                sender,  # 0x1D6F
                255,  # bindingIndex: 0xFF
                255,  # addressIndex: 0xFF
                reassembled,  # Reassembled payload
            ],
        )
        assert (
            "Reassembled fragmented message. Proceeding with normal handling."
            in caplog.text
        )
        mock_ack.assert_called_with(sender, aps_frame_2, 2, 1)
