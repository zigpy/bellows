import asyncio
from asyncio import timeout as asyncio_timeout
import logging

import zigpy.config
import zigpy.serial

from bellows.ash import AshProtocol
from bellows.thread import EventLoopThread
import bellows.types as t

LOGGER = logging.getLogger(__name__)
RESET_TIMEOUT = 2.5
DISCONNECT_TIMEOUT = 5


class Gateway(zigpy.serial.SerialProtocol):
    def __init__(self, api):
        super().__init__()
        self._api = api

        self._reset_future = None
        self._startup_reset_future = None

    def _ensure_connected(self) -> None:
        if self._transport is None:
            raise ConnectionResetError("Connection has been closed")

    async def send_data(self, data: bytes) -> None:
        self._ensure_connected()
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
        self._ensure_connected()
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

        # A future may already be cancelled by a caller whose task has not yet resumed
        for future in (self._startup_reset_future, self._reset_future):
            if future is not None and not future.done():
                future.set_exception(reason)

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

        self._ensure_connected()
        self._transport.send_reset()
        self._reset_future = asyncio.get_running_loop().create_future()
        self._reset_future.add_done_callback(self._reset_cleanup)

        async with asyncio_timeout(RESET_TIMEOUT):
            return await self._reset_future


class ThreadedGateway:
    """Runs a `Gateway` on an `EventLoopThread` and bridges calls in both directions.

    The worker loop is stopped only from the application loop, either from `disconnect()`
    or when the connection is lost, so `_closed` is read and written on one loop and every
    call that passed the check was queued on the worker before the stop was.
    """

    def __init__(self, api, thread: EventLoopThread):
        self._api = api
        self._thread = thread
        self._loop = asyncio.get_running_loop()
        self._gateway = None
        self._closed = False

    async def connect(self, config) -> None:
        try:
            self._gateway = await self._thread.run_coroutine_threadsafe(
                _connect(config, self)
            )
        except BaseException:
            # Wait for the worker to exit so the port is released before the caller sees
            # the failure and tries to reconnect
            self._close()
            await self._thread.thread_complete
            raise

    # Called by the `Gateway` on the worker loop
    def frame_received(self, data: bytes) -> None:
        self._loop.call_soon_threadsafe(self._api.frame_received, data)

    def enter_failed_state(self, code: t.NcpResetCode) -> None:
        self._loop.call_soon_threadsafe(self._api.enter_failed_state, code)

    def connection_lost(self, exc: Exception | None) -> None:
        self._loop.call_soon_threadsafe(self._connection_lost, exc)

    # Called on the application loop
    def _connection_lost(self, exc: Exception | None) -> None:
        # The transport has already closed its file descriptor by the time it reports this
        self._close()
        self._api.connection_lost(exc)

    def _close(self) -> None:
        if self._closed:
            return

        self._closed = True
        self._thread.stop()

    async def _run(self, coro):
        if self._closed:
            coro.close()
            raise ConnectionResetError("Gateway has been disconnected")

        try:
            return await self._thread.run_coroutine_threadsafe(coro)
        except asyncio.CancelledError:
            # The worker cancelled the task while shutting down, not our caller
            if self._closed and not asyncio.current_task().cancelling():
                raise ConnectionResetError("Gateway has been disconnected") from None

            raise

    async def send_data(self, data: bytes) -> None:
        await self._run(self._gateway.send_data(data))

    async def reset(self):
        return await self._run(self._gateway.reset())

    async def wait_for_startup_reset(self) -> None:
        await self._run(self._gateway.wait_for_startup_reset())

    async def disconnect(self) -> None:
        if not self._closed:
            try:
                async with asyncio_timeout(DISCONNECT_TIMEOUT):
                    await self._run(self._gateway.disconnect())
            except TimeoutError:
                LOGGER.warning("Timed out waiting for the connection to close")
            finally:
                self._close()

        await self._thread.thread_complete


async def _connect(config, api):
    loop = asyncio.get_running_loop()

    gateway = Gateway(api)
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

    # `connection_made` arrives on a later loop iteration, so the port is open before we
    # are connected and must be closed if we are cancelled in between
    try:
        await gateway.wait_until_connected()
    except BaseException:
        transport.close()
        await transport.wait_closed()
        raise

    return gateway


async def connect(config, api, use_thread=True):
    if not use_thread:
        return await _connect(config, api)

    thread = EventLoopThread()
    await thread.start()

    gateway = ThreadedGateway(api, thread)
    await gateway.connect(config)

    return gateway
