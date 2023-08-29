import asyncio
import logging

import pytest

from bellows.ezsp import EZSP
import bellows.ezsp.v4
import bellows.ezsp.v4.types as t

from .async_mock import ANY, AsyncMock, MagicMock, call, patch


@pytest.fixture
def prot_hndl():
    """Protocol handler mock."""
    return bellows.ezsp.v4.EZSPv4(MagicMock(), MagicMock())


async def test_command(prot_hndl):
    coro = prot_hndl.command("nop")
    asyncio.get_running_loop().call_soon(
        lambda: prot_hndl._awaiting[prot_hndl._seq - 1][2].set_result(True)
    )

    await coro
    assert prot_hndl._gw.data.call_count == 1


def test_receive_reply(prot_hndl):
    callback_mock = MagicMock(spec_set=asyncio.Future)
    prot_hndl._awaiting[0] = (0, prot_hndl.COMMANDS["version"][2], callback_mock)
    prot_hndl(b"\x00\xff\x00\x04\x05\x06")

    assert 0 not in prot_hndl._awaiting
    assert callback_mock.set_exception.call_count == 0
    assert callback_mock.set_result.call_count == 1
    callback_mock.set_result.assert_called_once_with([4, 5, 6])
    assert prot_hndl._handle_callback.call_count == 0


def test_receive_reply_after_timeout(prot_hndl):
    callback_mock = MagicMock(spec_set=asyncio.Future)
    callback_mock.set_result.side_effect = asyncio.InvalidStateError()
    prot_hndl._awaiting[0] = (0, prot_hndl.COMMANDS["version"][2], callback_mock)
    prot_hndl(b"\x00\xff\x00\x04\x05\x06")

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
