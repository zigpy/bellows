import asyncio
import functools
import logging
import sys

import pytest
import zigpy.config

from bellows import config, ezsp, uart
from bellows.exception import EzspError, InvalidCommandError
import bellows.ezsp.v4.types as v4_t
import bellows.types as t

if sys.version_info[:2] < (3, 11):
    from async_timeout import timeout as asyncio_timeout  # pragma: no cover
else:
    from asyncio import timeout as asyncio_timeout  # pragma: no cover

from unittest.mock import ANY, AsyncMock, MagicMock, call, patch, sentinel

DEVICE_CONFIG = {
    zigpy.config.CONF_DEVICE_PATH: "/dev/null",
    zigpy.config.CONF_DEVICE_BAUDRATE: 115200,
}


@pytest.fixture
async def ezsp_f():
    api = ezsp.EZSP(DEVICE_CONFIG)
    gw = MagicMock(spec_set=uart.Gateway)
    with patch("bellows.uart.connect", new=AsyncMock(return_value=gw)):
        await api.connect()
        yield api


async def make_ezsp(version=4) -> ezsp.EZSP:
    api = ezsp.EZSP(DEVICE_CONFIG)
    gw = MagicMock(spec_set=uart.Gateway)

    with patch("bellows.uart.connect", new=AsyncMock(return_value=gw)):
        await api.connect()

    assert api._ezsp_version == 4

    with patch.object(api, "_command", new=AsyncMock(return_value=[version, 0, 0])):
        await api.version()

    assert api._ezsp_version == version

    return api


async def test_connect(ezsp_f, monkeypatch):
    connected = False

    async def mockconnect(*args, **kwargs):
        nonlocal connected
        connected = True

    monkeypatch.setattr(uart, "connect", mockconnect)
    ezsp_f._gw = None

    await ezsp_f.connect()
    assert connected


async def test_reset(ezsp_f):
    ezsp_f.stop_ezsp = MagicMock()
    ezsp_f.start_ezsp = MagicMock()
    reset_mock = AsyncMock()
    ezsp_f._gw.reset = MagicMock(side_effect=reset_mock)

    await ezsp_f.reset()
    assert ezsp_f._gw.reset.call_count == 1
    assert ezsp_f.start_ezsp.call_count == 1
    assert ezsp_f.stop_ezsp.call_count == 1
    assert len(ezsp_f._callbacks) == 1


def test_close(ezsp_f):
    closed = False

    def close_mock(*args):
        nonlocal closed
        closed = True

    ezsp_f._gw.close = close_mock
    ezsp_f.close()
    assert closed is True
    assert ezsp_f._gw is None


def test_attr(ezsp_f):
    m = ezsp_f.getValue
    assert isinstance(m, functools.partial)
    assert callable(m)


async def test_non_existent_attr(ezsp_f):
    with pytest.raises(AttributeError):
        await ezsp_f.nonexistentMethod()


async def test_command(ezsp_f):
    ezsp_f.start_ezsp()
    with patch.object(ezsp_f._protocol, "command") as cmd_mock:
        await ezsp_f.nop()
    assert cmd_mock.call_count == 1


async def test_command_ezsp_stopped(ezsp_f):
    with pytest.raises(EzspError):
        await ezsp_f._command("version")


async def _test_list_command(ezsp_f, mockcommand):
    ezsp_f._command = mockcommand
    return await ezsp_f._list_command(
        "startScan", ["networkFoundHandler"], "scanCompleteHandler", 1
    )


async def test_list_command(ezsp_f):
    async def mockcommand(name, *args):
        assert name == "startScan"
        ezsp_f.frame_received(b"\x01\x00\x1b" + b"\x00" * 20)
        ezsp_f.frame_received(b"\x02\x00\x1b" + b"\x00" * 20)
        ezsp_f.frame_received(b"\x03\x00\x1c" + b"\x00" * 20)

        return [0]

    result = await _test_list_command(ezsp_f, mockcommand)
    assert len(result) == 2


async def test_list_command_initial_failure(ezsp_f):
    async def mockcommand(name, *args):
        assert name == "startScan"
        return [1]

    with pytest.raises(Exception):
        await _test_list_command(ezsp_f, mockcommand)


async def test_list_command_later_failure(ezsp_f):
    async def mockcommand(name, *args):
        assert name == "startScan"
        ezsp_f.frame_received(b"\x01\x00\x1b" + b"\x00" * 20)
        ezsp_f.frame_received(b"\x02\x00\x1b" + b"\x00" * 20)
        ezsp_f.frame_received(b"\x03\x00\x1c\x01\x01")

        return [0]

    with pytest.raises(Exception):
        await _test_list_command(ezsp_f, mockcommand)


async def _test_form_network(ezsp_f, initial_result, final_result):
    async def mockcommand(name, *args):
        assert name == "formNetwork"
        ezsp_f.frame_received(b"\x01\x00\x19" + final_result)
        return initial_result

    ezsp_f._command = mockcommand

    await ezsp_f.formNetwork(MagicMock())


async def test_form_network(ezsp_f):
    await _test_form_network(ezsp_f, [0], b"\x90")


async def test_form_network_fail(ezsp_f):
    with pytest.raises(Exception):
        await _test_form_network(ezsp_f, [1], b"\x90")


async def test_form_network_fail_stack_status(ezsp_f):
    with pytest.raises(Exception):
        await _test_form_network(ezsp_f, [0], b"\x00")


def test_receive_new(ezsp_f):
    callback = MagicMock()
    ezsp_f.add_callback(callback)
    ezsp_f.frame_received(b"\x00\xff\x00\x04\x05\x06")
    assert callback.call_count == 1


def test_callback(ezsp_f):
    testcb = MagicMock()

    cbid = ezsp_f.add_callback(testcb)
    ezsp_f.handle_callback(1, 2, 3)

    assert testcb.call_count == 1

    ezsp_f.remove_callback(cbid)
    ezsp_f.handle_callback(4, 5, 6)
    assert testcb.call_count == 1


def test_callback_multi(ezsp_f):
    testcb = MagicMock()

    cbid1 = ezsp_f.add_callback(testcb)
    ezsp_f.add_callback(testcb)

    ezsp_f.handle_callback(1, 2, 3)

    assert testcb.call_count == 2

    ezsp_f.remove_callback(cbid1)

    ezsp_f.handle_callback(4, 5, 6)
    testcb.assert_has_calls([call(1, 2, 3), call(1, 2, 3), call(4, 5, 6)])


def test_callback_exc(ezsp_f):
    testcb = MagicMock()
    testcb.side_effect = Exception("Testing")

    ezsp_f.add_callback(testcb)
    ezsp_f.handle_callback(1)
    assert testcb.call_count == 1


@pytest.mark.parametrize("version, call_count", ((4, 1), (5, 2), (6, 2), (99, 2)))
async def test_change_version(ezsp_f, version, call_count):
    def mockcommand(name, *args):
        assert name == "version"
        ezsp_f.frame_received(b"\x01\x00\x00\x21\x22\x23\x24")
        fut = asyncio.Future()
        fut.set_result([version, 2, 2046])
        return fut

    ezsp_f._command = MagicMock(side_effect=mockcommand)
    await ezsp_f.version()
    assert ezsp_f.ezsp_version == version
    assert ezsp_f._command.call_count == call_count


def test_stop_ezsp(ezsp_f):
    ezsp_f._ezsp_event.set()
    ezsp_f.stop_ezsp()
    assert ezsp_f._ezsp_event.is_set() is False


def test_start_ezsp(ezsp_f):
    ezsp_f._ezsp_event.clear()
    ezsp_f.start_ezsp()
    assert ezsp_f._ezsp_event.is_set() is True


def test_connection_lost(ezsp_f):
    ezsp_f.enter_failed_state = MagicMock(spec_set=ezsp_f.enter_failed_state)
    ezsp_f.connection_lost(sentinel.exc)
    assert ezsp_f.enter_failed_state.call_count == 1


async def test_enter_failed_state(ezsp_f):
    ezsp_f.stop_ezsp = MagicMock(spec_set=ezsp_f.stop_ezsp)
    cb = MagicMock(spec_set=ezsp_f.handle_callback)
    ezsp_f.add_callback(cb)
    ezsp_f.enter_failed_state(sentinel.error)
    await asyncio.sleep(0)
    assert ezsp_f.stop_ezsp.call_count == 1
    assert cb.call_count == 1
    assert cb.call_args[0][1][0] == sentinel.error


async def test_no_close_without_callback(ezsp_f):
    ezsp_f.stop_ezsp = MagicMock(spec_set=ezsp_f.stop_ezsp)
    ezsp_f.close = MagicMock(spec_set=ezsp_f.close)
    ezsp_f.enter_failed_state(sentinel.error)
    await asyncio.sleep(0)
    assert ezsp_f.stop_ezsp.call_count == 0
    assert ezsp_f.close.call_count == 0


@patch.object(ezsp.EZSP, "version", new_callable=AsyncMock)
@patch.object(ezsp.EZSP, "reset", new_callable=AsyncMock)
@patch("bellows.uart.connect", return_value=MagicMock(spec_set=uart.Gateway))
async def test_ezsp_init(conn_mock, reset_mock, version_mock):
    """Test initialize method."""
    zigpy_config = config.CONFIG_SCHEMA({"device": DEVICE_CONFIG})
    await ezsp.EZSP.initialize(zigpy_config)
    assert conn_mock.await_count == 1
    assert reset_mock.await_count == 1
    assert version_mock.await_count == 1


@patch.object(ezsp.EZSP, "version", side_effect=RuntimeError("Uh oh"))
@patch.object(ezsp.EZSP, "reset", new_callable=AsyncMock)
@patch.object(ezsp.EZSP, "close", new_callable=MagicMock)
@patch("bellows.uart.connect", return_value=MagicMock(spec_set=uart.Gateway))
async def test_ezsp_init_failure(conn_mock, close_mock, reset_mock, version_mock):
    """Test initialize method failing."""
    zigpy_config = config.CONFIG_SCHEMA({"device": DEVICE_CONFIG})

    with pytest.raises(RuntimeError):
        await ezsp.EZSP.initialize(zigpy_config)

    assert conn_mock.await_count == 1
    assert reset_mock.await_count == 1
    assert version_mock.await_count == 1
    assert close_mock.call_count == 1


async def test_ezsp_newer_version(ezsp_f):
    """Test newer version of ezsp."""
    with patch.object(
        ezsp_f, "_command", new=AsyncMock(return_value=(9, 0x12, 0x12345))
    ):
        await ezsp_f.version()


async def test_board_info(ezsp_f):
    """Test getting board info."""

    def cmd_mock(config):
        async def replacement(*args):
            return tuple(config[args])

        return replacement

    with patch.object(
        ezsp_f,
        "_command",
        new=cmd_mock(
            {
                ("getMfgToken", t.EzspMfgTokenId.MFG_BOARD_NAME): (
                    b"\xfe\xff\xff\xff",
                ),
                ("getMfgToken", t.EzspMfgTokenId.MFG_STRING): (
                    b"Manufacturer\xff\xff\xff",
                ),
                ("getValue", ezsp_f.types.EzspValueId.VALUE_VERSION_INFO): (
                    0x00,
                    b"\x01\x02\x03\x04\x05\x06",
                ),
            }
        ),
    ):
        mfg, brd, ver = await ezsp_f.get_board_info()

    assert mfg == "Manufacturer"
    assert brd == "0xFE"
    assert ver == "3.4.5.6 build 513"

    with patch.object(
        ezsp_f,
        "_command",
        new=cmd_mock(
            {
                ("getMfgToken", t.EzspMfgTokenId.MFG_BOARD_NAME): (
                    b"\xfe\xff\xff\xff",
                ),
                ("getMfgToken", t.EzspMfgTokenId.MFG_STRING): (
                    b"Manufacturer\xff\xff\xff",
                ),
                ("getValue", ezsp_f.types.EzspValueId.VALUE_VERSION_INFO): (
                    0x01,
                    b"\x01\x02\x03\x04\x05\x06",
                ),
            }
        ),
    ):
        mfg, brd, ver = await ezsp_f.get_board_info()

    assert mfg == "Manufacturer"
    assert brd == "0xFE"
    assert ver is None

    with patch.object(
        ezsp_f,
        "_command",
        new=cmd_mock(
            {
                ("getMfgToken", t.EzspMfgTokenId.MFG_BOARD_NAME): (
                    b"SkyBlue v0.1\x00\xff\xff\xff",
                ),
                ("getMfgToken", t.EzspMfgTokenId.MFG_STRING): (
                    b"Nabu Casa\x00\xff\xff\xff\xff\xff\xff",
                ),
                ("getValue", ezsp_f.types.EzspValueId.VALUE_VERSION_INFO): (
                    0x00,
                    b"\xbf\x00\x07\x01\x00\x00\xaa",
                ),
            }
        ),
    ):
        mfg, brd, ver = await ezsp_f.get_board_info()

    assert mfg == "Nabu Casa"
    assert brd == "SkyBlue v0.1"
    assert ver == "7.1.0.0 build 191"

    with patch.object(
        ezsp_f,
        "_command",
        new=cmd_mock(
            {
                ("getMfgToken", t.EzspMfgTokenId.MFG_BOARD_NAME): (b"\xff" * 16,),
                ("getMfgToken", t.EzspMfgTokenId.MFG_STRING): (b"\xff" * 16,),
                ("getValue", ezsp_f.types.EzspValueId.VALUE_VERSION_INFO): (
                    0x00,
                    b"\xbf\x00\x07\x01\x00\x00\xaa",
                ),
            }
        ),
    ):
        mfg, brd, ver = await ezsp_f.get_board_info()

    assert mfg is None
    assert brd is None
    assert ver == "7.1.0.0 build 191"


async def test_pre_permit(ezsp_f):
    with patch("bellows.ezsp.v4.EZSPv4.pre_permit") as pre_mock:
        await ezsp_f.pre_permit(sentinel.time)
        assert pre_mock.call_count == 1
        assert pre_mock.await_count == 1


async def test_update_policies(ezsp_f):
    with patch("bellows.ezsp.v4.EZSPv4.update_policies") as pol_mock:
        await ezsp_f.update_policies(sentinel.time)
        assert pol_mock.call_count == 1
        assert pol_mock.await_count == 1


async def test_set_source_routing_set_concentrator(ezsp_f):
    """Test enabling source routing."""
    with patch.object(ezsp_f, "setConcentrator", new=AsyncMock()) as cnc_mock:
        cnc_mock.return_value = (ezsp_f.types.EmberStatus.SUCCESS,)
        await ezsp_f.set_source_routing()
        assert cnc_mock.await_count == 1

        cnc_mock.return_value = (ezsp_f.types.EmberStatus.ERR_FATAL,)
        await ezsp_f.set_source_routing()
        assert cnc_mock.await_count == 2


async def test_set_source_routing_ezsp_v8(ezsp_f):
    """Test enabling source routing on EZSPv8."""

    ezsp_f._ezsp_version = 8
    ezsp_f.setConcentrator = AsyncMock(return_value=(ezsp_f.types.EmberStatus.SUCCESS,))
    ezsp_f.setSourceRouteDiscoveryMode = AsyncMock()

    await ezsp_f.set_source_routing()
    assert len(ezsp_f.setSourceRouteDiscoveryMode.mock_calls) == 1


async def test_leave_network_error(ezsp_f):
    """Test EZSP leaveNetwork command failure."""

    with patch.object(ezsp_f, "_command", new_callable=AsyncMock) as cmd_mock:
        cmd_mock.return_value = [t.EmberStatus.ERR_FATAL]
        with pytest.raises(EzspError):
            await ezsp_f.leaveNetwork(timeout=0.01)


async def test_leave_network_no_stack_status(ezsp_f):
    """Test EZSP leaveNetwork command, no stackStatusHandler callback."""

    with patch.object(ezsp_f, "_command", new_callable=AsyncMock) as cmd_mock:
        cmd_mock.return_value = [t.EmberStatus.SUCCESS]
        with pytest.raises(asyncio.TimeoutError):
            await ezsp_f.leaveNetwork(timeout=0.01)


async def test_leave_network(ezsp_f):
    """Test EZSP leaveNetwork command."""

    async def _mock_cmd(*args, **kwargs):
        ezsp_f.handle_callback("stackStatusHandler", [t.EmberStatus.NETWORK_UP])
        ezsp_f.handle_callback("stackStatusHandler", [t.EmberStatus.NETWORK_UP])
        ezsp_f.handle_callback("stackStatusHandler", [t.EmberStatus.NETWORK_DOWN])
        return [t.EmberStatus.SUCCESS]

    with patch.object(ezsp_f, "_command", new_callable=AsyncMock) as cmd_mock:
        cmd_mock.side_effect = _mock_cmd
        await ezsp_f.leaveNetwork(timeout=0.01)


@pytest.mark.parametrize(
    "value, expected_result",
    [
        (b"\xFF" * 8, True),
        (bytes.fromhex("0846b8a11c004b1200"), False),
        (b"", False),
    ],
)
async def test_can_burn_userdata_custom_eui64(ezsp_f, value, expected_result):
    """Test detecting if a custom EUI64 has been written."""
    ezsp_f.getMfgToken = AsyncMock(return_value=[value])

    assert await ezsp_f.can_burn_userdata_custom_eui64() == expected_result

    ezsp_f.getMfgToken.assert_called_once_with(t.EzspMfgTokenId.MFG_CUSTOM_EUI_64)


@pytest.mark.parametrize(
    "tokens, expected_key, expected_result",
    [
        ({}, None, False),
        (
            {t.NV3KeyId.CREATOR_STACK_RESTORED_EUI64: b"\xAA" * 8},
            t.NV3KeyId.CREATOR_STACK_RESTORED_EUI64,
            True,
        ),
        (
            {t.NV3KeyId.NVM3KEY_STACK_RESTORED_EUI64: b"\xAA" * 8},
            t.NV3KeyId.NVM3KEY_STACK_RESTORED_EUI64,
            True,
        ),
    ],
)
async def test_can_rewrite_custom_eui64(ezsp_f, tokens, expected_key, expected_result):
    """Test detecting if a custom EUI64 can be rewritten in NV3."""

    def get_token_data(key, index):
        if key not in tokens or index != 0:
            return [t.EmberStatus.ERR_FATAL, b""]

        return [t.EmberStatus.SUCCESS, tokens[key]]

    ezsp_f.getTokenData = AsyncMock(side_effect=get_token_data)

    key = await ezsp_f._get_nv3_restored_eui64_key()
    assert key == expected_key
    assert await ezsp_f.can_rewrite_custom_eui64() == expected_result


async def test_can_rewrite_custom_eui64_old_ezsp(ezsp_f):
    """Test detecting if a custom EUI64 can be rewritten in NV3, but with old EZSP."""

    assert await ezsp_f._get_nv3_restored_eui64_key() is None
    assert not await ezsp_f.can_rewrite_custom_eui64()


async def test_write_custom_eui64(ezsp_f):
    """Test writing a custom EUI64."""

    old_eui64 = t.EUI64.convert("AA" * 8)
    new_eui64 = t.EUI64.convert("BB" * 8)

    ezsp_f.getEui64 = AsyncMock(return_value=[old_eui64])
    ezsp_f.setMfgToken = AsyncMock(return_value=[t.EmberStatus.SUCCESS])
    ezsp_f.setTokenData = AsyncMock(return_value=[t.EmberStatus.SUCCESS])
    ezsp_f._get_mfg_custom_eui_64 = AsyncMock(return_value=old_eui64)
    ezsp_f._get_nv3_restored_eui64_key = AsyncMock(return_value=None)

    # Nothing is done when the EUI64 write is a no-op
    await ezsp_f.write_custom_eui64(old_eui64)

    ezsp_f.setMfgToken.assert_not_called()
    ezsp_f.setTokenData.assert_not_called()

    # If NV3 exists, all writes succeed
    ezsp_f._get_nv3_restored_eui64_key.return_value = (
        t.NV3KeyId.NVM3KEY_STACK_RESTORED_EUI64
    )
    await ezsp_f.write_custom_eui64(new_eui64)
    await ezsp_f.write_custom_eui64(new_eui64, burn_into_userdata=True)

    ezsp_f.setMfgToken.assert_not_called()
    ezsp_f.setTokenData.mock_calls == 2 * [
        call(
            t.NV3KeyId.NVM3KEY_STACK_RESTORED_EUI64,
            0,
            new_eui64.serialize(),
        )
    ]

    ezsp_f.setTokenData.reset_mock()

    # If NV3 does not and the MFG token does not, we conditionally write
    ezsp_f._get_mfg_custom_eui_64.return_value = None
    ezsp_f._get_nv3_restored_eui64_key.return_value = None

    with pytest.raises(EzspError):
        await ezsp_f.write_custom_eui64(new_eui64)

    # Burn kwarg not passed, so nothing is done
    ezsp_f.setMfgToken.assert_not_called()
    ezsp_f.setTokenData.assert_not_called()

    await ezsp_f.write_custom_eui64(new_eui64, burn_into_userdata=True)

    ezsp_f.setMfgToken.assert_called_once_with(
        t.EzspMfgTokenId.MFG_CUSTOM_EUI_64, new_eui64.serialize()
    )
    ezsp_f.setTokenData.assert_not_called()

    ezsp_f.setMfgToken.reset_mock()

    # If no method is viable, throw an error
    ezsp_f._get_mfg_custom_eui_64.return_value = old_eui64

    with pytest.raises(EzspError):
        await ezsp_f.write_custom_eui64(new_eui64)

    with pytest.raises(EzspError):
        await ezsp_f.write_custom_eui64(new_eui64, burn_into_userdata=True)

    ezsp_f.setMfgToken.assert_not_called()
    ezsp_f.setTokenData.assert_not_called()


async def test_write_custom_eui64_rcp(ezsp_f):
    """Test writing a custom EUI64 with RPC firmware."""

    old_eui64 = t.EUI64.convert("AA" * 8)
    new_eui64 = t.EUI64.convert("BB" * 8)

    ezsp_f.getEui64 = AsyncMock(return_value=[old_eui64])
    ezsp_f.setMfgToken = AsyncMock(return_value=[t.EmberStatus.INVALID_CALL])
    ezsp_f.setTokenData = AsyncMock(return_value=[t.EmberStatus.SUCCESS])

    # RCP firmware does not support manufacturing tokens
    ezsp_f.getMfgToken = AsyncMock(return_value=[b""])
    ezsp_f.getTokenData = AsyncMock(return_value=[t.EmberStatus.SUCCESS, b"\xFF" * 8])

    await ezsp_f.write_custom_eui64(new_eui64)

    ezsp_f.setMfgToken.assert_not_called()
    ezsp_f.setTokenData.mock_calls == [
        call(
            t.NV3KeyId.NVM3KEY_STACK_RESTORED_EUI64,
            0,
            new_eui64.serialize(),
        )
    ]


@patch.object(ezsp.EZSP, "version", new_callable=AsyncMock)
@patch.object(ezsp.EZSP, "reset", new_callable=AsyncMock)
@patch("bellows.uart.connect", return_value=MagicMock(spec_set=uart.Gateway))
async def test_ezsp_init_zigbeed(conn_mock, reset_mock, version_mock):
    """Test initialize method with a received startup reset frame."""
    zigpy_config = config.CONFIG_SCHEMA(
        {
            "device": {
                **DEVICE_CONFIG,
                zigpy.config.CONF_DEVICE_PATH: "socket://localhost:1234",
            }
        }
    )

    gw_wait_reset_mock = conn_mock.return_value.wait_for_startup_reset = AsyncMock()

    await ezsp.EZSP.initialize(zigpy_config)

    assert conn_mock.await_count == 1
    assert reset_mock.await_count == 0  # Reset is not called
    assert gw_wait_reset_mock.await_count == 1
    assert version_mock.await_count == 1


@patch.object(ezsp.EZSP, "version", new_callable=AsyncMock)
@patch.object(ezsp.EZSP, "reset", new_callable=AsyncMock)
@patch("bellows.uart.connect", return_value=MagicMock(spec_set=uart.Gateway))
@patch("bellows.ezsp.NETWORK_COORDINATOR_STARTUP_RESET_WAIT", 0.01)
async def test_ezsp_init_zigbeed_timeout(conn_mock, reset_mock, version_mock):
    """Test initialize method with a received startup reset frame."""
    zigpy_config = config.CONFIG_SCHEMA(
        {
            "device": {
                **DEVICE_CONFIG,
                zigpy.config.CONF_DEVICE_PATH: "socket://localhost:1234",
            }
        }
    )

    async def wait_forever(*args, **kwargs):
        return await asyncio.get_running_loop().create_future()

    gw_wait_reset_mock = conn_mock.return_value.wait_for_startup_reset = AsyncMock(
        side_effect=wait_forever
    )

    await ezsp.EZSP.initialize(zigpy_config)

    assert conn_mock.await_count == 1
    assert reset_mock.await_count == 1  # Reset will be called
    assert gw_wait_reset_mock.await_count == 1
    assert version_mock.await_count == 1


async def test_wait_for_stack_status(ezsp_f):
    assert not ezsp_f._stack_status_listeners[t.EmberStatus.NETWORK_DOWN]

    # Cancellation clears handlers
    with ezsp_f.wait_for_stack_status(t.EmberStatus.NETWORK_DOWN) as stack_status:
        with pytest.raises(asyncio.TimeoutError):
            async with asyncio_timeout(0.1):
                assert ezsp_f._stack_status_listeners[t.EmberStatus.NETWORK_DOWN]
                await stack_status

    assert not ezsp_f._stack_status_listeners[t.EmberStatus.NETWORK_DOWN]

    # Receiving multiple also works
    with ezsp_f.wait_for_stack_status(t.EmberStatus.NETWORK_DOWN) as stack_status:
        ezsp_f.handle_callback("stackStatusHandler", [t.EmberStatus.NETWORK_UP])
        ezsp_f.handle_callback("stackStatusHandler", [t.EmberStatus.NETWORK_DOWN])
        ezsp_f.handle_callback("stackStatusHandler", [t.EmberStatus.NETWORK_DOWN])

        await stack_status

    assert not ezsp_f._stack_status_listeners[t.EmberStatus.NETWORK_DOWN]


def test_ezsp_versions(ezsp_f):
    for version in range(4, ezsp.EZSP_LATEST + 1):
        assert version in ezsp_f._BY_VERSION
        assert ezsp_f._BY_VERSION[version].__name__ == f"EZSPv{version}"
        assert ezsp_f._BY_VERSION[version].VERSION == version


async def test_config_initialize_husbzb1(ezsp_f):
    """Test timeouts are properly set for HUSBZB-1."""

    ezsp_f._ezsp_version = 4

    ezsp_f.getConfigurationValue = AsyncMock(return_value=(t.EzspStatus.SUCCESS, 0))
    ezsp_f.setConfigurationValue = AsyncMock(return_value=(t.EzspStatus.SUCCESS,))
    ezsp_f.networkState = AsyncMock(return_value=(t.EmberNetworkStatus.JOINED_NETWORK,))

    expected_calls = [
        call(v4_t.EzspConfigId.CONFIG_SOURCE_ROUTE_TABLE_SIZE, 16),
        call(v4_t.EzspConfigId.CONFIG_END_DEVICE_POLL_TIMEOUT, 60),
        call(v4_t.EzspConfigId.CONFIG_END_DEVICE_POLL_TIMEOUT_SHIFT, 8),
        call(v4_t.EzspConfigId.CONFIG_INDIRECT_TRANSMISSION_TIMEOUT, 7680),
        call(v4_t.EzspConfigId.CONFIG_STACK_PROFILE, 2),
        call(v4_t.EzspConfigId.CONFIG_SUPPORTED_NETWORKS, 1),
        call(v4_t.EzspConfigId.CONFIG_MULTICAST_TABLE_SIZE, 16),
        call(v4_t.EzspConfigId.CONFIG_TRUST_CENTER_ADDRESS_CACHE_SIZE, 2),
        call(v4_t.EzspConfigId.CONFIG_SECURITY_LEVEL, 5),
        call(v4_t.EzspConfigId.CONFIG_ADDRESS_TABLE_SIZE, 16),
        call(v4_t.EzspConfigId.CONFIG_PAN_ID_CONFLICT_REPORT_THRESHOLD, 2),
        call(v4_t.EzspConfigId.CONFIG_KEY_TABLE_SIZE, 4),
        call(v4_t.EzspConfigId.CONFIG_MAX_END_DEVICE_CHILDREN, 32),
        call(
            v4_t.EzspConfigId.CONFIG_APPLICATION_ZDO_FLAGS,
            (
                v4_t.EmberZdoConfigurationFlags.APP_HANDLES_UNSUPPORTED_ZDO_REQUESTS
                | v4_t.EmberZdoConfigurationFlags.APP_RECEIVES_SUPPORTED_ZDO_REQUESTS
            ),
        ),
        call(v4_t.EzspConfigId.CONFIG_PACKET_BUFFER_COUNT, 255),
    ]

    await ezsp_f.write_config({})
    assert ezsp_f.setConfigurationValue.mock_calls == expected_calls


@pytest.mark.parametrize("version", ezsp.EZSP._BY_VERSION)
async def test_config_initialize(version: int, ezsp_f, caplog):
    """Test config initialization for all protocol versions."""

    assert ezsp_f.ezsp_version == 4

    with patch.object(ezsp_f, "_command", AsyncMock(return_value=[version, 2, 2046])):
        await ezsp_f.version()

    assert ezsp_f.ezsp_version == version

    ezsp_f.getConfigurationValue = AsyncMock(return_value=(t.EzspStatus.SUCCESS, 0))
    ezsp_f.setConfigurationValue = AsyncMock(return_value=(t.EzspStatus.SUCCESS,))
    ezsp_f.networkState = AsyncMock(return_value=(t.EmberNetworkStatus.JOINED_NETWORK,))

    ezsp_f.setValue = AsyncMock(return_value=(t.EzspStatus.SUCCESS,))
    ezsp_f.getValue = AsyncMock(return_value=(t.EzspStatus.SUCCESS, b"\xFF"))

    await ezsp_f.write_config({})

    with caplog.at_level(logging.DEBUG):
        ezsp_f.setConfigurationValue.return_value = (t.EzspStatus.ERROR_OUT_OF_MEMORY,)
        await ezsp_f.write_config({})

    assert "Could not set config" in caplog.text
    ezsp_f.setConfigurationValue.return_value = (t.EzspStatus.SUCCESS,)
    caplog.clear()

    # EZSPv6 does not set any values on startup
    if version < 7:
        return

    ezsp_f.setValue.reset_mock()
    ezsp_f.getValue.return_value = (t.EzspStatus.ERROR_INVALID_ID, b"")
    await ezsp_f.write_config({})
    assert len(ezsp_f.setValue.mock_calls) == 1

    ezsp_f.getValue = AsyncMock(return_value=(t.EzspStatus.SUCCESS, b"\xFF"))
    caplog.clear()

    with caplog.at_level(logging.DEBUG):
        ezsp_f.setValue.return_value = (t.EzspStatus.ERROR_INVALID_ID,)
        await ezsp_f.write_config({})

    assert "Could not set value" in caplog.text
    ezsp_f.setValue.return_value = (t.EzspStatus.SUCCESS,)
    caplog.clear()


async def test_cfg_initialize_skip(ezsp_f):
    """Test initialization."""

    ezsp_f.networkState = AsyncMock(return_value=(t.EmberNetworkStatus.JOINED_NETWORK,))

    p1 = patch.object(
        ezsp_f,
        "setConfigurationValue",
        new=AsyncMock(return_value=(t.EzspStatus.SUCCESS,)),
    )
    p2 = patch.object(
        ezsp_f,
        "getConfigurationValue",
        new=AsyncMock(return_value=(t.EzspStatus.SUCCESS, 22)),
    )
    with p1, p2:
        await ezsp_f.write_config({"CONFIG_END_DEVICE_POLL_TIMEOUT": None})

        # Config not set when it is explicitly disabled
        with pytest.raises(AssertionError):
            ezsp_f.setConfigurationValue.assert_called_with(
                v4_t.EzspConfigId.CONFIG_END_DEVICE_POLL_TIMEOUT, ANY
            )

    with p1, p2:
        await ezsp_f.write_config({"CONFIG_MULTICAST_TABLE_SIZE": 123})

        # Config is overridden
        ezsp_f.setConfigurationValue.assert_any_call(
            v4_t.EzspConfigId.CONFIG_MULTICAST_TABLE_SIZE, 123
        )

    with p1, p2:
        await ezsp_f.write_config({})

        # Config is set by default
        ezsp_f.setConfigurationValue.assert_any_call(
            v4_t.EzspConfigId.CONFIG_END_DEVICE_POLL_TIMEOUT, ANY
        )


async def test_reset_custom_eui64(ezsp_f):
    """Test resetting custom EUI64."""
    # No NV3 interface
    ezsp_f.getTokenData = AsyncMock(side_effect=InvalidCommandError)
    ezsp_f.setTokenData = AsyncMock(return_value=[t.EmberStatus.SUCCESS])
    await ezsp_f.reset_custom_eui64()

    assert len(ezsp_f.setTokenData.mock_calls) == 0

    # With NV3 interface
    ezsp_f.getTokenData = AsyncMock(return_value=[t.EmberStatus.SUCCESS, b"\xAB" * 8])
    await ezsp_f.reset_custom_eui64()
    assert ezsp_f.setTokenData.mock_calls == [
        call(t.NV3KeyId.CREATOR_STACK_RESTORED_EUI64, 0, t.LVBytes32(b"\xFF" * 8))
    ]


def test_empty_frame_received(ezsp_f):
    """Test dropping of invalid, empty frames."""
    ezsp_f._protocol = MagicMock(spec_set=ezsp_f._protocol)
    ezsp_f._protocol.__call__ = MagicMock()
    ezsp_f.frame_received(b"")

    assert ezsp_f._protocol.__call__.mock_calls == []
