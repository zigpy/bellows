import asyncio
import threading
from unittest.mock import AsyncMock, MagicMock, call, patch, sentinel

import pytest
import zigpy.config as conf
import zigpy.serial

from bellows import uart
import bellows.types as t


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

    threads = [t for t in threading.enumerate() if "bellows" in t.name]
    assert len(threads) == 0
    gw.close()


async def test_connect_threaded(monkeypatch):
    appmock = MagicMock()
    transport = MagicMock()

    async def mockconnect(loop, protocol_factory, **kwargs):
        protocol = protocol_factory()
        loop.call_soon(protocol.connection_made, transport)
        return None, protocol

    monkeypatch.setattr(zigpy.serial, "create_serial_connection", mockconnect)

    def on_transport_close():
        gw.connection_lost(None)

    transport.close.side_effect = on_transport_close
    gw = await uart.connect(
        conf.SCHEMA_DEVICE(
            {conf.CONF_DEVICE_PATH: "/dev/serial", conf.CONF_DEVICE_BAUDRATE: 115200}
        ),
        appmock,
    )

    # Need to close to release thread
    gw.close()

    # Ensure all threads are cleaned up
    [t.join(1) for t in threading.enumerate() if "bellows" in t.name]
    threads = [t for t in threading.enumerate() if "bellows" in t.name]
    assert len(threads) == 0


async def test_connect_threaded_failure(monkeypatch):
    appmock = MagicMock()
    transport = MagicMock()

    mockconnect = AsyncMock()
    mockconnect.side_effect = OSError

    monkeypatch.setattr(zigpy.serial, "create_serial_connection", mockconnect)

    def on_transport_close():
        gw.connection_lost(None)

    transport.close.side_effect = on_transport_close
    with pytest.raises(OSError):
        gw = await uart.connect(
            conf.SCHEMA_DEVICE(
                {
                    conf.CONF_DEVICE_PATH: "/dev/serial",
                    conf.CONF_DEVICE_BAUDRATE: 115200,
                }
            ),
            appmock,
        )

    # Ensure all threads are cleaned up
    [t.join(1) for t in threading.enumerate() if "bellows" in t.name]
    threads = [t for t in threading.enumerate() if "bellows" in t.name]
    assert len(threads) == 0


async def test_connect_threaded_failure_cancellation_propagation(monkeypatch):
    appmock = MagicMock()

    async def mock_connect(loop, protocol_factory, *args, **kwargs):
        protocol = protocol_factory()
        transport = AsyncMock()

        protocol.connection_made(transport)

        return transport, protocol

    with patch("bellows.uart.zigpy.serial.create_serial_connection", mock_connect):
        gw = await uart.connect(
            conf.SCHEMA_DEVICE(
                {
                    conf.CONF_DEVICE_PATH: "/dev/serial",
                    conf.CONF_DEVICE_BAUDRATE: 115200,
                }
            ),
            appmock,
            use_thread=True,
        )

    # Begin waiting for the startup reset
    wait_for_reset = gw.wait_for_startup_reset()

    # But lose connection halfway through
    asyncio.get_running_loop().call_later(0.1, gw.connection_lost, RuntimeError())

    # Cancellation should propagate to the outer loop
    with pytest.raises(RuntimeError):
        await wait_for_reset

    # Ensure all threads are cleaned up
    [t.join(1) for t in threading.enumerate() if "bellows" in t.name]
    threads = [t for t in threading.enumerate() if "bellows" in t.name]
    assert len(threads) == 0


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
    with pytest.raises(asyncio.TimeoutError):
        await gw.reset()


async def test_reset_old(gw):
    future = asyncio.get_event_loop().create_future()
    future.set_result(sentinel.result)
    gw._reset_future = future
    ret = await gw.reset()
    assert ret == sentinel.result
    gw._transport.write.assert_not_called()


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
    gw = await uart.connect(
        conf.SCHEMA_DEVICE(
            {conf.CONF_DEVICE_PATH: "/dev/serial", conf.CONF_DEVICE_BAUDRATE: 115200}
        ),
        app,
        use_thread=False,  # required until #484 is merged
    )

    asyncio.get_running_loop().call_later(0.1, gw.connection_lost, ValueError())

    with pytest.raises(ValueError):
        await gw.reset()

    # Need to close to release thread
    gw.close()

    # Ensure all threads are cleaned up
    [t.join(1) for t in threading.enumerate() if "bellows" in t.name]
    threads = [t for t in threading.enumerate() if "bellows" in t.name]
    assert len(threads) == 0


async def test_wait_for_startup_reset(gw):
    loop = asyncio.get_running_loop()
    loop.call_later(0.01, gw.reset_received, t.NcpResetCode.RESET_SOFTWARE)

    assert gw._startup_reset_future is None
    await gw.wait_for_startup_reset()
    assert gw._startup_reset_future is None


async def test_wait_for_startup_reset_failure(gw):
    assert gw._startup_reset_future is None

    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(gw.wait_for_startup_reset(), 0.01)

    assert gw._startup_reset_future is None


async def test_callbacks(gw):
    gw.data_received(b"some ezsp packet")
    assert gw._api.frame_received.mock_calls == [call(b"some ezsp packet")]

    gw.error_received(t.NcpResetCode.RESET_SOFTWARE)
    assert gw._api.enter_failed_state.mock_calls == [
        call(t.NcpResetCode.RESET_SOFTWARE)
    ]


def test_reset_propagation(gw):
    gw.reset_received(t.NcpResetCode.ERROR_EXCEEDED_MAXIMUM_ACK_TIMEOUT_COUNT)
    assert gw._api.enter_failed_state.mock_calls == [
        call(t.NcpResetCode.ERROR_EXCEEDED_MAXIMUM_ACK_TIMEOUT_COUNT)
    ]
