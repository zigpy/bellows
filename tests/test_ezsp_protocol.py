import asyncio
import logging

import pytest

import bellows.ezsp.v4
import bellows.ezsp.v4.types as t

from .async_mock import ANY, AsyncMock, MagicMock, call, patch


class _DummyProtocolHandler(bellows.ezsp.v4.EZSPv4):
    """Protocol handler mock."""

    @property
    def gw_mock(self):
        return self._gw

    @property
    def cb_mock(self):
        return self._handle_callback


@pytest.fixture
def prot_hndl():
    """Protocol handler mock."""
    return _DummyProtocolHandler(MagicMock(), MagicMock())


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
    assert prot_hndl.cb_mock.call_count == 0


def test_receive_reply_after_timeout(prot_hndl):
    callback_mock = MagicMock(spec_set=asyncio.Future)
    callback_mock.set_result.side_effect = asyncio.InvalidStateError()
    prot_hndl._awaiting[0] = (0, prot_hndl.COMMANDS["version"][2], callback_mock)
    prot_hndl(b"\x00\xff\x00\x04\x05\x06")

    assert 0 not in prot_hndl._awaiting
    assert callback_mock.set_exception.call_count == 0
    assert callback_mock.set_result.call_count == 1
    callback_mock.set_result.assert_called_once_with([4, 5, 6])
    assert prot_hndl.cb_mock.call_count == 0


def test_receive_reply_invalid_command(prot_hndl):
    callback_mock = MagicMock(spec_set=asyncio.Future)
    prot_hndl._awaiting[0] = (0, prot_hndl.COMMANDS["invalidCommand"][2], callback_mock)
    prot_hndl(b"\x00\xff\x58\x31")

    assert 0 not in prot_hndl._awaiting
    assert callback_mock.set_exception.call_count == 1
    assert callback_mock.set_result.call_count == 0
    assert prot_hndl.cb_mock.call_count == 0


async def test_cfg_initialize(prot_hndl, caplog):
    """Test initialization."""

    p1 = patch.object(prot_hndl, "setConfigurationValue", new=AsyncMock())
    p2 = patch.object(
        prot_hndl,
        "getConfigurationValue",
        new=AsyncMock(return_value=(t.EzspStatus.SUCCESS, 22)),
    )
    p3 = patch.object(prot_hndl, "get_free_buffers", new=AsyncMock(22))
    with p1 as cfg_mock, p2, p3:
        cfg_mock.return_value = (t.EzspStatus.SUCCESS,)
        await prot_hndl.initialize({"ezsp_config": {}, "source_routing": True})

        cfg_mock.return_value = (t.EzspStatus.ERROR_OUT_OF_MEMORY,)
        with caplog.at_level(logging.WARNING):
            await prot_hndl.initialize({"ezsp_config": {}, "source_routing": False})
            assert "Couldn't set" in caplog.text


async def test_config_initialize_husbzb1(prot_hndl):
    """Test timeouts are properly set for HUSBZB-1."""

    prot_hndl.getConfigurationValue = AsyncMock(return_value=(t.EzspStatus.SUCCESS, 22))
    prot_hndl.setConfigurationValue = AsyncMock(return_value=(t.EzspStatus.SUCCESS,))

    await prot_hndl.initialize({"ezsp_config": {}})
    prot_hndl.setConfigurationValue.assert_has_calls(
        [
            call(t.EzspConfigId.CONFIG_END_DEVICE_POLL_TIMEOUT, 60),
            call(t.EzspConfigId.CONFIG_END_DEVICE_POLL_TIMEOUT_SHIFT, 8),
        ]
    )


async def test_cfg_initialize_skip(prot_hndl):
    """Test initialization."""

    p1 = patch.object(
        prot_hndl,
        "setConfigurationValue",
        new=AsyncMock(return_value=(t.EzspStatus.SUCCESS,)),
    )
    p2 = patch.object(
        prot_hndl,
        "getConfigurationValue",
        new=AsyncMock(return_value=(t.EzspStatus.SUCCESS, 22)),
    )
    p3 = patch.object(prot_hndl, "get_free_buffers", new=AsyncMock(22))
    with p1, p2, p3:
        await prot_hndl.initialize(
            {"ezsp_config": {"CONFIG_END_DEVICE_POLL_TIMEOUT": None}}
        )

        # Config not set when it is explicitly disabled
        with pytest.raises(AssertionError):
            prot_hndl.setConfigurationValue.assert_called_with(
                t.EzspConfigId.CONFIG_END_DEVICE_POLL_TIMEOUT, ANY
            )

    with p1, p2, p3:
        await prot_hndl.initialize(
            {"ezsp_config": {"CONFIG_MULTICAST_TABLE_SIZE": 123}}
        )

        # Config is overridden
        prot_hndl.setConfigurationValue.assert_any_call(
            t.EzspConfigId.CONFIG_MULTICAST_TABLE_SIZE, 123
        )

    with p1, p2, p3:
        await prot_hndl.initialize({"ezsp_config": {}})

        # Config is set by default
        prot_hndl.setConfigurationValue.assert_any_call(
            t.EzspConfigId.CONFIG_END_DEVICE_POLL_TIMEOUT, ANY
        )


async def test_update_policies(prot_hndl):
    """Test update_policies."""

    with patch.object(prot_hndl, "setPolicy", new=AsyncMock()) as pol_mock:
        pol_mock.return_value = (t.EzspStatus.SUCCESS,)
        await prot_hndl.update_policies({"ezsp_policies": {}})

        pol_mock.return_value = (t.EzspStatus.ERROR_OUT_OF_MEMORY,)
        with pytest.raises(AssertionError):
            await prot_hndl.update_policies({"ezsp_policies": {}})


@pytest.mark.parametrize(
    "status, raw, expected_value",
    (
        (t.EzspStatus.ERROR_OUT_OF_MEMORY, b"", None),
        (t.EzspStatus.ERROR_OUT_OF_MEMORY, b"\x02\x02", None),
        (t.EzspStatus.SUCCESS, b"\x02\x02", 514),
    ),
)
async def test_get_free_buffers(prot_hndl, status, raw, expected_value):
    """Test getting free buffers."""

    p1 = patch.object(prot_hndl, "getValue", new=AsyncMock())
    with p1 as value_mock:
        value_mock.return_value = (status, raw)
        free_buffers = await prot_hndl.get_free_buffers()
        if expected_value is None:
            assert free_buffers is expected_value
        else:
            assert free_buffers == expected_value


async def test_unknown_command(prot_hndl, caplog):
    """Test receiving an unknown command."""

    unregistered_command = 0x04

    with caplog.at_level(logging.WARNING):
        prot_hndl(bytes([0x00, 0x00, unregistered_command, 0xAB, 0xCD]))

        assert "0x0004 received: b'abcd' (b'000004abcd')" in caplog.text
