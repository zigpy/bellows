import asyncio
import logging
import sys

if sys.version_info[:2] < (3, 11):
    from async_timeout import timeout as asyncio_timeout  # pragma: no cover
else:
    from asyncio import timeout as asyncio_timeout  # pragma: no cover

import zigpy.config
import zigpy.serial

from bellows.ash import AshProtocol
from bellows.thread import EventLoopThread, ThreadsafeProxy
import bellows.types as t

LOGGER = logging.getLogger(__name__)
RESET_TIMEOUT = 5


class Gateway(asyncio.Protocol):
    FLAG = b"\x7E"  # Marks end of frame
    ESCAPE = b"\x7D"
    XON = b"\x11"  # Resume transmission
    XOFF = b"\x13"  # Stop transmission
    SUBSTITUTE = b"\x18"
    CANCEL = b"\x1A"  # Terminates a frame in progress
    STUFF = 0x20
    RANDOMIZE_START = 0x42
    RANDOMIZE_SEQ = 0xB8

    RESERVED = FLAG + ESCAPE + XON + XOFF + SUBSTITUTE + CANCEL

    class Terminator:
        pass

    def __init__(self, application, connected_future=None, connection_done_future=None):
        self._application = application

        self._reset_future = None
        self._startup_reset_future = None
        self._connected_future = connected_future
        self._connection_done_future = connection_done_future

        self._transport = None

    def close(self):
        self._transport.close()

    def connection_made(self, transport):
        """Callback when the uart is connected"""
        self._transport = transport
        if self._connected_future is not None:
            self._connected_future.set_result(True)

    async def send_data(self, data: bytes) -> None:
        await self._transport.send_data(data)

    def data_received(self, data):
        """Callback when there is data received from the uart"""
        self._application.frame_received(data)

    def reset_received(self, code):
        """Reset acknowledgement frame receive handler"""
        # not a reset we've requested. Signal application reset
        if code is not t.NcpResetCode.RESET_SOFTWARE:
            self._application.enter_failed_state(code)
            return

        if self._reset_future and not self._reset_future.done():
            self._reset_future.set_result(True)
        elif self._startup_reset_future and not self._startup_reset_future.done():
            self._startup_reset_future.set_result(True)
        else:
            LOGGER.warning("Received an unexpected reset: %r", code)

    def error_received(self, code):
        """Error frame receive handler."""
        self._application.enter_failed_state(code)

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

    def eof_received(self):
        """Server gracefully closed its side of the connection."""
        self.connection_lost(ConnectionResetError("Remote server closed connection"))

    def connection_lost(self, exc):
        """Port was closed unexpectedly."""

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

        if exc is None:
            LOGGER.debug("Closed serial connection")
            return

        LOGGER.error("Lost serial connection: %r", exc)
        self._application.connection_lost(exc)

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


async def _connect(config, application):
    loop = asyncio.get_event_loop()

    connection_future = loop.create_future()
    connection_done_future = loop.create_future()

    gateway = Gateway(application, connection_future, connection_done_future)
    protocol = AshProtocol(gateway)

    if config[zigpy.config.CONF_DEVICE_FLOW_CONTROL] is None:
        xon_xoff, rtscts = True, False
    else:
        xon_xoff, rtscts = False, True

    transport, _ = await zigpy.serial.create_serial_connection(
        loop,
        lambda: protocol,
        url=config[zigpy.config.CONF_DEVICE_PATH],
        baudrate=config[zigpy.config.CONF_DEVICE_BAUDRATE],
        xonxoff=xon_xoff,
        rtscts=rtscts,
    )

    await connection_future

    thread_safe_protocol = ThreadsafeProxy(gateway, loop)
    return thread_safe_protocol, connection_done_future


async def connect(config, application, use_thread=True):
    if use_thread:
        application = ThreadsafeProxy(application, asyncio.get_event_loop())
        thread = EventLoopThread()
        await thread.start()
        try:
            protocol, connection_done = await thread.run_coroutine_threadsafe(
                _connect(config, application)
            )
        except Exception:
            thread.force_stop()
            raise
        connection_done.add_done_callback(lambda _: thread.force_stop())
    else:
        protocol, _ = await _connect(config, application)
    return protocol
