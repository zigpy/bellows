import asyncio
from asyncio import timeout as asyncio_timeout
import logging
import pickle
import socket
import struct
import threading
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, call, patch, sentinel

import pytest
import zigpy.serial

from bellows import uart
from bellows.ash import AshProtocol, NcpFailure, NcpResetCode, Reserved, RStackFrame
import bellows.types as t

DEVICE = {"path": "/dev/serial", "baudrate": 115200, "flow_control": None}


def bellows_threads():
    return [t for t in threading.enumerate() if "bellows" in t.name]


def assert_no_threads():
    [t.join(1) for t in bellows_threads()]
    assert bellows_threads() == []


@pytest.mark.parametrize(
    ("flow_control", "xonxoff", "rtscts"),
    [
        (None, True, False),
        ("software", True, False),
        ("hardware", False, True),
    ],
)
async def test_connect(flow_control, xonxoff, rtscts):
    appmock = MagicMock()
    transport = MagicMock()
    kwargs = {}

    async def mockconnect(loop, protocol_factory, **kw):
        kwargs.update(kw)
        protocol = protocol_factory()
        loop.call_soon(protocol.connection_made, transport)
        return None, protocol

    with patch("zigpy.serial.create_serial_connection", mockconnect):
        gw = await uart.connect(
            appmock,
            path="/dev/serial",
            baudrate=115200,
            flow_control=flow_control,
            isolated=False,
        )

    assert isinstance(gw, uart.Gateway)
    assert kwargs == {
        "url": "/dev/serial",
        "baudrate": 115200,
        "xonxoff": xonxoff,
        "rtscts": rtscts,
    }
    gw.close()


class MockSerial:
    """Stands in for `zigpy.serial.create_serial_connection` and remembers the worker side."""

    def __init__(self):
        self.transport = MagicMock()
        self.transport.close.side_effect = self.on_transport_close
        self.protocol = None

    async def __call__(self, loop, protocol_factory, **kwargs):
        self.protocol = protocol_factory()
        loop.call_soon(self.protocol.connection_made, self.transport)
        return self.transport, self.protocol

    def on_transport_close(self):
        self.protocol.connection_lost(None)

    def lose_connection(self, exc):
        asyncio.get_running_loop().call_soon(self.protocol.connection_lost, exc)


@pytest.fixture
def serial():
    serial = MockSerial()

    with patch("zigpy.serial.create_serial_connection", serial):
        yield serial


@pytest.fixture
def app():
    return MagicMock()


@pytest.fixture
def gateways():
    """Every `Gateway` the worker creates, since the worker does not hand them out."""
    gateways = []

    class RecordingGateway(uart.Gateway):
        def __init__(self, api):
            super().__init__(api)
            gateways.append(self)

    with patch.object(uart, "Gateway", RecordingGateway):
        yield gateways


async def in_process_worker(sock, path, baudrate, flow_control, log_levels):
    reader, writer = await asyncio.open_connection(sock=sock)

    try:
        await uart._Worker(reader, writer).run(path, baudrate, flow_control)
    finally:
        writer.close()
        await writer.wait_closed()


@pytest.fixture
def workers():
    """Runs workers on the test loop instead of in a subinterpreter, so mocks reach them."""
    workers = SimpleNamespace(tasks=[], worker=in_process_worker)

    def launch(loop, fd, *args):
        task = asyncio.ensure_future(workers.worker(socket.socket(fileno=fd), *args))
        workers.tasks.append(task)
        return None, task

    # The protocol does not need subinterpreters, so these tests run on every Python
    with (
        patch.object(uart, "_launch_worker", launch),
        patch.object(uart, "interpreters", MagicMock()),
    ):
        yield workers


@pytest.fixture
async def isolated_gw(workers, gateways, serial, app):
    gw = await uart.connect(app, **DEVICE)
    assert isinstance(gw, uart.IsolatedGateway)

    yield gw

    async with asyncio_timeout(1):
        await gw.disconnect()

    assert workers.tasks[0].done()


async def test_connect_isolated(isolated_gw, workers, serial, app):
    async with asyncio_timeout(1):
        await isolated_gw.disconnect()

    assert serial.transport.close.call_count == 1
    assert app.connection_lost.mock_calls == [call(None)]
    assert workers.tasks[0].done()

    # A second disconnect is a no-op
    async with asyncio_timeout(1):
        await isolated_gw.disconnect()


async def test_connect_isolated_failure(workers):
    mockconnect = AsyncMock(side_effect=OSError)

    with (
        patch("zigpy.serial.create_serial_connection", mockconnect),
        pytest.raises(OSError),
    ):
        await uart.connect(MagicMock(), **DEVICE)

    assert workers.tasks[0].done()


async def test_connect_isolated_cancelled(workers):
    async def mockconnect(loop, protocol_factory, **kwargs):
        await asyncio.get_running_loop().create_future()

    with patch("zigpy.serial.create_serial_connection", mockconnect):
        task = asyncio.create_task(uart.connect(MagicMock(), **DEVICE))
        await asyncio.sleep(0.1)
        task.cancel()

        with pytest.raises(asyncio.CancelledError):
            await task

    assert workers.tasks[0].done()


async def test_connect_isolated_cancelled_after_port_opened(workers):
    transport = MagicMock()
    transport.wait_closed = AsyncMock()

    async def mockconnect(loop, protocol_factory, **kwargs):
        protocol = protocol_factory()
        loop.call_later(1, protocol.connection_made, transport)
        return transport, protocol

    with patch("zigpy.serial.create_serial_connection", mockconnect):
        task = asyncio.create_task(uart.connect(MagicMock(), **DEVICE))
        await asyncio.sleep(0.1)
        task.cancel()

        with pytest.raises(asyncio.CancelledError):
            await task

    assert transport.close.call_count == 1
    assert transport.wait_closed.mock_calls == [call()]
    assert workers.tasks[0].done()


async def test_connect_isolated_cancelled_after_connected(workers, serial, app):
    """Cancelled once the worker has connected, before `Connected` has been read here."""
    connected = asyncio.get_running_loop().create_future()
    real_connect = uart._connect

    async def _connect(api, **kwargs):
        gateway = await real_connect(api, **kwargs)
        connected.set_result(None)
        return gateway

    with patch.object(uart, "_connect", _connect):
        task = asyncio.create_task(uart.connect(app, **DEVICE))
        await connected
        task.cancel()

        with pytest.raises(asyncio.CancelledError):
            await task

    assert serial.transport.close.call_count == 1
    assert workers.tasks[0].done()


async def test_isolated_calls_run_on_worker(isolated_gw, gateways, serial, app):
    sent = []

    async def send_data(data):
        sent.append(data)

    # `serial.protocol` is the `AshProtocol`, the gateway's transport
    serial.protocol.send_data = send_data

    await isolated_gw.send_data(b"data")
    assert sent == [b"data"]

    gateways[0].data_received(b"frame")
    gateways[0].error_received(NcpResetCode.RESET_SOFTWARE)

    # Messages arrive in order, so the events have been handled once this reply has
    await isolated_gw.send_data(b"data")

    assert app.frame_received.mock_calls == [call(b"frame")]
    assert app.enter_failed_state.mock_calls == [call(NcpResetCode.RESET_SOFTWARE)]


async def test_isolated_reset(isolated_gw, gateways, serial):
    def send_reset():
        asyncio.get_running_loop().call_soon(
            gateways[0].reset_received, NcpResetCode.RESET_SOFTWARE
        )

    serial.protocol.send_reset = send_reset

    async with asyncio_timeout(1):
        assert await isolated_gw.reset() is True


async def test_isolated_request_failure(isolated_gw, serial):
    code = NcpResetCode.ERROR_EXCEEDED_MAXIMUM_ACK_TIMEOUT_COUNT
    serial.protocol.send_data = AsyncMock(side_effect=NcpFailure(code))

    with pytest.raises(NcpFailure) as exc_info:
        await isolated_gw.send_data(b"data")

    assert exc_info.value.code == code

    serial.protocol.send_data = AsyncMock(side_effect=ValueError("odd"))

    with pytest.raises(RuntimeError, match="ValueError: odd"):
        await isolated_gw.send_data(b"data")


async def test_isolated_connection_lost(isolated_gw, serial, app):
    wait_for_reset = asyncio.ensure_future(isolated_gw.wait_for_startup_reset())
    await asyncio.sleep(0.1)
    serial.lose_connection(RuntimeError("boom"))

    # The failure propagates to the application loop
    with pytest.raises(RuntimeError, match="boom"):
        async with asyncio_timeout(1):
            await wait_for_reset

    async with asyncio_timeout(1):
        await isolated_gw.disconnect()

    assert len(app.connection_lost.mock_calls) == 1
    (exc,) = app.connection_lost.mock_calls[0].args
    assert isinstance(exc, RuntimeError) and exc.args == ("boom",)

    # Later calls fail with the transport's error as their cause
    with pytest.raises(ConnectionResetError) as exc_info:
        await isolated_gw.send_data(b"data")

    assert isinstance(exc_info.value.__cause__, RuntimeError)
    assert exc_info.value.__cause__.args == ("boom",)


async def test_isolated_call_after_disconnect(isolated_gw):
    async with asyncio_timeout(1):
        await isolated_gw.disconnect()

    with pytest.raises(ConnectionResetError) as exc_info:
        await isolated_gw.reset()

    assert exc_info.value.__cause__ is None


async def test_isolated_call_after_connection_lost_on_worker(isolated_gw, serial, app):
    """A call queued before the loss is delivered here fails instead of hanging."""
    lost = asyncio.get_running_loop().create_future()
    app.connection_lost.side_effect = lambda exc: lost.set_result(exc)

    # Lose the connection on the worker and queue a call behind it, before the application
    # loop has been told
    serial.lose_connection(None)
    send = asyncio.ensure_future(isolated_gw.send_data(b"data"))

    with pytest.raises(ConnectionResetError):
        async with asyncio_timeout(1):
            await send

    async with asyncio_timeout(1):
        await lost


async def test_isolated_stuck_task_on_shutdown(isolated_gw, serial):
    async def wait_forever(data):
        await asyncio.get_running_loop().create_future()

    serial.protocol.send_data = wait_forever

    send = asyncio.ensure_future(isolated_gw.send_data(b"data"))
    await asyncio.sleep(0.1)
    serial.lose_connection(RuntimeError("boom"))

    # Cancelled by the worker during shutdown, so the caller sees a connection error
    with pytest.raises(ConnectionResetError) as exc_info:
        async with asyncio_timeout(1):
            await send

    assert isinstance(exc_info.value.__cause__, RuntimeError)


async def test_isolated_caller_cancellation(isolated_gw, serial):
    cancelled = asyncio.get_running_loop().create_future()

    async def wait_forever(data):
        try:
            await asyncio.get_running_loop().create_future()
        except asyncio.CancelledError:
            cancelled.set_result(None)
            raise

    serial.protocol.send_data = wait_forever

    with pytest.raises(TimeoutError):
        async with asyncio_timeout(0.1):
            await isolated_gw.send_data(b"data")

    # The cancellation reached the worker
    async with asyncio_timeout(1):
        await cancelled


def _frame(payload: bytes) -> bytes:
    return struct.pack("<I", len(payload)) + payload


async def test_isolated_worker_exits_unexpectedly(workers, app):
    async def worker(sock, *args):
        reader, writer = await asyncio.open_connection(sock=sock)
        writer.write(_frame(pickle.dumps(uart.Connected())))
        # Dies with a request outstanding
        await reader.readexactly(4)
        writer.close()
        await writer.wait_closed()

    workers.worker = worker
    gw = await uart.connect(app, **DEVICE)

    with pytest.raises(ConnectionResetError):
        async with asyncio_timeout(1):
            await gw.reset()

    assert len(app.connection_lost.mock_calls) == 1
    assert isinstance(app.connection_lost.mock_calls[0].args[0], ConnectionResetError)

    with pytest.raises(ConnectionResetError):
        await gw.send_data(b"data")

    async with asyncio_timeout(1):
        await gw.disconnect()


async def test_isolated_worker_exits_before_connecting(workers, app):
    async def worker(sock, *args):
        reader, writer = await asyncio.open_connection(sock=sock)
        writer.close()
        await writer.wait_closed()

    workers.worker = worker

    with pytest.raises(ConnectionResetError):
        await uart.connect(app, **DEVICE)


async def test_isolated_refuses_unlisted_class(workers, app):
    """A message naming a class outside the protocol's vocabulary is rejected."""

    async def worker(sock, *args):
        reader, writer = await asyncio.open_connection(sock=sock)
        writer.write(_frame(pickle.dumps(uart.Connected())))
        writer.write(_frame(pickle.dumps(uart.ConnectionLost(ValueError("no")))))
        await reader.read()
        writer.close()
        await writer.wait_closed()

    workers.worker = worker
    gw = await uart.connect(app, **DEVICE)

    with pytest.raises(pickle.UnpicklingError, match="ValueError"):
        async with asyncio_timeout(1):
            await gw.disconnect()


class FakeNcp(AshProtocol):
    """The NCP end of the link: ACKs data like the host side does, answers RST."""

    def __init__(self):
        super().__init__(MagicMock())
        self.transport = None

    def connection_made(self, transport):
        super().connection_made(transport)
        self.transport = transport

    def rst_frame_received(self, frame):
        super().rst_frame_received(frame)
        self.send_rstack()

    def send_rstack(self):
        frame = RStackFrame(version=2, reset_code=NcpResetCode.RESET_SOFTWARE)
        self.transport.write(frame.to_bytes() + bytes([Reserved.FLAG]))


@pytest.fixture
async def ncp():
    ncps = []

    def factory():
        ncps.append(FakeNcp())
        return ncps[-1]

    server = await asyncio.get_running_loop().create_server(factory, "127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]

    yield ncps, f"socket://127.0.0.1:{port}"

    server.close()


needs_interpreters = pytest.mark.skipif(
    uart.interpreters is None, reason="Subinterpreters need Python 3.14"
)


@pytest.fixture
async def real_gw(ncp, app, caplog):
    """A gateway in a real subinterpreter, always disconnected, even when the test fails."""
    ncps, path = ncp

    # The worker copies this level when it starts
    caplog.set_level(logging.DEBUG, logger="bellows.uart")

    gw = await uart.connect(app, path=path, baudrate=115200, flow_control=None)
    assert isinstance(gw, uart.IsolatedGateway)

    yield gw

    async with asyncio_timeout(1):
        await gw.disconnect()


@needs_interpreters
async def test_interpreter_roundtrip(real_gw, ncp, app, caplog):
    gw = real_gw
    ncps, _ = ncp
    frames = []
    app.frame_received.side_effect = frames.append

    assert len(bellows_threads()) == 1

    async with asyncio_timeout(1):
        assert await gw.reset() is True
        await gw.send_data(b"\x01\x02\x03")
        await ncps[0].send_data(b"\xaa\xbb")

    assert ncps[0]._ezsp_protocol.data_received.mock_calls == [call(b"\x01\x02\x03")]
    assert frames == [b"\xaa\xbb"]

    # A cancelled wait is cancelled on the worker too: a second one would otherwise fail
    waiting = asyncio.ensure_future(gw.wait_for_startup_reset())
    await asyncio.sleep(0.1)
    waiting.cancel()

    with pytest.raises(asyncio.CancelledError):
        await waiting

    waiting = asyncio.ensure_future(gw.wait_for_startup_reset())
    await asyncio.sleep(0.1)
    ncps[0].send_rstack()

    async with asyncio_timeout(1):
        await waiting

    async with asyncio_timeout(1):
        await gw.disconnect()

    assert app.connection_lost.mock_calls == [call(None)]
    assert_no_threads()

    # The worker's log records arrive under their own logger names
    assert [r.message for r in caplog.records if r.name == "bellows.uart"] == [
        "Resetting ASH",
        "Received reset: <NcpResetCode.RESET_SOFTWARE: 11>",
        "Received reset: <NcpResetCode.RESET_SOFTWARE: 11>",
    ]


@needs_interpreters
async def test_interpreter_connect_failure(app):
    with pytest.raises(FileNotFoundError):
        await uart.connect(
            app, path="/nonexistent/serial/port", baudrate=115200, flow_control=None
        )

    assert_no_threads()


@pytest.fixture
async def gw():
    gw = uart.Gateway(MagicMock())
    gw._transport = MagicMock()
    return gw


def test_close(gw):
    gw.close()
    assert gw._transport.close.call_count == 1


async def test_reset_timeout(gw, monkeypatch):
    monkeypatch.setattr(uart, "RESET_TIMEOUT", 0.1)
    with pytest.raises(TimeoutError):
        await gw.reset()


async def test_reset_old(gw):
    future = asyncio.get_running_loop().create_future()
    future.set_result(sentinel.result)
    gw._reset_future = future
    ret = await gw.reset()
    assert ret == sentinel.result
    assert len(gw._transport.write.mock_calls) == 0


async def test_disconnected(gw):
    gw._transport = None

    with pytest.raises(ConnectionResetError):
        await gw.send_data(b"data")

    with pytest.raises(ConnectionResetError):
        await gw.reset()

    with pytest.raises(ConnectionResetError):
        await gw.wait_for_startup_reset()


async def test_connection_lost_cancelled_startup_reset(gw):
    task = asyncio.create_task(gw.wait_for_startup_reset())
    await asyncio.sleep(0)

    # The future is cancelled synchronously, the task only resumes on a later step
    task.cancel()
    gw.connection_lost(RuntimeError())

    with pytest.raises(asyncio.CancelledError):
        await task


def test_connection_lost_exc(gw):
    gw.connection_lost(sentinel.exception)

    conn_lost = gw._api.connection_lost
    assert conn_lost.call_count == 1
    assert conn_lost.mock_calls[0].args[0] is sentinel.exception


async def test_connection_lost_reset_error_propagation(monkeypatch):
    app = MagicMock()
    transport = MagicMock()
    transport.is_closing.return_value = False

    async def mockconnect(loop, protocol_factory, **kwargs):
        protocol = protocol_factory()
        loop.call_soon(protocol.connection_made, transport)
        return None, protocol

    monkeypatch.setattr(zigpy.serial, "create_serial_connection", mockconnect)

    def on_transport_close():
        gw.connection_lost(None)

    transport.close.side_effect = on_transport_close
    gw = await uart.connect(app, **DEVICE, isolated=False)

    asyncio.get_running_loop().call_later(0.1, gw.connection_lost, ValueError())

    with pytest.raises(ValueError):
        await gw.reset()

    gw.close()


@pytest.mark.parametrize(
    "reset_code",
    [
        t.NcpResetCode.RESET_SOFTWARE,
        t.NcpResetCode.RESET_POWER_ON,
        t.NcpResetCode.RESET_WATCHDOG,
        t.NcpResetCode.RESET_EXTERNAL,
    ],
)
async def test_wait_for_startup_reset(gw, reset_code):
    loop = asyncio.get_running_loop()
    loop.call_later(0.01, gw.reset_received, reset_code)

    assert gw._startup_reset_future is None
    await gw.wait_for_startup_reset()
    assert gw._startup_reset_future is None


async def test_wait_for_startup_reset_failure(gw):
    assert gw._startup_reset_future is None

    with pytest.raises(TimeoutError):
        await asyncio.wait_for(gw.wait_for_startup_reset(), 0.01)

    assert gw._startup_reset_future is None


async def test_callbacks(gw):
    gw.data_received(b"some ezsp packet")
    assert gw._api.frame_received.mock_calls == [call(b"some ezsp packet")]

    gw.error_received(t.NcpResetCode.RESET_SOFTWARE)
    assert gw._api.enter_failed_state.mock_calls == [
        call(t.NcpResetCode.RESET_SOFTWARE)
    ]


async def test_error_received_during_reset_ignored(gw):
    # Set up a reset future to simulate being in the middle of a reset
    loop = asyncio.get_running_loop()
    gw._reset_future = loop.create_future()

    # Error should be ignored (not trigger failed state)
    gw.error_received(t.NcpResetCode.ERROR_EXCEEDED_MAXIMUM_ACK_TIMEOUT_COUNT)
    assert gw._api.enter_failed_state.call_count == 0

    # Clean up
    gw._reset_future.cancel()


def test_unexpected_reset_triggers_failed_state(gw):
    # When no reset is expected, any reset should trigger failed state
    assert gw._reset_future is None
    assert gw._startup_reset_future is None

    gw.reset_received(t.NcpResetCode.RESET_SOFTWARE)
    assert gw._api.enter_failed_state.mock_calls == [
        call(t.NcpResetCode.RESET_SOFTWARE)
    ]
