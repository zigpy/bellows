import asyncio
import binascii
import logging
import serial_asyncio
import serial


LOGGER = logging.getLogger(__name__)


class Gateway(asyncio.Protocol):
    FLAG = b'\x7E'  # Marks end of frame
    ESCAPE = b'\x7D'
    XON = b'\x11'  # Resume transmission
    XOFF = b'\x13'  # Stop transmission
    SUBSTITUTE = b'\x18'
    CANCEL = b'\x1A'  # Terminates a frame in progress

    RESERVED = FLAG + ESCAPE + XON + XOFF + SUBSTITUTE + CANCEL

    def __init__(self, application, connected_future=None):
        self._send_seq = 0
        self._rec_seq = 0
        self._buffer = b''
        self._application = application
        self._reset_future = None
        self._connected_future = connected_future

    def connection_made(self, transport):
        self._transport = transport
        if self._connected_future is not None:
            self._connected_future.set_result(True)

    def data_received(self, data):
        # TODO: Fix this handling for multiple instances of the characters
        # If a Cancel Byte or Substitute Byte is received, the bytes received
        # so far are discarded. In the case of a Substitute Byte, subsequent
        # bytes will also be discarded until the next Flag Byte.
        if self.CANCEL in data:
            data = data[data.find(self.CANCEL) + 1:]
        if self.SUBSTITUTE in data:
            data = data[:data.find(self.SUBSTITUTE) + 1]

        self._buffer += data
        while self._buffer:
            frame, self._buffer = self._extract_frame(self._buffer)
            if frame is None:
                break
            self.frame_received(frame)

    def _extract_frame(self, data):
        if self.FLAG in data:
            place = data.find(self.FLAG)
            return self._unstuff(data[:place + 1]), data[place + 1:]
        return None, data

    def frame_received(self, data):
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
        LOGGER.debug("Data frame: %r", data)
        seq = (data[0] & 0b01110000) >> 4
        self._rec_seq = (seq + 1) % 8
        self.write(self._ack_frame())
        self._application.frame_received(self._randomize(data[1:-3]))

    def ack_frame_received(self, data):
        LOGGER.debug("ACK frame: %r", data)

    def nak_frame_received(self, data):
        LOGGER.debug("NAK frame: %r", data)

    def rst_frame_received(self, data):
        LOGGER.debug("RST frame: %r", data)

    def rstack_frame_received(self, data):
        LOGGER.debug("RSTACK frame: %r", data)
        if self._reset_future is None:
            LOGGER.warn("Reset future is None")
            return
        self._reset_future.set_result(True)

    def error_frame_received(self, data):
        LOGGER.debug("Error frame: %r", data)

    def write(self, data):
        LOGGER.debug("Sending: %r", data)
        self._transport.write(data)

    def close(self):
        self._transport.close()

    def reset(self):
        # TODO: It'd be nice to delete self._reset_future.
        if self._reset_future is not None:
            raise TypeError("reset can only be called on a new connection")

        self.write(self._rst_frame())
        self._reset_future = asyncio.Future()
        return self._reset_future

    def data(self, data):
        self.write(self._data_frame(data))
        self._send_seq = (self._send_seq + 1) % 8

    def _data_frame(self, data):
        control = (self._send_seq << 4) + self._rec_seq
        data = self._randomize(data)
        return self._frame(bytes([control]), data)

    def _ack_frame(self):
        assert 0 <= self._rec_seq < 8
        control = bytes([0b10000000 | (self._rec_seq & 0b00000111)])
        return self._frame(control, b'')

    def _nak_frame(self):
        raise NotImplementedError
        control = None
        return self._frame(control, b'')

    def _rst_frame(self):
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
        rand = 0x42
        out = b''
        for c in s:
            out += bytes([c ^ rand])
            if rand % 2:
                rand = (rand >> 1) ^ 0xB8
            else:
                rand = rand >> 1
        return out

    def _stuff(self, s):
        """Byte stuff (escape) a string for transmission"""
        out = b''
        for c in s:
            if c in self.RESERVED:
                out += self.ESCAPE + bytes([c ^ 0x20])
            else:
                out += bytes([c])
        return out

    def _unstuff(self, s):
        """Unstuff (unescape) a string after receipt"""
        out = b''
        escaped = False
        for c in s:
            if escaped:
                out += bytes([c ^ 0x20])
                escaped = False
            elif c == 0x7D:
                escaped = True
            else:
                out += bytes([c])
        return out


@asyncio.coroutine
def connect(port, application, loop=None):
    if loop is None:
        loop = asyncio.get_event_loop()

    connection_future = asyncio.Future()
    protocol = Gateway(application, connection_future)

    transport, protocol = yield from serial_asyncio.create_serial_connection(
        loop,
        lambda: protocol,
        url=port,
        baudrate=57600,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        xonxoff=True,
    )

    yield from connection_future

    return protocol
