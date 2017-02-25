from unittest import mock

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
