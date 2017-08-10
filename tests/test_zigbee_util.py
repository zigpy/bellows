import asyncio
from unittest import mock

import pytest

from bellows.zigbee import util


class Listenable(util.ListenableMixin):
    def __init__(self):
        self._listeners = {}


def test_listenable():
    l = Listenable()
    listener = mock.MagicMock()
    l.add_listener(listener)
    l.add_listener(listener)

    broken_listener = mock.MagicMock()
    broken_listener.event.side_effect = Exception()
    l.add_listener(broken_listener)

    l.listener_event('event')
    assert listener.event.call_count == 2
    assert broken_listener.event.call_count == 1


class Logger(util.LocalLogMixin):
    log = mock.MagicMock()


def test_log():
    l = Logger()
    l.debug("Test debug")
    l.info("Test info")
    l.warn("Test warn")
    l.error("Test error")


def test_zha_security_end_device():
    util.zha_security(controller=False)


def test_zha_security_controller():
    util.zha_security(controller=True)


def _test_retry(exception, exceptions, n):
    counter = 0

    @util.retry(exceptions)
    @asyncio.coroutine
    def count():
        nonlocal counter
        counter += 1
        if counter <= n:
            exc = exception()
            exc._counter = counter
            raise exc

    loop = asyncio.get_event_loop()
    loop.run_until_complete(count())
    return counter


def test_retry_no_retries():
    counter = _test_retry(Exception, Exception, 0)
    assert counter == 1


def test_retry_always():
    with pytest.raises(ValueError) as exc_info:
        _test_retry(ValueError, (IndexError, ValueError), 999)
    print(exc_info.value)
    assert exc_info.value._counter == 3


def test_retry_once():
    counter = _test_retry(ValueError, ValueError, 1)
    assert counter == 2


def test_zigbee_security_hash():
    message = bytes([0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77, 0x88, 0x4A, 0xF7])
    key = util.aesMmoHash(message)
    assert key.contents == [0x41, 0x61, 0x8F, 0xC0, 0xC8, 0x3B, 0x0E, 0x14, 0xA5, 0x89, 0x95, 0x4B, 0x16, 0xE3, 0x14, 0x66]

    message = bytes([0x7A, 0x93, 0x97, 0x23, 0xA5, 0xC6, 0x39, 0xB2, 0x69, 0x16, 0x18, 0x02, 0x81, 0x9B])
    key = util.aesMmoHash(message)
    assert key.contents == [0xF9, 0x39, 0x03, 0x72, 0x16, 0x85, 0xFD, 0x32, 0x9D, 0x26, 0x84, 0x9B, 0x90, 0xF2, 0x95, 0x9A]

    message = bytes([0x83, 0xFE, 0xD3, 0x40, 0x7A, 0x93, 0x97, 0x23, 0xA5, 0xC6, 0x39, 0xB2, 0x69, 0x16, 0x18, 0x02, 0xAE, 0xBB])
    key = util.aesMmoHash(message)
    assert key.contents == [0x33, 0x3C, 0x23, 0x68, 0x60, 0x79, 0x46, 0x8E, 0xB2, 0x7B, 0xA2, 0x4B, 0xD9, 0xC7, 0xE5, 0x64]


def test_convert_install_code():
    message = bytes([0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77, 0x88, 0x4A, 0xF7])
    key = util.convertInstallCode(message)
    assert key.contents == [0x41, 0x61, 0x8F, 0xC0, 0xC8, 0x3B, 0x0E, 0x14, 0xA5, 0x89, 0x95, 0x4B, 0x16, 0xE3, 0x14, 0x66]


def test_fail_convert_install_code():
    key = util.convertInstallCode(bytes([]))
    assert key is None

    message = bytes([0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77, 0x88, 0xFF, 0xFF])
    key = util.convertInstallCode(message)
    assert key is None
