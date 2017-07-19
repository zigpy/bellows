import asyncio
import functools
import logging
import os

import bellows.types as t
from bellows.zigbee.exceptions import DeliveryError

LOGGER = logging.getLogger(__name__)


class ListenableMixin:
    def add_listener(self, listener):
        id_ = id(listener)
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


def zha_security(controller=False):
    empty_key_data = t.EmberKeyData()
    empty_key_data.contents = t.fixed_list(16, t.uint8_t)([t.uint8_t(0)] * 16)
    zha_key = t.EmberKeyData()
    zha_key.contents = t.fixed_list(16, t.uint8_t)(
        [t.uint8_t(c) for c in b'ZigBeeAlliance09']
    )

    isc = t.EmberInitialSecurityState()
    isc.bitmask = t.uint16_t(
        t.EmberInitialSecurityBitmask.HAVE_PRECONFIGURED_KEY |
        t.EmberInitialSecurityBitmask.REQUIRE_ENCRYPTED_KEY
    )
    isc.preconfiguredKey = zha_key
    isc.networkKey = empty_key_data
    isc.networkKeySequenceNumber = t.uint8_t(0)
    isc.preconfiguredTrustCenterEui64 = t.EmberEUI64(
        [t.uint8_t(0)] * 8
    )

    if controller:
        isc.bitmask |= (
            t.EmberInitialSecurityBitmask.TRUST_CENTER_GLOBAL_LINK_KEY |
            t.EmberInitialSecurityBitmask.HAVE_NETWORK_KEY
        )
        isc.bitmask = t.uint16_t(isc.bitmask)
        random_key = t.fixed_list(16, t.uint8_t)(
            [t.uint8_t(x) for x in os.urandom(16)]
        )
        isc.networkKey = random_key
    return isc


@asyncio.coroutine
def retry(func, retry_exceptions, tries=3, delay=0.1):
    """Retry a function in case of exception

    Only exceptions in `retry_exceptions` will be retried.
    """
    while True:
        try:
            r = yield from func()
            return r
        except retry_exceptions:
            if tries <= 1:
                raise
            tries -= 1
            yield from asyncio.sleep(delay)


def retryable(retry_exceptions, tries=1, delay=0.1):
    """Return a decorator which makes a function able to be retried

    This adds "tries" and "delay" keyword arguments to the function. Only
    exceptions in `retry_exceptions` will be retried.
    """
    def decorator(func):
        nonlocal tries, delay

        @functools.wraps(func)
        def wrapper(*args, tries=tries, delay=delay, **kwargs):
            if tries <= 1:
                return func(*args, **kwargs)
            return retry(
                functools.partial(func, *args, **kwargs),
                retry_exceptions,
                tries=tries,
                delay=delay,
            )
        return wrapper
    return decorator


retryable_request = retryable((DeliveryError, asyncio.TimeoutError))
