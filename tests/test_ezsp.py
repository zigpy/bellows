import asyncio
import functools

from asynctest import CoroutineMock, mock
from bellows import config, ezsp, uart
from bellows.exception import EzspError
import bellows.ezsp.v4.types as t
import pytest
import serial

DEVICE_CONFIG = {
    config.CONF_DEVICE_PATH: "/dev/null",
    config.CONF_DEVICE_BAUDRATE: 115200,
}


@pytest.fixture
async def ezsp_f():
    api = ezsp.EZSP(DEVICE_CONFIG)
    with mock.patch("bellows.uart.connect"):
        await api.connect()
        yield api


def test_connect(ezsp_f, monkeypatch):
    connected = False

    async def mockconnect(*args, **kwargs):
        nonlocal connected
        connected = True

    monkeypatch.setattr(uart, "connect", mockconnect)
    ezsp_f._gw = None

    loop = asyncio.get_event_loop()
    loop.run_until_complete(ezsp_f.connect())
    assert connected


@pytest.mark.asyncio
async def test_reset(ezsp_f):
    ezsp_f.stop_ezsp = mock.MagicMock()
    ezsp_f.start_ezsp = mock.MagicMock()
    reset_mock = asyncio.coroutine(mock.MagicMock())
    ezsp_f._gw.reset = mock.MagicMock(side_effect=reset_mock)

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


@pytest.mark.asyncio
def test_command(ezsp_f):
    ezsp_f.start_ezsp()
    with mock.patch.object(ezsp_f._protocol, "command") as cmd_mock:
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
    return loop.run_until_complete(ezsp_f.formNetwork(mock.MagicMock()))


def test_form_network(ezsp_f):
    _test_form_network(ezsp_f, [0], b"\x90")


def test_form_network_fail(ezsp_f):
    with pytest.raises(Exception):
        _test_form_network(ezsp_f, [1], b"\x90")


def test_form_network_fail_stack_status(ezsp_f):
    with pytest.raises(Exception):
        _test_form_network(ezsp_f, [0], b"\x00")


def test_receive_new(ezsp_f):
    callback = mock.MagicMock()
    ezsp_f.add_callback(callback)
    ezsp_f.frame_received(b"\x00\xff\x00\x04\x05\x06")
    assert callback.call_count == 1


def test_callback(ezsp_f):
    testcb = mock.MagicMock()

    cbid = ezsp_f.add_callback(testcb)
    ezsp_f.handle_callback(1, 2, 3)

    assert testcb.call_count == 1

    ezsp_f.remove_callback(cbid)
    ezsp_f.handle_callback(4, 5, 6)
    assert testcb.call_count == 1


def test_callback_multi(ezsp_f):
    testcb = mock.MagicMock()

    cbid1 = ezsp_f.add_callback(testcb)
    ezsp_f.add_callback(testcb)

    ezsp_f.handle_callback(1, 2, 3)

    assert testcb.call_count == 2

    ezsp_f.remove_callback(cbid1)

    ezsp_f.handle_callback(4, 5, 6)
    testcb.assert_has_calls(
        [mock.call(1, 2, 3), mock.call(1, 2, 3), mock.call(4, 5, 6)]
    )


def test_callback_exc(ezsp_f):
    testcb = mock.MagicMock()
    testcb.side_effect = Exception("Testing")

    ezsp_f.add_callback(testcb)
    ezsp_f.handle_callback(1)
    assert testcb.call_count == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("version, call_count", ((4, 1), (5, 2), (6, 2)))
async def test_change_version(ezsp_f, version, call_count):
    def mockcommand(name, *args):
        assert name == "version"
        ezsp_f.frame_received(b"\x01\x00\x00\x21\x22\x23\x24")
        fut = asyncio.Future()
        fut.set_result([version, 2, 2046])
        return fut

    ezsp_f._command = mock.MagicMock(side_effect=mockcommand)
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
    ezsp_f.enter_failed_state = mock.MagicMock(spec_set=ezsp_f.enter_failed_state)
    ezsp_f.connection_lost(mock.sentinel.exc)
    assert ezsp_f.enter_failed_state.call_count == 1


def test_enter_failed_state(ezsp_f):
    ezsp_f.stop_ezsp = mock.MagicMock(spec_set=ezsp_f.stop_ezsp)
    ezsp_f.handle_callback = mock.MagicMock(spec_set=ezsp_f.handle_callback)
    ezsp_f.enter_failed_state(mock.sentinel.error)
    assert ezsp_f.stop_ezsp.call_count == 1
    assert ezsp_f.handle_callback.call_count == 1
    assert ezsp_f.handle_callback.call_args[0][1][0] == mock.sentinel.error


@pytest.mark.asyncio
@mock.patch.object(ezsp.EZSP, "reset", new_callable=CoroutineMock)
@mock.patch.object(uart, "connect")
async def test_probe_success(mock_connect, mock_reset):
    """Test device probing."""

    res = await ezsp.EZSP.probe(DEVICE_CONFIG)
    assert res is True
    assert mock_connect.call_count == 1
    assert mock_connect.await_count == 1
    assert mock_reset.call_count == 1
    assert mock_connect.return_value.close.call_count == 1

    mock_connect.reset_mock()
    mock_reset.reset_mock()
    mock_connect.reset_mock()
    res = await ezsp.EZSP.probe(DEVICE_CONFIG)
    assert res is True
    assert mock_connect.call_count == 1
    assert mock_connect.await_count == 1
    assert mock_reset.call_count == 1
    assert mock_connect.return_value.close.call_count == 1


@pytest.mark.asyncio
@mock.patch.object(ezsp.EZSP, "reset", new_callable=CoroutineMock)
@mock.patch.object(uart, "connect")
@pytest.mark.parametrize(
    "exception", (asyncio.TimeoutError, serial.SerialException, EzspError)
)
async def test_probe_fail(mock_connect, mock_reset, exception):
    """Test device probing fails."""

    mock_reset.side_effect = exception
    mock_reset.reset_mock()
    mock_connect.reset_mock()
    res = await ezsp.EZSP.probe(DEVICE_CONFIG)
    assert res is False
    assert mock_connect.call_count == 1
    assert mock_connect.await_count == 1
    assert mock_reset.call_count == 1
    assert mock_connect.return_value.close.call_count == 1


@pytest.mark.asyncio
@mock.patch("bellows.ezsp.v4.EZSPv4.initialize", new_callable=CoroutineMock)
@mock.patch.object(ezsp.EZSP, "version", new_callable=CoroutineMock)
@mock.patch.object(ezsp.EZSP, "reset", new_callable=CoroutineMock)
@mock.patch.object(uart, "connect")
async def test_ezsp_init(conn_mock, reset_mock, version_mock, prot_handler_mock):
    """Test initializat methdod."""
    await ezsp.EZSP.initialize({"device": DEVICE_CONFIG})
    assert conn_mock.await_count == 1
    assert reset_mock.await_count == 1
    assert version_mock.await_count == 1
    assert prot_handler_mock.await_count == 1


@pytest.mark.asyncio
async def test_ezsp_newer_version(ezsp_f):
    """Test newer version of ezsp."""
    with mock.patch.object(
        ezsp_f, "_command", new=CoroutineMock(return_value=(9, 0x12, 0x12345))
    ):
        await ezsp_f.version()


@pytest.mark.asyncio
async def test_board_info(ezsp_f):
    """Test getting board info."""

    status = 0x00

    async def cmd_mock(cmd_name, *args):
        assert cmd_name in ("getMfgToken", "getValue")
        if cmd_name == "getMfgToken":
            if args[0] == t.EzspMfgTokenId.MFG_BOARD_NAME:
                return (b"\xfe\xff\xff\xff",)
            return (b"Manufacturer\xff\xff\xff",)

        if cmd_name == "getValue":
            return (status, b"\x01\x02\x03\x04\x05\x06")

    with mock.patch.object(ezsp_f, "_command", new=cmd_mock):
        mfg, brd, ver = await ezsp_f.get_board_info()
    assert mfg == "Manufacturer"
    assert brd == b"\xfe"
    assert ver == "3.4.5.6 build 513"

    with mock.patch.object(ezsp_f, "_command", new=cmd_mock):
        status = 0x01
        mfg, brd, ver = await ezsp_f.get_board_info()
    assert mfg == "Manufacturer"
    assert brd == b"\xfe"
    assert ver == "unknown stack version"


@pytest.mark.asyncio
async def test_set_source_route(ezsp_f):
    """Test setting a src route for device."""
    device = mock.MagicMock()
    device.relays = None

    with mock.patch.object(ezsp_f, "setSourceRoute", new=CoroutineMock()) as src_mock:
        src_mock.return_value = (mock.sentinel.success,)
        res = await ezsp_f.set_source_route(device)
        assert src_mock.await_count == 0
        assert res == (t.EmberStatus.ERR_FATAL,)

        device.relays = []
        res = await ezsp_f.set_source_route(device)
        assert src_mock.await_count == 1
        assert res == (mock.sentinel.success,)


def test_pre_permit(ezsp_f):
    with mock.patch("bellows.ezsp.v4.EZSPv4.pre_permit") as pre_mock:
        ezsp_f.pre_permit(mock.sentinel.time)
        assert pre_mock.call_count == 1


def test_update_policies(ezsp_f):
    with mock.patch("bellows.ezsp.v4.EZSPv4.update_policies") as pol_mock:
        ezsp_f.update_policies(mock.sentinel.time)
        assert pol_mock.call_count == 1
