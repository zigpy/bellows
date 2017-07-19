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


def _test_retry(exception, retry_exceptions, n):
    counter = 0

    @asyncio.coroutine
    def count():
        nonlocal counter
        counter += 1
        if counter <= n:
            exc = exception()
            exc._counter = counter
            raise exc

    loop = asyncio.get_event_loop()
    loop.run_until_complete(util.retry(count, retry_exceptions))
    return counter


def test_retry_no_retries():
    counter = _test_retry(Exception, Exception, 0)
    assert counter == 1


def test_retry_always():
    with pytest.raises(ValueError) as exc_info:
        _test_retry(ValueError, (IndexError, ValueError), 999)
    assert exc_info.value._counter == 3


def test_retry_once():
    counter = _test_retry(ValueError, ValueError, 1)
    assert counter == 2


def _test_retryable(exception, retry_exceptions, n, tries=3, delay=0.001):
    counter = 0

    @util.retryable(retry_exceptions)
    @asyncio.coroutine
    def count(x, y, z):
        assert x == y == z == 9
        nonlocal counter
        counter += 1
        if counter <= n:
            exc = exception()
            exc._counter = counter
            raise exc

    loop = asyncio.get_event_loop()
    loop.run_until_complete(count(9, 9, 9, tries=tries, delay=delay))
    return counter


def test_retryable_no_retry():
    counter = _test_retryable(Exception, Exception, 0, 0, 0)
    assert counter == 1


def test_retryable_exception_no_retry():
    with pytest.raises(Exception) as exc_info:
        _test_retryable(Exception, Exception, 1, 0, 0)
    assert exc_info.value._counter == 1


def test_retryable_no_retries():
    counter = _test_retryable(Exception, Exception, 0)
    assert counter == 1


def test_retryable_always():
    with pytest.raises(ValueError) as exc_info:
        _test_retryable(ValueError, (IndexError, ValueError), 999)
    assert exc_info.value._counter == 3


def test_retryable_once():
    counter = _test_retryable(ValueError, ValueError, 1)
    assert counter == 2
