import logging


LOGGER = logging.getLogger(__name__)


class ListenableMixin:
    def add_listener(self, listener):
        id_ = hash(listener)
        while id_ in self._listeners:
            id_ += 1
        self._listeners[id_] = listener
        return id_

    def listener_event(self, method_name, *args):
        for listener in self._listeners.values():
            try:
                method = getattr(listener, method_name)
                method(*args)
            except Exception as e:
                LOGGER.warning("Error calling listener.%s: %s", method_name, e)


class LocalLogMixin:
    def debug(self, msg, *args):
        return self.log(logging.DEBUG, msg, *args)

    def info(self, msg, *args):
        return self.log(logging.INFO, msg, *args)

    def warn(self, msg, *args):
        return self.log(logging.WARNING, msg, *args)

    def error(self, msg, *args):
        return self.log(logging.ERROR, msg, *args)

