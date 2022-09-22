import asyncio
import functools

import pytest
import serial

from bellows import config, ezsp, uart
from bellows.exception import EzspError
import bellows.ezsp.v4.types as t

from .async_mock import AsyncMock, MagicMock, call, patch, sentinel

DEVICE_CONFIG = {
    config.CONF_DEVICE_PATH: "/dev/null",
    config.CONF_DEVICE_BAUDRATE: 115200,
}


@pytest.fixture
async def ezsp_f():
    api = ezsp.EZSP(DEVICE_CONFIG)
    gw = MagicMock(spec_set=uart.Gateway)
    with patch("bellows.uart.connect", new=AsyncMock(return_value=gw)):
        await api.connect()
        yield api


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
    assert len(ezsp_f._callbacks) == 0


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


def test_non_existent_attr(ezsp_f):
    with pytest.raises(AttributeError):
        ezsp_f.nonexistentMethod()


def test_command(ezsp_f):
    ezsp_f.start_ezsp()
    with patch.object(ezsp_f._protocol, "command") as cmd_mock:
        ezsp_f.nop()
    assert cmd_mock.call_count == 1


def test_command_ezsp_stopped(ezsp_f):
    with pytest.raises(EzspError):
        ezsp_f._command("version")


def _test_list_command(ezsp_f, mockcommand):
    loop = asyncio.get_event_loop()
    ezsp_f._command = mockcommand
    return loop.run_until_complete(
        ezsp_f._list_command(
            "startScan", ["networkFoundHandler"], "scanCompleteHandler", 1
        )
    )


def test_list_command(ezsp_f):
    async def mockcommand(name, *args):
        assert name == "startScan"
        ezsp_f.frame_received(b"\x01\x00\x1b" + b"\x00" * 20)
        ezsp_f.frame_received(b"\x02\x00\x1b" + b"\x00" * 20)
        ezsp_f.frame_received(b"\x03\x00\x1c" + b"\x00" * 20)

        return [0]

    result = _test_list_command(ezsp_f, mockcommand)
    assert len(result) == 2


def test_list_command_initial_failure(ezsp_f):
    async def mockcommand(name, *args):
        assert name == "startScan"
        return [1]

    with pytest.raises(Exception):
        _test_list_command(ezsp_f, mockcommand)


def test_list_command_later_failure(ezsp_f):
    async def mockcommand(name, *args):
        assert name == "startScan"
        ezsp_f.frame_received(b"\x01\x00\x1b" + b"\x00" * 20)
        ezsp_f.frame_received(b"\x02\x00\x1b" + b"\x00" * 20)
        ezsp_f.frame_received(b"\x03\x00\x1c\x01\x01")

        return [0]

    with pytest.raises(Exception):
        _test_list_command(ezsp_f, mockcommand)


def _test_form_network(ezsp_f, initial_result, final_result):
    async def mockcommand(name, *args):
        assert name == "formNetwork"
        ezsp_f.frame_received(b"\x01\x00\x19" + final_result)
        return initial_result

    ezsp_f._command = mockcommand

    loop = asyncio.get_event_loop()
    return loop.run_until_complete(ezsp_f.formNetwork(MagicMock()))


def test_form_network(ezsp_f):
    _test_form_network(ezsp_f, [0], b"\x90")


def test_form_network_fail(ezsp_f):
    with pytest.raises(Exception):
        _test_form_network(ezsp_f, [1], b"\x90")


def test_form_network_fail_stack_status(ezsp_f):
    with pytest.raises(Exception):
        _test_form_network(ezsp_f, [0], b"\x00")


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


@pytest.mark.parametrize("version, call_count", ((4, 1), (5, 2), (6, 2)))
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


@patch("bellows.uart.connect", return_value=MagicMock(spec_set=uart.Gateway))
async def test_probe_success(mock_connect):
    """Test device probing."""

    # Probe works with default baud
    with patch(
        "bellows.ezsp.protocol.ProtocolHandler.command",
        AsyncMock(return_value=(4, 0, 0)),
    ):
        res = await ezsp.EZSP.probe(DEVICE_CONFIG)

    assert type(res) is dict
    assert mock_connect.call_count == 1
    assert mock_connect.await_count == 1
    assert mock_connect.return_value.close.call_count == 1
    mock_connect.reset_mock()

    # Probe first fails with default baud but then works with alternate baud
    with patch(
        "bellows.ezsp.protocol.ProtocolHandler.command",
        AsyncMock(side_effect=[asyncio.TimeoutError(), (4, 0, 0)]),
    ):
        res = await ezsp.EZSP.probe(DEVICE_CONFIG)

    assert type(res) is dict
    assert mock_connect.call_count == 2
    assert mock_connect.await_count == 2
    assert mock_connect.return_value.close.call_count == 2


@pytest.mark.parametrize(
    "exception", (asyncio.TimeoutError, serial.SerialException, EzspError, RuntimeError)
)
async def test_probe_fail(exception):
    """Test device probing fails."""

    p1 = patch.object(ezsp.EZSP, "version", new_callable=AsyncMock)
    p2 = patch("bellows.uart.connect", return_value=MagicMock(spec_set=uart.Gateway))

    with p1 as mock_version, p2 as mock_connect:
        mock_version.side_effect = exception
        res = await ezsp.EZSP.probe(DEVICE_CONFIG)

    assert res is False
    assert mock_connect.call_count == 2
    assert mock_connect.await_count == 2
    assert mock_version.call_count == 2
    assert mock_connect.return_value.close.call_count == 2


@patch.object(ezsp.EZSP, "set_source_routing", new_callable=AsyncMock)
@patch("bellows.ezsp.v4.EZSPv4.initialize", new_callable=AsyncMock)
@patch.object(ezsp.EZSP, "version", new_callable=AsyncMock)
@patch.object(ezsp.EZSP, "reset", new_callable=AsyncMock)
@patch("bellows.uart.connect", return_value=MagicMock(spec_set=uart.Gateway))
async def test_ezsp_init(
    conn_mock, reset_mock, version_mock, prot_handler_mock, src_mock
):
    """Test initialize method."""
    zigpy_config = config.CONFIG_SCHEMA({"device": DEVICE_CONFIG})
    await ezsp.EZSP.initialize(zigpy_config)
    assert conn_mock.await_count == 1
    assert reset_mock.await_count == 1
    assert version_mock.await_count == 1
    assert prot_handler_mock.await_count == 1
    assert src_mock.call_count == 0
    assert src_mock.await_count == 0

    zigpy_config = config.CONFIG_SCHEMA(
        {"device": DEVICE_CONFIG, "source_routing": "yes"}
    )
    await ezsp.EZSP.initialize(zigpy_config)
    assert src_mock.await_count == 1


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
    assert ver == "unknown stack version"

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


async def test_set_concentrator(ezsp_f):
    """Test enabling source routing."""
    with patch.object(ezsp_f, "setConcentrator", new=AsyncMock()) as cnc_mock:
        cnc_mock.return_value = (ezsp_f.types.EmberStatus.SUCCESS,)
        await ezsp_f.set_source_routing()
        assert cnc_mock.await_count == 1

        cnc_mock.return_value = (ezsp_f.types.EmberStatus.ERR_FATAL,)
        await ezsp_f.set_source_routing()
        assert cnc_mock.await_count == 2


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
        (status,) = await ezsp_f.leaveNetwork(timeout=0.01)
        assert status == t.EmberStatus.NETWORK_DOWN


@pytest.mark.parametrize(
    "value, expected_result",
    [(b"\xFF" * 8, True), (bytes.fromhex("0846b8a11c004b1200"), False)],
)
async def test_can_write_custom_eui64(ezsp_f, value, expected_result):
    """Test detecting whether or not the EUI64 can be written again."""
    ezsp_f.getMfgToken = AsyncMock(return_value=[value])

    result = await ezsp_f.can_write_custom_eui64()
    assert result == expected_result

    ezsp_f.getMfgToken.assert_called_once_with(t.EzspMfgTokenId.MFG_CUSTOM_EUI_64)


@patch.object(ezsp.EZSP, "set_source_routing", new_callable=AsyncMock)
@patch("bellows.ezsp.v4.EZSPv4.initialize", new_callable=AsyncMock)
@patch.object(ezsp.EZSP, "version", new_callable=AsyncMock)
@patch.object(ezsp.EZSP, "reset", new_callable=AsyncMock)
@patch("bellows.uart.connect", return_value=MagicMock(spec_set=uart.Gateway))
async def test_ezsp_init_zigbeed(
    conn_mock, reset_mock, version_mock, prot_handler_mock, src_mock
):
    """Test initialize method with a received startup reset frame."""
    zigpy_config = config.CONFIG_SCHEMA(
        {
            "device": {
                **DEVICE_CONFIG,
                config.CONF_DEVICE_PATH: "socket://localhost:1234",
            }
        }
    )

    gw_wait_reset_mock = conn_mock.return_value.wait_for_startup_reset = AsyncMock()

    await ezsp.EZSP.initialize(zigpy_config)

    assert conn_mock.await_count == 1
    assert reset_mock.await_count == 0  # Reset is not called
    assert gw_wait_reset_mock.await_count == 1
    assert version_mock.await_count == 1
    assert prot_handler_mock.await_count == 1
    assert src_mock.call_count == 0
    assert src_mock.await_count == 0


@patch.object(ezsp.EZSP, "set_source_routing", new_callable=AsyncMock)
@patch("bellows.ezsp.v4.EZSPv4.initialize", new_callable=AsyncMock)
@patch.object(ezsp.EZSP, "version", new_callable=AsyncMock)
@patch.object(ezsp.EZSP, "reset", new_callable=AsyncMock)
@patch("bellows.uart.connect", return_value=MagicMock(spec_set=uart.Gateway))
@patch("bellows.ezsp.NETWORK_COORDINATOR_STARTUP_RESET_WAIT", 0.01)
async def test_ezsp_init_zigbeed_timeout(
    conn_mock, reset_mock, version_mock, prot_handler_mock, src_mock
):
    """Test initialize method with a received startup reset frame."""
    zigpy_config = config.CONFIG_SCHEMA(
        {
            "device": {
                **DEVICE_CONFIG,
                config.CONF_DEVICE_PATH: "socket://localhost:1234",
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
    assert prot_handler_mock.await_count == 1
    assert src_mock.call_count == 0
    assert src_mock.await_count == 0
