import asyncio
from unittest import mock

import serial_asyncio
import pytest

from bellows import uart


def test_connect(monkeypatch):
    portmock = mock.MagicMock()
    appmock = mock.MagicMock()

    @asyncio.coroutine
    def mockconnect(loop, protocol_factory, **kwargs):
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
    gw.data_received(b'\xc1\x02\x0b\nR\x7e')
    assert gw._reset_future.set_result.call_count == 1


def test_wrong_rstack_frame_received(gw):
    gw._reset_future = mock.MagicMock()
    gw.data_received(b'\xc1\x02\x01\nR\x7e')
    assert gw._reset_future.set_result.call_count == 0


def test_error_rstack_frame_received(gw):
    gw._reset_future = mock.MagicMock()
    gw.data_received(b'\xc1\x02\x81\nR\x7e')
    assert gw._reset_future.set_result.call_count == 0


def test_rstack_frame_received_nofut(gw):
    gw.data_received(b'\xc1\x02\x0b\nR\x7e')


def test_error_frame_received(gw):
    gw.frame_received(bytes([0b11000010]))


def test_unknown_frame_received(gw):
    gw.frame_received(bytes([0b11011111]))


def test_close(gw):
    gw.close()
    assert gw._transport.close.call_count == 1


def test_reset(gw):
    gw.reset()
    assert gw._transport.write.call_count == 1


def test_reset_old(gw):
    with pytest.raises(Exception):
        gw._reset_future = mock.sentinel.future
        gw.reset()
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
