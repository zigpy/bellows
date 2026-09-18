import asyncio
from asyncio import timeout as asyncio_timeout
import threading
from unittest.mock import AsyncMock, MagicMock, call, sentinel

import pytest
import zigpy.config as conf
import zigpy.serial

from bellows import uart
import bellows.thread
import bellows.types as t

DEVICE_CONFIG = conf.SCHEMA_DEVICE(
    {conf.CONF_DEVICE_PATH: "/dev/serial", conf.CONF_DEVICE_BAUDRATE: 115200}
)


def bellows_threads():
    return [t for t in threading.enumerate() if "bellows" in t.name]


def assert_no_threads():
    [t.join(1) for t in bellows_threads()]
    assert bellows_threads() == []


@pytest.mark.parametrize("flow_control", ["software", "hardware"])
async def test_connect(flow_control, monkeypatch):
    appmock = MagicMock()
    transport = MagicMock()

    async def mockconnect(loop, protocol_factory, **kwargs):
        protocol = protocol_factory()
        loop.call_soon(protocol.connection_made, transport)
        return None, protocol

    monkeypatch.setattr(zigpy.serial, "create_serial_connection", mockconnect)
    gw = await uart.connect(
        conf.SCHEMA_DEVICE(
            {
                conf.CONF_DEVICE_PATH: "/dev/serial",
                conf.CONF_DEVICE_BAUDRATE: 115200,
                conf.CONF_DEVICE_FLOW_CONTROL: flow_control,
            }
        ),
        appmock,
        use_thread=False,
    )

    assert bellows_threads() == []
    gw.close()


class MockSerial:
    """Stands in for `zigpy.serial.create_serial_connection` and remembers the worker side."""

    def __init__(self):
        self.transport = MagicMock()
        self.transport.close.side_effect = self.on_transport_close
        self.protocol = None
        self.loop = None

    async def __call__(self, loop, protocol_factory, **kwargs):
        self.loop = asyncio.get_running_loop()
        self.protocol = protocol_factory()
        loop.call_soon(self.protocol.connection_made, self.transport)
        return self.transport, self.protocol

    def on_transport_close(self):
        self.protocol.connection_lost(None)

    def lose_connection(self, exc):
        self.loop.call_soon_threadsafe(self.protocol.connection_lost, exc)


@pytest.fixture
def serial(monkeypatch):
    serial = MockSerial()
    monkeypatch.setattr(zigpy.serial, "create_serial_connection", serial)
    return serial


@pytest.fixture
def app():
    return MagicMock()


@pytest.fixture
async def threaded_gw(serial, app):
    gw = await uart.connect(DEVICE_CONFIG, app, use_thread=True)
    assert isinstance(gw, uart.ThreadedGateway)
    assert len(bellows_threads()) == 1

    yield gw

    async with asyncio_timeout(1):
        await gw.disconnect()
    assert_no_threads()


async def test_connect_threaded(threaded_gw, serial, app):
    async with asyncio_timeout(1):
        await threaded_gw.disconnect()

    assert serial.transport.close.call_count == 1
    assert app.connection_lost.mock_calls == [call(None)]
    assert_no_threads()

    # A second disconnect is a no-op
    async with asyncio_timeout(1):
        await threaded_gw.disconnect()


async def test_connect_threaded_failure(monkeypatch):
    appmock = MagicMock()
    mockconnect = AsyncMock(side_effect=OSError)
    monkeypatch.setattr(zigpy.serial, "create_serial_connection", mockconnect)

    with pytest.raises(OSError):
        await uart.connect(DEVICE_CONFIG, appmock, use_thread=True)

    assert_no_threads()


async def test_connect_threaded_cancelled(monkeypatch):
    appmock = MagicMock()

    async def mockconnect(loop, protocol_factory, **kwargs):
        await asyncio.get_running_loop().create_future()

    monkeypatch.setattr(zigpy.serial, "create_serial_connection", mockconnect)

    task = asyncio.create_task(uart.connect(DEVICE_CONFIG, appmock, use_thread=True))
    await asyncio.sleep(0.1)
    task.cancel()

    with pytest.raises(asyncio.CancelledError):
        await task

    assert_no_threads()


async def test_connect_threaded_cancelled_after_port_opened(monkeypatch):
    transport = MagicMock()
    transport.wait_closed = AsyncMock()

    async def mockconnect(loop, protocol_factory, **kwargs):
        protocol = protocol_factory()
        loop.call_later(1, protocol.connection_made, transport)
        return transport, protocol

    monkeypatch.setattr(zigpy.serial, "create_serial_connection", mockconnect)

    task = asyncio.create_task(
        uart.connect(DEVICE_CONFIG, MagicMock(), use_thread=True)
    )
    await asyncio.sleep(0.1)
    task.cancel()

    with pytest.raises(asyncio.CancelledError):
        await task

    assert transport.close.call_count == 1
    assert transport.wait_closed.mock_calls == [call()]
    assert_no_threads()


async def test_threaded_calls_run_on_worker(threaded_gw, serial, app):
    gateway = threaded_gw._gateway
    worker_loop = None

    async def send_data(data):
        nonlocal worker_loop
        worker_loop = asyncio.get_running_loop()

    # `serial.protocol` is the `AshProtocol`, the gateway's transport
    serial.protocol.send_data = send_data

    await threaded_gw.send_data(b"data")
    assert worker_loop is serial.loop

    serial.loop.call_soon_threadsafe(gateway.data_received, b"frame")
    serial.loop.call_soon_threadsafe(
        gateway.error_received, t.NcpResetCode.RESET_SOFTWARE
    )
    await threaded_gw.send_data(b"data")
    await asyncio.sleep(0)

    assert app.frame_received.mock_calls == [call(b"frame")]
    assert app.enter_failed_state.mock_calls == [call(t.NcpResetCode.RESET_SOFTWARE)]


async def test_threaded_reset(threaded_gw, serial):
    gateway = threaded_gw._gateway

    def send_reset():
        serial.loop.call_soon(gateway.reset_received, t.NcpResetCode.RESET_SOFTWARE)

    serial.protocol.send_reset = send_reset

    async with asyncio_timeout(1):
        assert await threaded_gw.reset() is True


async def test_threaded_connection_lost(threaded_gw, serial, app):
    exc = RuntimeError()

    wait_for_reset = asyncio.ensure_future(threaded_gw.wait_for_startup_reset())
    await asyncio.sleep(0.1)
    serial.lose_connection(exc)

    # The failure propagates to the outer loop
    with pytest.raises(RuntimeError):
        async with asyncio_timeout(1):
            await wait_for_reset

    async with asyncio_timeout(1):
        await threaded_gw.disconnect()

    assert app.connection_lost.mock_calls == [call(exc)]
    assert_no_threads()

    with pytest.raises(ConnectionResetError):
        await threaded_gw.send_data(b"data")


async def test_threaded_call_after_disconnect(threaded_gw):
    async with asyncio_timeout(1):
        await threaded_gw.disconnect()

    with pytest.raises(ConnectionResetError):
        await threaded_gw.reset()


async def test_threaded_call_after_connection_lost_on_worker(threaded_gw, serial, app):
    """A call queued before the loss is delivered here fails instead of hanging."""
    lost = asyncio.get_running_loop().create_future()
    app.connection_lost.side_effect = lambda exc: lost.set_result(exc)

    # Lose the connection on the worker and queue a call behind it, before the application
    # loop has been told
    serial.lose_connection(None)
    send = asyncio.ensure_future(threaded_gw.send_data(b"data"))

    with pytest.raises(ConnectionResetError):
        async with asyncio_timeout(1):
            await send

    async with asyncio_timeout(1):
        await lost


async def test_threaded_stuck_task_on_shutdown(threaded_gw, serial, monkeypatch):
    monkeypatch.setattr(bellows.thread, "SHUTDOWN_TIMEOUT", 0.1)

    async def wait_forever(data):
        await asyncio.get_running_loop().create_future()

    serial.protocol.send_data = wait_forever

    send = asyncio.ensure_future(threaded_gw.send_data(b"data"))
    await asyncio.sleep(0.1)
    serial.lose_connection(None)

    # Cancelled by the worker during shutdown, so the caller sees a connection error
    with pytest.raises(ConnectionResetError):
        async with asyncio_timeout(1):
            await send


async def test_threaded_caller_cancellation(threaded_gw, serial):
    async def wait_forever(data):
        await asyncio.get_running_loop().create_future()

    serial.protocol.send_data = wait_forever

    with pytest.raises(TimeoutError):
        async with asyncio_timeout(0.1):
            await threaded_gw.send_data(b"data")


async def test_threaded_disconnect_timeout(threaded_gw, serial, monkeypatch, caplog):
    monkeypatch.setattr(uart, "DISCONNECT_TIMEOUT", 0.1)
    monkeypatch.setattr(bellows.thread, "SHUTDOWN_TIMEOUT", 0.1)
    serial.transport.close.side_effect = None

    async with asyncio_timeout(1):
        await threaded_gw.disconnect()

    assert "Timed out waiting for the connection to close" in caplog.text
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
    gw = await uart.connect(DEVICE_CONFIG, app, use_thread=False)

    asyncio.get_running_loop().call_later(0.1, gw.connection_lost, ValueError())

    with pytest.raises(ValueError):
        await gw.reset()

    gw.close()
    assert_no_threads()


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
