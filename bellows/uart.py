import asyncio
import binascii
import logging

import zigpy.serial

from bellows.config import (
    CONF_DEVICE_BAUDRATE,
    CONF_DEVICE_PATH,
    CONF_FLOW_CONTROL,
    CONF_FLOW_CONTROL_DEFAULT,
)
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
        self._send_seq = 0
        self._rec_seq = 0
        self._buffer = b""
        self._application = application
        self._reset_future = None
        self._startup_reset_future = None
        self._connected_future = connected_future
        self._sendq = asyncio.Queue()
        self._pending = (-1, None)
        self._connection_done_future = connection_done_future

        self._send_task = None

    def connection_made(self, transport):
        """Callback when the uart is connected"""
        self._transport = transport
        if self._connected_future is not None:
            self._connected_future.set_result(True)
            self._send_task = asyncio.create_task(self._send_loop())

    def data_received(self, data):
        """Callback when there is data received from the uart"""
        # TODO: Fix this handling for multiple instances of the characters
        # If a Cancel Byte or Substitute Byte is received, the bytes received
        # so far are discarded. In the case of a Substitute Byte, subsequent
        # bytes will also be discarded until the next Flag Byte.
        if self.CANCEL in data:
            self._buffer = b""
            data = data[data.rfind(self.CANCEL) + 1 :]
        if self.SUBSTITUTE in data:
            self._buffer = b""
            data = data[data.find(self.FLAG) + 1 :]

        self._buffer += data
        while self._buffer:
            frame, self._buffer = self._extract_frame(self._buffer)
            if frame is None:
                break
            self.frame_received(frame)

    def _extract_frame(self, data):
        """Extract a frame from the data buffer"""
        if self.FLAG in data:
            place = data.find(self.FLAG)
            frame = self._unstuff(data[: place + 1])
            rest = data[place + 1 :]
            crc = binascii.crc_hqx(frame[:-3], 0xFFFF)
            crc = bytes([crc >> 8, crc % 256])
            if crc != frame[-3:-1]:
                LOGGER.error(
                    "CRC error in frame %s (%s != %s)",
                    binascii.hexlify(frame),
                    binascii.hexlify(frame[-3:-1]),
                    binascii.hexlify(crc),
                )
                self.write(self._nak_frame())
                # Make sure that we also handle the next frame if it is already received
                return self._extract_frame(rest)

            return frame, rest
        return None, data

    def frame_received(self, data):
        """Frame receive handler"""
        if (data[0] & 0b10000000) == 0:
            self.data_frame_received(data)
        elif (data[0] & 0b11100000) == 0b10000000:
            self.ack_frame_received(data)
        elif (data[0] & 0b11100000) == 0b10100000:
            self.nak_frame_received(data)
        elif data[0] == 0b11000000:
            self.rst_frame_received(data)
        elif data[0] == 0b11000001:
            self.rstack_frame_received(data)
        elif data[0] == 0b11000010:
            self.error_frame_received(data)
        else:
            LOGGER.error("UNKNOWN FRAME RECEIVED: %r", data)  # TODO

    def data_frame_received(self, data):
        """Data frame receive handler"""
        LOGGER.debug("Data frame: %s", binascii.hexlify(data))
        seq = (data[0] & 0b01110000) >> 4
        self._rec_seq = (seq + 1) % 8
        self.write(self._ack_frame())
        self._handle_ack(data[0])
        self._application.frame_received(self._randomize(data[1:-3]))

    def ack_frame_received(self, data):
        """Acknowledgement frame receive handler"""
        LOGGER.debug("ACK frame: %s", binascii.hexlify(data))
        self._handle_ack(data[0])

    def nak_frame_received(self, data):
        """Negative acknowledgement frame receive handler"""
        LOGGER.debug("NAK frame: %s", binascii.hexlify(data))
        self._handle_nak(data[0])

    def rst_frame_received(self, data):
        """Reset frame handler"""
        LOGGER.debug("RST frame: %s", binascii.hexlify(data))

    def rstack_frame_received(self, data):
        """Reset acknowledgement frame receive handler"""
        self._send_seq = 0
        self._rec_seq = 0
        code, version = self._get_error_code(data)

        LOGGER.debug(
            "RSTACK Version: %d Reason: %s frame: %s",
            version,
            code.name,
            binascii.hexlify(data),
        )
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

    async def wait_for_startup_reset(self) -> None:
        """Wait for the first reset frame on startup."""
        assert self._startup_reset_future is None
        self._startup_reset_future = asyncio.get_running_loop().create_future()

        try:
            await self._startup_reset_future
        finally:
            self._startup_reset_future = None

    @staticmethod
    def _get_error_code(data):
        """Extracts error code from RSTACK or ERROR frames."""
        return t.NcpResetCode(data[2]), data[1]

    def error_frame_received(self, data):
        """Error frame receive handler."""
        error_code, version = self._get_error_code(data)
        LOGGER.debug(
            "Error code: %s, Version: %d, frame: %s",
            error_code.name,
            version,
            binascii.hexlify(data),
        )
        self._application.enter_failed_state(error_code)

    def write(self, data):
        """Send data to the uart"""
        LOGGER.debug("Sending: %s", binascii.hexlify(data))
        self._transport.write(data)

    def close(self):
        self._sendq.put_nowait(self.Terminator)
        self._transport.close()

    def _reset_cleanup(self, future):
        """Delete reset future."""
        self._reset_future = None

    def eof_received(self):
        """Server gracefully closed its side of the connection."""
        self.connection_lost(OSError("Server closed connection"))

    def connection_lost(self, exc):
        """Port was closed unexpectedly."""

        LOGGER.debug("Connection lost: %r", exc)

        if self._connection_done_future:
            self._connection_done_future.set_result(exc)
            self._connection_done_future = None

        if self._reset_future:
            self._reset_future.cancel()
            self._reset_future = None

        if self._send_task:
            self._send_task.cancel()
            self._send_task = None

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

        self._send_seq = 0
        self._rec_seq = 0
        self._buffer = b""
        while not self._sendq.empty():
            self._sendq.get_nowait()
        if self._pending[1]:
            self._pending[1].set_result(True)
        self._pending = (-1, None)

        self._reset_future = asyncio.get_event_loop().create_future()
        self._reset_future.add_done_callback(self._reset_cleanup)
        self.write(self._rst_frame())
        return await asyncio.wait_for(self._reset_future, timeout=RESET_TIMEOUT)

    async def _send_loop(self):
        """Send queue handler"""
        while True:
            item = await self._sendq.get()
            if item is self.Terminator:
                break
            data, seq = item
            success = False
            rxmit = 0
            while not success:
                self._pending = (seq, asyncio.get_event_loop().create_future())
                self.write(self._data_frame(data, seq, rxmit))
                rxmit = 1
                success = await self._pending[1]

    def _handle_ack(self, control):
        """Handle an acknowledgement frame"""
        ack = ((control & 0b00000111) - 1) % 8
        if ack == self._pending[0]:
            pending, self._pending = self._pending, (-1, None)
            pending[1].set_result(True)

    def _handle_nak(self, control):
        """Handle negative acknowledgment frame"""
        nak = control & 0b00000111
        if nak == self._pending[0]:
            self._pending[1].set_result(False)

    def data(self, data):
        """Send a data frame"""
        seq = self._send_seq
        self._send_seq = (seq + 1) % 8
        self._sendq.put_nowait((data, seq))

    def _data_frame(self, data, seq, rxmit):
        """Construct a data frame"""
        assert 0 <= seq <= 7
        assert 0 <= rxmit <= 1
        control = (seq << 4) | (rxmit << 3) | self._rec_seq
        return self._frame(bytes([control]), self._randomize(data))

    def _ack_frame(self):
        """Construct a acknowledgement frame"""
        assert 0 <= self._rec_seq < 8
        control = bytes([0b10000000 | (self._rec_seq & 0b00000111)])
        return self._frame(control, b"")

    def _nak_frame(self):
        """Construct a negative acknowledgement frame"""
        assert 0 <= self._rec_seq < 8
        control = bytes([0b10100000 | (self._rec_seq & 0b00000111)])
        return self._frame(control, b"")

    def _rst_frame(self):
        """Construct a reset frame"""
        return self.CANCEL + self._frame(b"\xC0", b"")

    def _frame(self, control, data):
        """Construct a frame"""
        crc = binascii.crc_hqx(control + data, 0xFFFF)
        crc = bytes([crc >> 8, crc % 256])
        return self._stuff(control + data + crc) + self.FLAG

    def _randomize(self, s):
        """XOR s with a pseudo-random sequence for transmission

        Used only in data frames
        """
        rand = self.RANDOMIZE_START
        out = b""
        for c in s:
            out += bytes([c ^ rand])
            if rand % 2:
                rand = (rand >> 1) ^ self.RANDOMIZE_SEQ
            else:
                rand = rand >> 1
        return out

    def _stuff(self, s):
        """Byte stuff (escape) a string for transmission"""
        out = b""
        for c in s:
            if c in self.RESERVED:
                out += self.ESCAPE + bytes([c ^ self.STUFF])
            else:
                out += bytes([c])
        return out

    def _unstuff(self, s):
        """Unstuff (unescape) a string after receipt"""
        out = b""
        escaped = False
        for c in s:
            if escaped:
                out += bytes([c ^ self.STUFF])
                escaped = False
            elif c in self.ESCAPE:
                escaped = True
            else:
                out += bytes([c])
        return out


async def _connect(config, application):
    loop = asyncio.get_event_loop()

    connection_future = loop.create_future()
    connection_done_future = loop.create_future()
    protocol = Gateway(application, connection_future, connection_done_future)

    if config[CONF_FLOW_CONTROL] == CONF_FLOW_CONTROL_DEFAULT:
        xon_xoff, rtscts = True, False
    else:
        xon_xoff, rtscts = False, True

    transport, protocol = await zigpy.serial.create_serial_connection(
        loop,
        lambda: protocol,
        url=config[CONF_DEVICE_PATH],
        baudrate=config[CONF_DEVICE_BAUDRATE],
        xonxoff=xon_xoff,
        rtscts=rtscts,
    )

    await connection_future

    thread_safe_protocol = ThreadsafeProxy(protocol, loop)
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
