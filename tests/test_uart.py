import asyncio
import threading

import pytest
import serial_asyncio

from bellows import uart
import bellows.config as conf

from .async_mock import AsyncMock, MagicMock, patch, sentinel


@pytest.mark.parametrize("flow_control", [conf.CONF_FLOW_CONTROL_DEFAULT, "hardware"])
async def test_connect(flow_control, monkeypatch):
    appmock = MagicMock()
    transport = MagicMock()

    async def mockconnect(loop, protocol_factory, **kwargs):
        protocol = protocol_factory()
        loop.call_soon(protocol.connection_made, transport)
        return None, protocol

    monkeypatch.setattr(serial_asyncio, "create_serial_connection", mockconnect)
    gw = await uart.connect(
        conf.SCHEMA_DEVICE(
            {
                conf.CONF_DEVICE_PATH: "/dev/serial",
                conf.CONF_DEVICE_BAUDRATE: 115200,
                conf.CONF_FLOW_CONTROL: flow_control,
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

    monkeypatch.setattr(serial_asyncio, "create_serial_connection", mockconnect)

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

    monkeypatch.setattr(serial_asyncio, "create_serial_connection", mockconnect)

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
def gw():
    gw = uart.Gateway(MagicMock())
    gw._transport = MagicMock()
    return gw


def test_randomize(gw):
    assert gw._randomize(b"\x00\x00\x00\x00\x00") == b"\x42\x21\xa8\x54\x2a"
    assert gw._randomize(b"\x42\x21\xa8\x54\x2a") == b"\x00\x00\x00\x00\x00"


def test_stuff(gw):
    orig = b"\x00\x7E\x01\x7D\x02\x11\x03\x13\x04\x18\x05\x1a\x06"
    stuff = (
        b"\x00\x7D\x5E\x01\x7D\x5D\x02\x7D\x31\x03\x7D\x33\x04\x7D\x38\x05\x7D\x3a\x06"
    )
    assert gw._stuff(orig) == stuff


def test_unstuff(gw):
    orig = b"\x00\x7E\x01\x7D\x02\x11\x03\x13\x04\x18\x05\x1a\x06"
    stuff = (
        b"\x00\x7D\x5E\x01\x7D\x5D\x02\x7D\x31\x03\x7D\x33\x04\x7D\x38\x05\x7D\x3a\x06"
    )
    assert gw._unstuff(stuff) == orig


def test_rst(gw):
    assert gw._rst_frame() == b"\x1a\xc0\x38\xbc\x7e"


def test_data_frame(gw):
    expected = b"\x42\x21\xa8\x54\x2a"
    assert gw._data_frame(b"\x00\x00\x00\x00\x00", 0, False)[1:-3] == expected


def test_cancel_received(gw):
    gw.rst_frame_received = MagicMock()
    gw.data_received(b"garbage")
    gw.data_received(b"\x1a\xc0\x38\xbc\x7e")
    assert gw.rst_frame_received.call_count == 1
    assert gw._buffer == b""


def test_substitute_received(gw):
    gw.rst_frame_received = MagicMock()
    gw.data_received(b"garbage")
    gw.data_received(b"\x18\x38\xbc\x7epart")
    gw.data_received(b"ial")
    gw.rst_frame_received.assert_not_called()
    assert gw._buffer == b"partial"


def test_partial_data_received(gw):
    gw.write = MagicMock()
    gw.data_received(b"\x54\x79\xa1\xb0")
    gw.data_received(b"\x50\xf2\x6e\x7e")
    assert gw.write.call_count == 1
    assert gw._application.frame_received.call_count == 1


def test_crc_error(gw):
    gw.write = MagicMock()
    gw.data_received(b"L\xa1\x8e\x03\xcd\x07\xb9Y\xfbG%\xae\xbd~")
    assert gw.write.call_count == 1
    assert gw._application.frame_received.call_count == 0


def test_crc_error_and_valid_frame(gw):
    gw.write = MagicMock()
    gw.data_received(
        b"L\xa1\x8e\x03\xcd\x07\xb9Y\xfbG%\xae\xbd~\x54\x79\xa1\xb0\x50\xf2\x6e\x7e"
    )
    assert gw.write.call_count == 2
    assert gw._application.frame_received.call_count == 1


def test_data_frame_received(gw):
    gw.write = MagicMock()
    gw.data_received(b"\x54\x79\xa1\xb0\x50\xf2\x6e\x7e")
    assert gw.write.call_count == 1
    assert gw._application.frame_received.call_count == 1


def test_ack_frame_received(gw):
    gw.data_received(b"\x86\x10\xbe\x7e")


def test_nak_frame_received(gw):
    gw.frame_received(bytes([0b10100000]))


def test_rst_frame_received(gw):
    gw.data_received(b"garbage\x1a\xc0\x38\xbc\x7e")


def test_rstack_frame_received(gw):
    gw._reset_future = MagicMock()
    gw._reset_future.done = MagicMock(return_value=False)
    gw.data_received(b"\xc1\x02\x0b\nR\x7e")
    assert gw._reset_future.done.call_count == 1
    assert gw._reset_future.set_result.call_count == 1


def test_wrong_rstack_frame_received(gw):
    gw._reset_future = MagicMock()
    gw.data_received(b"\xc1\x02\x01\xab\x18\x7e")
    assert gw._reset_future.set_result.call_count == 0


def test_error_rstack_frame_received(gw):
    gw._reset_future = MagicMock()
    gw.data_received(b"\xc1\x02\x81\x3a\x90\x7e")
    assert gw._reset_future.set_result.call_count == 0


def test_rstack_frame_received_nofut(gw):
    gw.data_received(b"\xc1\x02\x0b\nR\x7e")


def test_rstack_frame_received_out_of_order(gw):
    gw._reset_future = MagicMock()
    gw._reset_future.done = MagicMock(return_value=True)
    gw.data_received(b"\xc1\x02\x0b\nR\x7e")
    assert gw._reset_future.done.call_count == 1
    assert gw._reset_future.set_result.call_count == 0


def test_error_frame_received(gw):
    from bellows.types import NcpResetCode

    gw.frame_received(b"\xc2\x02\x03\xd2\x0a\x7e")
    efs = gw._application.enter_failed_state
    assert efs.call_count == 1
    assert efs.call_args[0][0] == NcpResetCode.RESET_WATCHDOG


def test_unknown_frame_received(gw):
    gw.frame_received(bytes([0b11011111]))


def test_close(gw):
    gw.close()
    assert gw._transport.close.call_count == 1


async def test_reset(gw):
    gw._sendq.put_nowait(sentinel.queue_item)
    fut = asyncio.Future()
    gw._pending = (sentinel.seq, fut)
    gw._transport.write.side_effect = lambda *args: gw._reset_future.set_result(
        sentinel.reset_result
    )
    reset_result = await gw.reset()

    assert gw._transport.write.call_count == 1
    assert gw._send_seq == 0
    assert gw._rec_seq == 0
    assert len(gw._buffer) == 0
    assert gw._sendq.empty()
    assert fut.done()
    assert gw._pending == (-1, None)

    assert reset_result is sentinel.reset_result


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


async def test_data(gw):
    loop = asyncio.get_running_loop()
    write_call_count = 0

    def mockwrite(data):
        nonlocal loop, write_call_count
        if data == b"\x10 @\xda}^Z~":
            loop.call_soon(gw._handle_nak, gw._pending[0])
        else:
            loop.call_soon(gw._handle_ack, (gw._pending[0] + 1) % 8)
        write_call_count += 1

    gw.write = mockwrite

    gw.data(b"foo")
    gw.data(b"bar")
    gw.data(b"baz")
    gw._sendq.put_nowait(gw.Terminator)

    await gw._send_loop()
    assert write_call_count == 4


def test_connection_lost_exc(gw):
    gw.connection_lost(sentinel.exception)

    conn_lost = gw._application.connection_lost
    assert conn_lost.call_count == 1
    assert conn_lost.call_args[0][0] is sentinel.exception


def test_connection_closed(gw):
    gw.connection_lost(None)

    assert gw._application.connection_lost.call_count == 0


def test_eof_received(gw):
    gw.eof_received()

    assert gw._application.connection_lost.call_count == 1


async def test_connection_lost_reset_error_propagation(monkeypatch):
    app = MagicMock()
    transport = MagicMock()

    async def mockconnect(loop, protocol_factory, **kwargs):
        protocol = protocol_factory()
        loop.call_soon(protocol.connection_made, transport)
        return None, protocol

    monkeypatch.setattr(serial_asyncio, "create_serial_connection", mockconnect)

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

    with pytest.raises(asyncio.CancelledError):
        await gw.reset()

    # Need to close to release thread
    gw.close()

    # Ensure all threads are cleaned up
    [t.join(1) for t in threading.enumerate() if "bellows" in t.name]
    threads = [t for t in threading.enumerate() if "bellows" in t.name]
    assert len(threads) == 0


async def test_wait_for_startup_reset(gw):
    loop = asyncio.get_running_loop()
    loop.call_later(0.01, gw.data_received, b"\xc1\x02\x0b\nR\x7e")

    assert gw._startup_reset_future is None
    await gw.wait_for_startup_reset()
    assert gw._startup_reset_future is None


async def test_wait_for_startup_reset_failure(gw):
    assert gw._startup_reset_future is None

    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(gw.wait_for_startup_reset(), 0.01)

    assert gw._startup_reset_future is None
