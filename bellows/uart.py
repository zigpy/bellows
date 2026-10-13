import asyncio
from asyncio import timeout as asyncio_timeout
import logging
import urllib.parse

import zigpy.config
import zigpy.serial

from bellows.ash import AshProtocol
from bellows.thread import EventLoopThread, ThreadsafeProxy
import bellows.types as t

LOGGER = logging.getLogger(__name__)
RESET_TIMEOUT = 2.5

# An ESPHome port in this mode engages its tap, which ACKs frames on our behalf. The
# mode does not name a protocol: which one the tap speaks is the device's configuration.
ACKLESS_MODE = "protocol"

# URL schemes served by an ESPHome serial proxy, which is the only transport that can take
# the acknowledging off our hands
ESPHOME_SCHEMES = frozenset({"esphome", "esphome-hass"})


def is_esphome_url(path: str) -> bool:
    """Whether the path is served by an ESPHome serial proxy."""
    return urllib.parse.urlparse(path).scheme in ESPHOME_SCHEMES


class Gateway(zigpy.serial.SerialProtocol):
    def __init__(self, api, connection_done_future=None):
        super().__init__()
        self._api = api

        self._reset_future = None
        self._startup_reset_future = None
        self._connection_done_future = connection_done_future

    async def send_data(self, data: bytes) -> None:
        await self._transport.send_data(data)

    def data_received(self, data):
        """Callback when there is data received from the uart"""

        # We intentionally do not call `SerialProtocol.data_received`
        self._api.frame_received(data)

    def reset_received(self, code: t.NcpResetCode) -> None:
        """Reset acknowledgement frame receive handler"""
        LOGGER.debug("Received reset: %r", code)

        if self._reset_future and not self._reset_future.done():
            self._reset_future.set_result(True)
        elif self._startup_reset_future and not self._startup_reset_future.done():
            self._startup_reset_future.set_result(True)
        else:
            self._api.enter_failed_state(code)
            LOGGER.warning("Received an unexpected reset: %r", code)

    def error_received(self, code: t.NcpResetCode) -> None:
        """Error frame receive handler."""
        if self._reset_future is not None or self._startup_reset_future is not None:
            LOGGER.debug("Ignoring spurious error during reset: %r", code)
        else:
            self._api.enter_failed_state(code)

    async def wait_for_startup_reset(self) -> None:
        """Wait for the first reset frame on startup."""
        assert self._startup_reset_future is None
        self._startup_reset_future = asyncio.get_running_loop().create_future()

        try:
            await self._startup_reset_future
        finally:
            self._startup_reset_future = None

    def _reset_cleanup(self, future):
        """Delete reset future."""
        self._reset_future = None

    def connection_lost(self, exc):
        """Port was closed unexpectedly."""
        super().connection_lost(exc)

        LOGGER.debug("Connection lost: %r", exc)
        reason = exc or ConnectionResetError("Remote server closed connection")

        # XXX: The startup reset future must be resolved with an error *before* the
        # "connection done" future is completed: the secondary thread has an attached
        # callback to stop itself, which will cause the a future to propagate a
        # `CancelledError` into the active event loop, breaking everything!
        if self._startup_reset_future:
            self._startup_reset_future.set_exception(reason)

        if self._connection_done_future:
            self._connection_done_future.set_result(exc)
            self._connection_done_future = None

        if self._reset_future:
            self._reset_future.set_exception(reason)
            self._reset_future = None

        self._api.connection_lost(exc)

    async def reset(self):
        """Send a reset frame and init internal state."""
        LOGGER.debug("Resetting ASH")
        if self._reset_future is not None:
            LOGGER.error(
                "received new reset request while an existing one is in progress"
            )
            return await self._reset_future

        self._transport.send_reset()
        self._reset_future = asyncio.get_event_loop().create_future()
        self._reset_future.add_done_callback(self._reset_cleanup)

        async with asyncio_timeout(RESET_TIMEOUT):
            return await self._reset_future


async def _connect(config, api):
    loop = asyncio.get_event_loop()

    connection_done_future = loop.create_future()

    path = config[zigpy.config.CONF_DEVICE_PATH]

    gateway = Gateway(api, connection_done_future)
    # serialx opens an ESPHome port in the mode we ask for or raises, so whether the tap
    # acknowledges for us is known before the first frame arrives
    protocol = AshProtocol(gateway, suppress_acks=is_esphome_url(path))

    flow_control = config[zigpy.config.CONF_DEVICE_FLOW_CONTROL]

    extra_kwargs = {}

    if is_esphome_url(path):
        extra_kwargs["mode"] = ACKLESS_MODE

    transport, _ = await zigpy.serial.create_serial_connection(
        loop,
        lambda: protocol,
        url=path,
        baudrate=config[zigpy.config.CONF_DEVICE_BAUDRATE],
        xonxoff=flow_control in (None, "software"),
        rtscts=flow_control == "hardware",
        **extra_kwargs,
    )

    if is_esphome_url(path):
        LOGGER.debug(
            "Port acknowledges NCP frames on our behalf, suppressing our own ACKs"
        )

    await gateway.wait_until_connected()

    thread_safe_protocol = ThreadsafeProxy(gateway, loop)
    return thread_safe_protocol, connection_done_future


async def connect(config, api, use_thread=True):
    if use_thread:
        api = ThreadsafeProxy(api, asyncio.get_event_loop())
        thread = EventLoopThread()
        await thread.start()
        try:
            protocol, connection_done = await thread.run_coroutine_threadsafe(
                _connect(config, api)
            )
        except Exception:
            thread.force_stop()
            raise
        connection_done.add_done_callback(lambda _: thread.force_stop())
    else:
        protocol, _ = await _connect(config, api)
    return protocol
