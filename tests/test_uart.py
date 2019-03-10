import asyncio
from unittest import mock

import serial_asyncio
import pytest

from bellows import uart


def test_connect(monkeypatch):
    portmock = mock.MagicMock()
    appmock = mock.MagicMock()

    async def mockconnect(loop, protocol_factory, **kwargs):
        protocol = protocol_factory()
        loop.call_soon(protocol.connection_made, None)
        return None, protocol

    monkeypatch.setattr(
        serial_asyncio,
        'create_serial_connection',
        mockconnect,
    )
    loop = asyncio.get_event_loop()
    loop.run_until_complete(uart.connect(portmock, 115200, appmock))


@pytest.fixture
def gw():
    gw = uart.Gateway(mock.MagicMock())
    gw._transport = mock.MagicMock()
    return gw


def test_randomize(gw):
    assert gw._randomize(b'\x00\x00\x00\x00\x00') == b'\x42\x21\xa8\x54\x2a'
    assert gw._randomize(b'\x42\x21\xa8\x54\x2a') == b'\x00\x00\x00\x00\x00'


def test_stuff(gw):
    orig = b'\x00\x7E\x01\x7D\x02\x11\x03\x13\x04\x18\x05\x1a\x06'
    stuff = b'\x00\x7D\x5E\x01\x7D\x5D\x02\x7D\x31\x03\x7D\x33\x04\x7D\x38\x05\x7D\x3a\x06'
    assert gw._stuff(orig) == stuff


def test_unstuff(gw):
    orig = b'\x00\x7E\x01\x7D\x02\x11\x03\x13\x04\x18\x05\x1a\x06'
    stuff = b'\x00\x7D\x5E\x01\x7D\x5D\x02\x7D\x31\x03\x7D\x33\x04\x7D\x38\x05\x7D\x3a\x06'
    assert gw._unstuff(stuff) == orig


def test_rst(gw):
    assert gw._rst_frame() == b'\x1a\xc0\x38\xbc\x7e'


def test_data_frame(gw):
    expected = b'\x42\x21\xa8\x54\x2a'
    assert gw._data_frame(b'\x00\x00\x00\x00\x00', 0, False)[1:-3] == expected


def test_cancel_received(gw):
    gw.rst_frame_received = mock.MagicMock()
    gw.data_received(b'garbage')
    gw.data_received(b'\x1a\xc0\x38\xbc\x7e')
    assert gw.rst_frame_received.call_count == 1
    assert gw._buffer == b''


def test_substitute_received(gw):
    gw.rst_frame_received = mock.MagicMock()
    gw.data_received(b'garbage')
    gw.data_received(b'\x18\x38\xbc\x7epart')
    gw.data_received(b'ial')
    gw.rst_frame_received.assert_not_called()
    assert gw._buffer == b'partial'


def test_partial_data_received(gw):
    gw.write = mock.MagicMock()
    gw.data_received(b'\x54\x79\xa1\xb0')
    gw.data_received(b'\x50\xf2\x6e\x7e')
    assert gw.write.call_count == 1
    assert gw._application.frame_received.call_count == 1


def test_crc_error(gw):
    gw.write = mock.MagicMock()
    gw.data_received(b'L\xa1\x8e\x03\xcd\x07\xb9Y\xfbG%\xae\xbd~')
    assert gw.write.call_count == 1
    assert gw._application.frame_received.call_count == 0


def test_crc_error_and_valid_frame(gw):
    gw.write = mock.MagicMock()
    gw.data_received(b'L\xa1\x8e\x03\xcd\x07\xb9Y\xfbG%\xae\xbd~\x54\x79\xa1\xb0\x50\xf2\x6e\x7e')
    assert gw.write.call_count == 2
    assert gw._application.frame_received.call_count == 1


def test_data_frame_received(gw):
    gw.write = mock.MagicMock()
    gw.data_received(b'\x54\x79\xa1\xb0\x50\xf2\x6e\x7e')
    assert gw.write.call_count == 1
    assert gw._application.frame_received.call_count == 1


def test_ack_frame_received(gw):
    gw.data_received(b'\x86\x10\xbe\x7e')


def test_nak_frame_received(gw):
    gw.frame_received(bytes([0b10100000]))


def test_rst_frame_received(gw):
    gw.data_received(b'garbage\x1a\xc0\x38\xbc\x7e')


def test_rstack_frame_received(gw):
    gw._reset_future = mock.MagicMock()
    gw._reset_future.done = mock.MagicMock(return_value=False)
    gw.data_received(b'\xc1\x02\x0b\nR\x7e')
    assert gw._reset_future.done.call_count == 1
    assert gw._reset_future.set_result.call_count == 1


def test_wrong_rstack_frame_received(gw):
    gw._reset_future = mock.MagicMock()
    gw.data_received(b'\xc1\x02\x01\xab\x18\x7e')
    assert gw._reset_future.set_result.call_count == 0


def test_error_rstack_frame_received(gw):
    gw._reset_future = mock.MagicMock()
    gw.data_received(b'\xc1\x02\x81\x3a\x90\x7e')
    assert gw._reset_future.set_result.call_count == 0


def test_rstack_frame_received_nofut(gw):
    gw.data_received(b'\xc1\x02\x0b\nR\x7e')


def test_rstack_frame_received_out_of_order(gw):
    gw._reset_future = mock.MagicMock()
    gw._reset_future.done = mock.MagicMock(return_value=True)
    gw.data_received(b'\xc1\x02\x0b\nR\x7e')
    assert gw._reset_future.done.call_count == 1
    assert gw._reset_future.set_result.call_count == 0


def test_error_frame_received(gw):
    from bellows.types import NcpResetCode
    gw.frame_received(b'\xc2\x02\x03\xd2\x0a\x7e')
    efs = gw._application.enter_failed_state
    assert efs.call_count == 1
    assert efs.call_args[0][0] == NcpResetCode.RESET_WATCHDOG


def test_unknown_frame_received(gw):
    gw.frame_received(bytes([0b11011111]))


def test_close(gw):
    gw.close()
    assert gw._transport.close.call_count == 1


@pytest.mark.asyncio
async def test_reset(gw):
    gw._sendq.put_nowait(mock.sentinel.queue_item)
    fut = asyncio.Future()
    gw._pending = (mock.sentinel.seq, fut)
    gw._transport.write.side_effect = lambda *args: gw._reset_future.set_result(
        mock.sentinel.reset_result)
    ret = gw.reset()

    assert asyncio.iscoroutine(ret)
    assert gw._transport.write.call_count == 1
    assert gw._send_seq == 0
    assert gw._rec_seq == 0
    assert len(gw._buffer) == 0
    assert gw._sendq.empty()
    assert fut.done()
    assert gw._pending == (-1, None)

    reset_result = await ret
    assert reset_result is mock.sentinel.reset_result


@pytest.mark.asyncio
async def test_reset_timeout(gw, monkeypatch):
    monkeypatch.setattr(uart, 'RESET_TIMEOUT', 0.1)
    with pytest.raises(asyncio.TimeoutError):
        await gw.reset()


def test_reset_old(gw):
    gw._reset_future = mock.sentinel.future
    ret = gw.reset()
    assert ret == mock.sentinel.future
    gw._transport.write.assert_not_called()


def test_data(gw):
    write_call_count = 0

    def mockwrite(data):
        nonlocal loop, write_call_count
        if data == b'\x10 @\xda}^Z~':
            print(write_call_count)
            loop.call_soon(gw._handle_nak, gw._pending[0])
        else:
            loop.call_soon(gw._handle_ack, (gw._pending[0] + 1) % 8)
        write_call_count += 1

    gw.write = mockwrite

    gw.data(b'foo')
    gw.data(b'bar')
    gw.data(b'baz')
    gw._sendq.put_nowait(gw.Terminator)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(gw._send_task())
    assert write_call_count == 4


def test_connection_lost_exc(gw):
    gw.connection_lost(mock.sentinel.exception)

    conn_lost = gw._application.connection_lost
    assert conn_lost.call_count == 1
    assert conn_lost.call_args[0][0] is mock.sentinel.exception


def test_connection_closed(gw):
    gw.connection_lost(None)

    assert gw._application.connection_lost.call_count == 0
