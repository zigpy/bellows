import asyncio
import functools

from asynctest import CoroutineMock, mock
from bellows import ezsp, uart
from bellows.exception import EzspError
import pytest
import serial


@pytest.fixture
def ezsp_f():
    api = ezsp.EZSP()
    api._gw = mock.MagicMock(spec_set=uart.Gateway)
    return api


def test_connect(ezsp_f, monkeypatch):
    connected = False

    async def mockconnect(*args, **kwargs):
        nonlocal connected
        connected = True

    monkeypatch.setattr(uart, "connect", mockconnect)
    ezsp_f._gw = None

    loop = asyncio.get_event_loop()
    loop.run_until_complete(ezsp_f.connect(mock.sentinel.port, mock.sentinel.speed))
    assert connected

    ezsp_f.connect = mock.MagicMock(side_effect=asyncio.coroutine(mock.MagicMock()))
    loop.run_until_complete(ezsp_f.reconnect())
    assert ezsp_f.connect.call_count == 1
    assert ezsp_f.connect.call_args[0][0] is mock.sentinel.port
    assert ezsp_f.connect.call_args[0][1] is mock.sentinel.speed


@pytest.mark.asyncio
async def test_reset(ezsp_f):
    ezsp_f.stop_ezsp = mock.MagicMock()
    ezsp_f.start_ezsp = mock.MagicMock()
    reset_mock = asyncio.coroutine(mock.MagicMock())
    ezsp_f._gw.reset = mock.MagicMock(side_effect=reset_mock)
    f_1 = asyncio.Future()
    ezsp_f._awaiting[1] = (mock.sentinel.schema1, mock.sentinel.schema2, f_1)

    await ezsp_f.reset()
    assert ezsp_f._gw.reset.call_count == 1
    assert ezsp_f.start_ezsp.call_count == 1
    assert ezsp_f.stop_ezsp.call_count == 1
    assert f_1.done() is True
    assert f_1.cancelled() is True
    assert len(ezsp_f._awaiting) == 0
    assert len(ezsp_f._callbacks) == 0
    assert ezsp_f._seq == 0


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


def test_non_existent_attr_with_list(ezsp_f):
    with pytest.raises(AttributeError):
        ezsp_f.__getattr__(("unexpectedly", "hah"))


@pytest.mark.asyncio
async def test_command(ezsp_f):
    ezsp_f._gw = mock.MagicMock()

    ezsp_f.start_ezsp()
    coro = ezsp_f._command("nop")
    ezsp_f._awaiting[ezsp_f._seq - 1][2].set_result(True)
    await coro
    assert ezsp_f._gw.data.call_count == 1


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
        ezsp_f.frame_received(b"\x01\x00\x1b")
        ezsp_f.frame_received(b"\x02\x00\x1b")
        ezsp_f.frame_received(b"\x03\x00\x1c")

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
        ezsp_f.frame_received(b"\x01\x00\x1b")
        ezsp_f.frame_received(b"\x02\x00\x1b")
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
    ezsp_f.handle_callback = mock.MagicMock()
    ezsp_f.frame_received(b"\x00\xff\x00\x04\x05\x06")
    assert ezsp_f.handle_callback.call_count == 1


def test_receive_protocol_5(ezsp_f):
    ezsp_f.handle_callback = mock.MagicMock()
    ezsp_f.frame_received(b"\x01\x80\xff\x00\x00\x06\x02\x00")
    assert ezsp_f.handle_callback.call_count == 1


def test_receive_reply(ezsp_f):
    ezsp_f.handle_callback = mock.MagicMock()
    callback_mock = mock.MagicMock(spec_set=asyncio.Future)
    ezsp_f._awaiting[0] = (0, ezsp_f.COMMANDS["version"][2], callback_mock)
    ezsp_f.frame_received(b"\x00\xff\x00\x04\x05\x06")

    assert 0 not in ezsp_f._awaiting
    assert callback_mock.set_exception.call_count == 0
    assert callback_mock.set_result.call_count == 1
    callback_mock.set_result.assert_called_once_with([4, 5, 6])
    assert ezsp_f.handle_callback.call_count == 0


def test_receive_reply_after_timeout(ezsp_f):
    ezsp_f.handle_callback = mock.MagicMock()
    callback_mock = mock.MagicMock(spec_set=asyncio.Future)
    callback_mock.set_result.side_effect = asyncio.InvalidStateError()
    ezsp_f._awaiting[0] = (0, ezsp_f.COMMANDS["version"][2], callback_mock)
    ezsp_f.frame_received(b"\x00\xff\x00\x04\x05\x06")

    assert 0 not in ezsp_f._awaiting
    assert callback_mock.set_exception.call_count == 0
    assert callback_mock.set_result.call_count == 1
    callback_mock.set_result.assert_called_once_with([4, 5, 6])
    assert ezsp_f.handle_callback.call_count == 0


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
        ezsp_f.frame_received(b"\x01\x00\x1b")
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


def test_ezsp_frame(ezsp_f):
    ezsp_f._seq = 0x22
    data = ezsp_f._ezsp_frame("version", 6)
    assert data == b"\x22\x00\x00\x06"

    ezsp_f._ezsp_version = 5
    data = ezsp_f._ezsp_frame("version", 6)
    assert data == b"\x22\x00\xff\x00\x00\x06"


@pytest.mark.asyncio
@mock.patch.object(ezsp.EZSP, "reset", new_callable=CoroutineMock)
@mock.patch.object(uart, "connect")
async def test_probe_success(mock_connect, mock_reset):
    """Test device probing."""

    res = await ezsp.EZSP.probe(mock.sentinel.uart, mock.sentinel.baud)
    assert res is True
    assert mock_connect.call_count == 1
    assert mock_connect.await_count == 1
    assert mock_connect.call_args[0][0] is mock.sentinel.uart
    assert mock_reset.call_count == 1
    assert mock_connect.return_value.close.call_count == 1

    mock_connect.reset_mock()
    mock_reset.reset_mock()
    mock_connect.reset_mock()
    res = await ezsp.EZSP.probe(mock.sentinel.uart, mock.sentinel.baud)
    assert res is True
    assert mock_connect.call_count == 1
    assert mock_connect.await_count == 1
    assert mock_connect.call_args[0][0] is mock.sentinel.uart
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
    res = await ezsp.EZSP.probe(mock.sentinel.uart, mock.sentinel.baud)
    assert res is False
    assert mock_connect.call_count == 1
    assert mock_connect.await_count == 1
    assert mock_connect.call_args[0][0] is mock.sentinel.uart
    assert mock_reset.call_count == 1
    assert mock_connect.return_value.close.call_count == 1
