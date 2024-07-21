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
