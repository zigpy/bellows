from __future__ import annotations

import asyncio
from asyncio import timeout as asyncio_timeout
from concurrent.futures import ThreadPoolExecutor
import dataclasses
from io import BytesIO
import itertools
import logging
from logging import LogRecord
from logging.handlers import QueueHandler
import multiprocessing
import pickle
import socket
import struct

import zigpy.serial
import zigpy.types

from bellows.ash import AshProtocol, NcpFailure, NcpResetCode

LOGGER = logging.getLogger(__name__)
RESET_TIMEOUT = 2.5

# The worker process copies these loggers' effective levels from the application when it
# starts, and forwards every record that passes them
WORKER_LOGGERS = (
    "",
    "asyncio",
    "bellows.ash",
    "bellows.uart",
    "zigpy.serial",
    "serialx",
)


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

    def reset_received(self, code: NcpResetCode) -> None:
        """Reset acknowledgement frame receive handler"""
        LOGGER.debug("Received reset: %r", code)

        if self._reset_future and not self._reset_future.done():
            self._reset_future.set_result(True)
        elif self._startup_reset_future and not self._startup_reset_future.done():
            self._startup_reset_future.set_result(True)
        else:
            self._api.enter_failed_state(code)
            LOGGER.warning("Received an unexpected reset: %r", code)

    def error_received(self, code: NcpResetCode) -> None:
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


# Messages between the application and the worker process. Every message is a pickled
# dataclass behind a 32-bit length prefix.


# Application -> worker. Requests carry an id that their reply repeats.
@dataclasses.dataclass(frozen=True)
class SendData:
    id: int
    data: bytes


@dataclasses.dataclass(frozen=True)
class Reset:
    id: int


@dataclasses.dataclass(frozen=True)
class WaitForStartupReset:
    id: int


@dataclasses.dataclass(frozen=True)
class Cancel:
    id: int


# Worker -> application
@dataclasses.dataclass(frozen=True)
class Connected:
    pass


@dataclasses.dataclass(frozen=True)
class ConnectFailed:
    exc: Exception


@dataclasses.dataclass(frozen=True)
class Done:
    id: int
    result: object


@dataclasses.dataclass(frozen=True)
class Failed:
    id: int
    exc: Exception


@dataclasses.dataclass(frozen=True)
class FrameReceived:
    data: bytes


@dataclasses.dataclass(frozen=True)
class FailedState:
    code: NcpResetCode


@dataclasses.dataclass(frozen=True)
class ConnectionLost:
    exc: Exception | None


@dataclasses.dataclass(frozen=True)
class Log:
    record: LogRecord


# Everything that may cross the boundary. Pickle refuses to send or receive any other
# class, so the protocol's vocabulary is this list and not whatever an object graph holds.
_ALLOWED_CLASSES = frozenset(
    {
        SendData,
        Reset,
        WaitForStartupReset,
        Cancel,
        Connected,
        ConnectFailed,
        Done,
        Failed,
        FrameReceived,
        FailedState,
        ConnectionLost,
        Log,
        LogRecord,
        NcpResetCode,
        # `NcpResetCode` pickles its value as this
        zigpy.types.uint8_t,
        # The exceptions ASH, the gateway and the serial transport raise
        NcpFailure,
        AssertionError,
        RuntimeError,
        TimeoutError,
        OSError,
        BlockingIOError,
        BrokenPipeError,
        ConnectionAbortedError,
        ConnectionError,
        ConnectionRefusedError,
        ConnectionResetError,
        FileNotFoundError,
        IsADirectoryError,
        NotADirectoryError,
        PermissionError,
    }
)
_ALLOWED_GLOBALS = {(cls.__module__, cls.__qualname__): cls for cls in _ALLOWED_CLASSES}


class _Pickler(pickle.Pickler):
    def reducer_override(self, obj):
        # Called for every instance and class in the graph, not for primitives
        cls = obj if isinstance(obj, type) else type(obj)

        if cls not in _ALLOWED_CLASSES:
            raise pickle.PicklingError(f"{cls!r} may not cross the process boundary")

        return NotImplemented


class _Unpickler(pickle.Unpickler):
    def find_class(self, module, name):
        if (module, name) not in _ALLOWED_GLOBALS:
            raise pickle.UnpicklingError(
                f"{module}.{name} may not cross the process boundary"
            )

        return _ALLOWED_GLOBALS[module, name]


def _dumps(message) -> bytes:
    buffer = BytesIO()
    _Pickler(buffer).dump(message)
    return buffer.getvalue()


def _portable(exc: BaseException | None) -> Exception | None:
    """The exception itself if the protocol can carry it, otherwise one describing it."""
    try:
        _dumps(exc)
    except pickle.PicklingError:
        return RuntimeError(f"{type(exc).__qualname__}: {exc}")

    return exc


def _write(writer: asyncio.StreamWriter, message) -> None:
    payload = _dumps(message)
    writer.write(struct.pack("<I", len(payload)) + payload)


async def _read(reader: asyncio.StreamReader):
    """Read one message, or `None` once the other side has closed its end."""
    try:
        header = await reader.readexactly(4)
    except asyncio.IncompleteReadError as exc:
        if exc.partial:
            raise

        return None

    (length,) = struct.unpack("<I", header)
    return _Unpickler(BytesIO(await reader.readexactly(length))).load()


class _ForwardingHandler(QueueHandler):
    """Ships the worker's log records to the application process."""

    def __init__(self, loop: asyncio.AbstractEventLoop, writer: asyncio.StreamWriter):
        super().__init__(queue=None)
        self._loop = loop
        self._writer = writer

    def prepare(self, record: LogRecord) -> LogRecord:
        # The message is formatted and `args` is cleared; `()` is what a record without
        # arguments normally carries
        record = super().prepare(record)
        record.args = ()
        return record

    def enqueue(self, record: LogRecord) -> None:
        # Records also come from executor threads, the writer is only used on the loop
        self._loop.call_soon_threadsafe(_write, self._writer, Log(record))


class _Worker:
    """The worker process's side: owns the `Gateway` and serves requests for it."""

    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        self._reader = reader
        self._writer = writer
        self._gateway = None
        self._requests: dict[int, asyncio.Task] = {}

    async def run(self, path: str, baudrate: int, flow_control: str | None) -> None:
        connect = asyncio.ensure_future(self._connect(path, baudrate, flow_control))

        try:
            # Until the application closes its end, which it may do while connecting
            await self._read_messages()
        finally:
            connect.cancel()

            for task in self._requests.values():
                task.cancel()

            await asyncio.gather(
                connect, *self._requests.values(), return_exceptions=True
            )

            if self._gateway is not None:
                await self._gateway.disconnect()

    async def _connect(self, path: str, baudrate: int, flow_control: str | None):
        try:
            self._gateway = await _connect(
                self, path=path, baudrate=baudrate, flow_control=flow_control
            )
        except Exception as exc:
            _write(self._writer, ConnectFailed(_portable(exc)))
        else:
            _write(self._writer, Connected())

    async def _read_messages(self) -> None:
        while (message := await _read(self._reader)) is not None:
            match message:
                case SendData(id=id, data=data):
                    self._start(id, self._gateway.send_data(data))
                case Reset(id=id):
                    self._start(id, self._gateway.reset())
                case WaitForStartupReset(id=id):
                    self._start(id, self._gateway.wait_for_startup_reset())
                case Cancel(id=id):
                    # The request may have finished just before the cancel arrived
                    if id in self._requests:
                        self._requests[id].cancel()
                case _:
                    raise TypeError(f"Unexpected message: {message!r}")

    def _start(self, id: int, coro) -> None:
        task = asyncio.ensure_future(coro)
        self._requests[id] = task
        task.add_done_callback(lambda task: self._finish(id, task))

    def _finish(self, id: int, task: asyncio.Task) -> None:
        del self._requests[id]

        if task.cancelled():
            # The application already gave up on it
            return

        if task.exception() is not None:
            _write(self._writer, Failed(id, _portable(task.exception())))
        else:
            _write(self._writer, Done(id, task.result()))

    # Called by the `Gateway`
    def frame_received(self, data: bytes) -> None:
        _write(self._writer, FrameReceived(data))

    def enter_failed_state(self, code: NcpResetCode) -> None:
        _write(self._writer, FailedState(code))

    def connection_lost(self, exc: Exception | None) -> None:
        _write(self._writer, ConnectionLost(_portable(exc)))


async def _run_worker(
    sock: socket.socket,
    path: str,
    baudrate: int,
    flow_control: str | None,
    log_levels: tuple[tuple[str, int], ...],
) -> None:
    loop = asyncio.get_running_loop()
    reader, writer = await asyncio.open_connection(sock=sock)

    for name, level in log_levels:
        logging.getLogger(name).setLevel(level)

    handler = _ForwardingHandler(loop, writer)
    logging.getLogger().addHandler(handler)

    try:
        await _Worker(reader, writer).run(path, baudrate, flow_control)
    finally:
        logging.getLogger().removeHandler(handler)
        writer.close()
        await writer.wait_closed()


def _worker_main(sock: socket.socket, *args) -> None:
    """Entry point in the worker process."""
    asyncio.run(_run_worker(sock, *args))


def _launch_worker(loop: asyncio.AbstractEventLoop, sock: socket.socket, *args):
    """Start the worker process. Returns it and a future that resolves when it exits."""
    # `fork` would copy the application's threads and locks. The socket is duplicated
    # into the child, nothing else is inherited.
    process = multiprocessing.get_context("spawn").Process(
        target=_worker_main, args=(sock, *args), name=__name__, daemon=True
    )
    process.start()
    sock.close()

    executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix=__name__)
    future = loop.run_in_executor(executor, process.join)
    executor.shutdown(wait=False)

    return process, future


class IsolatedGateway:
    """Runs a `Gateway` on an event loop in its own process and bridges the two.

    The application's garbage collector stops every thread sharing its GIL, while ASH
    acknowledgements have a deadline. The worker process has its own.

    The worker owns the gateway and exits only once the application closes its end of
    the socket, so every request that passed the `_closed` check reached it before the
    close did.
    """

    def __init__(self, api):
        self._api = api
        self._loop = asyncio.get_running_loop()
        self._process = None
        self._worker_complete = None
        self._writer = None
        self._messages = None
        self._connected = self._loop.create_future()
        self._requests: dict[int, asyncio.Future] = {}
        self._ids = itertools.count()
        self._closed = False
        self._lost_exc = None

    async def connect(
        self, *, path: str, baudrate: int, flow_control: str | None
    ) -> None:
        ours, theirs = socket.socketpair()
        log_levels = tuple(
            (name, logging.getLogger(name).getEffectiveLevel())
            for name in WORKER_LOGGERS
        )

        self._process, self._worker_complete = _launch_worker(
            self._loop, theirs, path, baudrate, flow_control, log_levels
        )

        reader, self._writer = await asyncio.open_connection(sock=ours)
        self._messages = asyncio.ensure_future(self._read_messages(reader))

        try:
            await asyncio.shield(self._connected)
        except BaseException:
            # Wait for the worker to exit so the port is released before the caller sees
            # the failure and tries to reconnect
            self._connected.cancel()
            self._close()
            await self._finish()
            raise

    async def _read_messages(self, reader: asyncio.StreamReader) -> None:
        while (message := await _read(reader)) is not None:
            match message:
                case Connected():
                    if not self._connected.done():
                        self._connected.set_result(None)
                case ConnectFailed(exc=exc):
                    if not self._connected.done():
                        self._connected.set_exception(exc)
                case Done(id=id, result=result):
                    if id in self._requests:
                        self._requests.pop(id).set_result(result)
                case Failed(id=id, exc=exc):
                    if id in self._requests:
                        self._requests.pop(id).set_exception(exc)
                case FrameReceived(data=data):
                    self._api.frame_received(data)
                case FailedState(code=code):
                    self._api.enter_failed_state(code)
                case ConnectionLost(exc=exc):
                    self._connection_lost(exc)
                case Log(record=record):
                    logging.getLogger(record.name).handle(record)
                case _:
                    raise TypeError(f"Unexpected message: {message!r}")

        # The worker has exited, which is expected only after we closed our end
        crashed = not self._closed
        self._closed = True

        if not self._connected.done():
            self._connected.set_exception(
                ConnectionResetError("Worker exited before connecting")
            )
        elif crashed:
            self._connection_lost(ConnectionResetError("Worker exited unexpectedly"))

        # Requests the worker cancelled while shutting down, instead of answering
        for future in self._requests.values():
            future.set_exception(self._disconnected_error())

        self._requests.clear()

    def _connection_lost(self, exc: Exception | None) -> None:
        # The transport has already closed its file descriptor by the time it reports this
        self._lost_exc = exc
        self._close()
        self._api.connection_lost(exc)

    def _close(self) -> None:
        if self._closed:
            return

        self._closed = True
        self._writer.write_eof()

    def _disconnected_error(self) -> ConnectionResetError:
        # Chain the transport's own error, since every call made after the loss fails here
        exc = ConnectionResetError("Gateway has been disconnected")
        exc.__cause__ = self._lost_exc
        return exc

    async def _request(self, message_type, *args):
        if self._closed:
            raise self._disconnected_error()

        id = next(self._ids)
        future = self._loop.create_future()
        self._requests[id] = future
        _write(self._writer, message_type(id, *args))

        try:
            return await future
        except asyncio.CancelledError:
            # Our caller gave up; a reply arriving later is dropped
            del self._requests[id]

            if not self._closed:
                _write(self._writer, Cancel(id))

            raise

    async def send_data(self, data: bytes) -> None:
        await self._request(SendData, data)

    async def reset(self):
        return await self._request(Reset)

    async def wait_for_startup_reset(self) -> None:
        await self._request(WaitForStartupReset)

    async def disconnect(self) -> None:
        self._close()
        await self._finish()

    async def _finish(self) -> None:
        await self._worker_complete
        await self._messages
        self._writer.close()

        if self._process is not None:
            if self._process.exitcode:
                LOGGER.error("Worker process exited with %s", self._process.exitcode)

            self._process.close()
            self._process = None


async def _connect(api, *, path: str, baudrate: int, flow_control: str | None):
    loop = asyncio.get_running_loop()

    gateway = Gateway(api)
    protocol = AshProtocol(gateway)

    transport, _ = await zigpy.serial.create_serial_connection(
        loop,
        lambda: protocol,
        url=path,
        baudrate=baudrate,
        xonxoff=flow_control in (None, "software"),
        rtscts=flow_control == "hardware",
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


async def connect(
    api,
    *,
    path: str,
    baudrate: int,
    flow_control: str | None,
    isolated: bool = True,
    use_thread: bool | None = None,
):
    # Backwards compatibility
    if use_thread is not None:
        isolated = use_thread

    if not isolated:
        return await _connect(
            api, path=path, baudrate=baudrate, flow_control=flow_control
        )

    gateway = IsolatedGateway(api)
    await gateway.connect(path=path, baudrate=baudrate, flow_control=flow_control)

    return gateway
