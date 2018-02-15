import asyncio
import binascii
import logging
import serial_asyncio
import serial

import bellows.types as t


LOGGER = logging.getLogger(__name__)


class Gateway(asyncio.Protocol):
    FLAG = b'\x7E'  # Marks end of frame
    ESCAPE = b'\x7D'
    XON = b'\x11'  # Resume transmission
    XOFF = b'\x13'  # Stop transmission
    SUBSTITUTE = b'\x18'
    CANCEL = b'\x1A'  # Terminates a frame in progress
    STUFF = 0x20
    RANDOMIZE_START = 0x42
    RANDOMIZE_SEQ = 0xB8

    RESERVED = FLAG + ESCAPE + XON + XOFF + SUBSTITUTE + CANCEL

    class Terminator:
        pass

    def __init__(self, application, connected_future=None):
        self._send_seq = 0
        self._rec_seq = 0
        self._buffer = b''
        self._application = application
        self._reset_future = None
        self._connected_future = connected_future
        self._sendq = asyncio.Queue()
        self._pending = (-1, None)

    def connection_made(self, transport):
        """Callback when the uart is connected"""
        self._transport = transport
        if self._connected_future is not None:
            self._connected_future.set_result(True)
            asyncio.async(self._send_task())

    def data_received(self, data):
        """Callback when there is data received from the uart"""
        # TODO: Fix this handling for multiple instances of the characters
        # If a Cancel Byte or Substitute Byte is received, the bytes received
        # so far are discarded. In the case of a Substitute Byte, subsequent
        # bytes will also be discarded until the next Flag Byte.
        if self.CANCEL in data:
            self._buffer = b''
            data = data[data.rfind(self.CANCEL) + 1:]
        if self.SUBSTITUTE in data:
            self._buffer = b''
            data = data[data.find(self.FLAG) + 1:]

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
            return self._unstuff(data[:place + 1]), data[place + 1:]
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
        try:
            code = t.NcpResetCode(data[2])
        except ValueError:
            code = t.NcpResetCode.ERROR_UNKNOWN_EM3XX_ERROR

        LOGGER.debug("RSTACK Version: %d Reason: %s frame: %s", data[1], code.name, binascii.hexlify(data))
        # Only handle the frame, if it is a reply to our reset request
        if code is not t.NcpResetCode.RESET_SOFTWARE:
            return

        if self._reset_future is None:
            LOGGER.warn("Reset future is None")
            return

        self._reset_future.set_result(True)

    def error_frame_received(self, data):
        """Error frame receive handler"""
        LOGGER.debug("Error frame: %s", binascii.hexlify(data))

    def write(self, data):
        """Send data to the uart"""
        LOGGER.debug("Sending: %s", binascii.hexlify(data))
        self._transport.write(data)

    def close(self):
        self._sendq.put_nowait(self.Terminator)
        self._transport.close()

    def reset(self):
        """Sends a reset frame"""
        # TODO: It'd be nice to delete self._reset_future.
        if self._reset_future is not None:
            raise TypeError("reset can only be called on a new connection")

        self.write(self._rst_frame())
        self._reset_future = asyncio.Future()
        return self._reset_future

    @asyncio.coroutine
    def _send_task(self):
        """Send queue handler"""
        while True:
            item = yield from self._sendq.get()
            if item is self.Terminator:
                break
            data, seq = item
            success = False
            rxmit = 0
            while not success:
                self._pending = (seq, asyncio.Future())
                self.write(self._data_frame(data, seq, rxmit))
                rxmit = 1
                success = yield from self._pending[1]

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
        return self._frame(control, b'')

    def _rst_frame(self):
        """Construct a reset frame"""
        return self.CANCEL + self._frame(b'\xC0', b'')

    def _frame(self, control, data):
        """Construct a frame"""
        crc = binascii.crc_hqx(control + data, 0xffff)
        crc = bytes([crc >> 8, crc % 256])
        return self._stuff(control + data + crc) + self.FLAG

    def _randomize(self, s):
        """XOR s with a pseudo-random sequence for transmission

        Used only in data frames
        """
        rand = self.RANDOMIZE_START
        out = b''
        for c in s:
            out += bytes([c ^ rand])
            if rand % 2:
                rand = (rand >> 1) ^ self.RANDOMIZE_SEQ
            else:
                rand = rand >> 1
        return out

    def _stuff(self, s):
        """Byte stuff (escape) a string for transmission"""
        out = b''
        for c in s:
            if c in self.RESERVED:
                out += self.ESCAPE + bytes([c ^ self.STUFF])
            else:
                out += bytes([c])
        return out

    def _unstuff(self, s):
        """Unstuff (unescape) a string after receipt"""
        out = b''
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


@asyncio.coroutine
def connect(port, baudrate, application, loop=None):
    if loop is None:
        loop = asyncio.get_event_loop()

    connection_future = asyncio.Future()
    protocol = Gateway(application, connection_future)

    transport, protocol = yield from serial_asyncio.create_serial_connection(
        loop,
        lambda: protocol,
        url=port,
        baudrate=baudrate,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        xonxoff=True,
    )

    yield from connection_future

    return protocol
