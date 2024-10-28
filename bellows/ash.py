from __future__ import annotations

import abc
import asyncio
import binascii
from collections.abc import Coroutine
import contextlib
import dataclasses
import enum
import logging
import sys
import time
import typing

if sys.version_info[:2] < (3, 11):
    from async_timeout import timeout as asyncio_timeout  # pragma: no cover
else:
    from asyncio import timeout as asyncio_timeout  # pragma: no cover

from zigpy.types import BaseDataclassMixin

import bellows.types as t

_LOGGER = logging.getLogger(__name__)

MAX_BUFFER_SIZE = 1024


class Reserved(enum.IntEnum):
    FLAG = 0x7E  # Marks end of frame
    ESCAPE = 0x7D
    XON = 0x11  # Resume transmission
    XOFF = 0x13  # Stop transmission
    SUBSTITUTE = 0x18  # Replaces a byte received with a low-level communication error
    CANCEL = 0x1A  # Terminates a frame in progress


RESERVED_BYTES = frozenset(Reserved)
RESERVED_WITHOUT_ESCAPE = frozenset([v for v in Reserved if v != Reserved.ESCAPE])

# Initial value of t_rx_ack, the maximum time the NCP waits to receive acknowledgement
# of a DATA frame
T_RX_ACK_INIT = 1.6

# Minimum value of t_rx_ack
T_RX_ACK_MIN = 0.4

# Maximum value of t_rx_ack
T_RX_ACK_MAX = 3.2

# Delay before sending a non-piggybacked acknowledgement
T_TX_ACK_DELAY = 0.02

# Time from receiving an ACK or NAK with the nRdy flag set after which the NCP resumes
# sending callback frames to the host without requiring an ACK or NAK with the nRdy
# flag clear
T_REMOTE_NOTRDY = 1.0

# Maximum number of DATA frames the NCP can transmit without having received
# acknowledgements
TX_K = 1  # TODO: investigate why this cannot be raised without causing a firmware crash

# Maximum number of consecutive timeouts allowed while waiting to receive an ACK before
# going to the FAILED state. The value 0 prevents the NCP from entering the error state
# due to timeouts.
ACK_TIMEOUTS = 5


def generate_random_sequence(length: int) -> bytes:
    output = bytearray()
    rand = 0x42

    for _i in range(length):
        output.append(rand)

        if rand & 0b00000001 == 0:
            rand = rand >> 1
        else:
            rand = (rand >> 1) ^ 0xB8

    return output


# Since the sequence is static for every frame, we only need to generate it once
PSEUDO_RANDOM_DATA_SEQUENCE = generate_random_sequence(256)

if sys.version_info[:2] < (3, 12):
    create_eager_task = asyncio.create_task
else:
    _T = typing.TypeVar("T")

    def create_eager_task(
        coro: Coroutine[typing.Any, typing.Any, _T],
        *,
        name: str | None = None,
        loop: asyncio.AbstractEventLoop | None = None,
    ) -> asyncio.Task[_T]:
        """Create a task from a coroutine and schedule it to run immediately."""
        if loop is None:
            loop = asyncio.get_running_loop()

        return asyncio.Task(coro, loop=loop, name=name, eager_start=True)


class NcpState(enum.Enum):
    CONNECTED = "connected"
    FAILED = "failed"


class ParsingError(Exception):
    pass


class AshException(Exception):
    pass


class NotAcked(AshException):
    def __init__(self, frame: NakFrame) -> None:
        self.frame = frame

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(frame={self.frame})>"


class NcpFailure(AshException):
    def __init__(self, code: t.NcpResetCode) -> None:
        self.code = code

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(code={self.code})>"

    def __eq__(self, other: object) -> bool | NotImplemented:
        if not isinstance(other, NcpFailure):
            return NotImplemented

        return self.code == other.code


class AshFrame(abc.ABC, BaseDataclassMixin):
    MASK: t.uint8_t
    MASK_VALUE: t.uint8_t

    @classmethod
    def from_bytes(cls, data: bytes) -> AshFrame:
        raise NotImplementedError()

    def to_bytes(self) -> bytes:
        raise NotImplementedError()

    @classmethod
    def _unwrap(cls, data: bytes) -> tuple[int, bytes]:
        if len(data) < 3:
            raise ParsingError(f"Frame is too short: {data!r}")

        computed_crc = binascii.crc_hqx(data[:-2], 0xFFFF).to_bytes(2, "big")

        if computed_crc != data[-2:]:
            raise ParsingError(
                f"Invalid CRC bytes in frame {data!r}:"
                f" expected {computed_crc.hex()}, got {data[-2:].hex()}"
            )

        return data[0], data[1:-2]

    @staticmethod
    def append_crc(data: bytes) -> bytes:
        return data + binascii.crc_hqx(data, 0xFFFF).to_bytes(2, "big")


@dataclasses.dataclass(frozen=True)
class DataFrame(AshFrame):
    MASK = 0b10000000
    MASK_VALUE = 0b00000000

    frm_num: int
    re_tx: bool
    ack_num: int
    ezsp_frame: bytes

    @staticmethod
    def _randomize(data: bytes) -> bytes:
        assert len(data) <= len(PSEUDO_RANDOM_DATA_SEQUENCE)
        return bytes([a ^ b for a, b in zip(data, PSEUDO_RANDOM_DATA_SEQUENCE)])

    @classmethod
    def from_bytes(cls, data: bytes) -> DataFrame:
        control, data = cls._unwrap(data)

        return cls(
            frm_num=(control & 0b01110000) >> 4,
            re_tx=(control & 0b00001000) >> 3,
            ack_num=(control & 0b00000111) >> 0,
            ezsp_frame=cls._randomize(data),
        )

    def to_bytes(self, *, randomize: bool = True) -> bytes:
        return self.append_crc(
            bytes(
                [
                    self.MASK_VALUE
                    | (self.frm_num) << 4
                    | (self.re_tx) << 3
                    | (self.ack_num) << 0
                ]
            )
            + self._randomize(self.ezsp_frame)
        )


@dataclasses.dataclass(frozen=True)
class AckFrame(AshFrame):
    MASK = 0b11100000
    MASK_VALUE = 0b10000000

    res: int
    ncp_ready: bool
    ack_num: int

    @classmethod
    def from_bytes(cls, data: bytes) -> AckFrame:
        control, data = cls._unwrap(data)

        return cls(
            res=(control & 0b00010000) >> 4,
            ncp_ready=(control & 0b00001000) >> 3,
            ack_num=(control & 0b00000111) >> 0,
        )

    def to_bytes(self) -> bytes:
        return self.append_crc(
            bytes(
                [
                    self.MASK_VALUE
                    | (self.res) << 4
                    | (self.ncp_ready) << 3
                    | (self.ack_num) << 0
                ]
            )
        )


@dataclasses.dataclass(frozen=True)
class NakFrame(AshFrame):
    MASK = 0b11100000
    MASK_VALUE = 0b10100000

    res: int
    ncp_ready: bool
    ack_num: int

    @classmethod
    def from_bytes(cls, data: bytes) -> AckFrame:
        control, data = cls._unwrap(data)

        return cls(
            res=(control & 0b00010000) >> 4,
            ncp_ready=(control & 0b00001000) >> 3,
            ack_num=(control & 0b00000111) >> 0,
        )

    def to_bytes(self) -> bytes:
        return self.append_crc(
            bytes(
                [
                    self.MASK_VALUE
                    | (self.res) << 4
                    | (self.ncp_ready) << 3
                    | (self.ack_num) << 0
                ]
            )
        )


@dataclasses.dataclass(frozen=True)
class RstFrame(AshFrame):
    MASK = 0b11111111
    MASK_VALUE = 0b11000000

    @classmethod
    def from_bytes(cls, data: bytes) -> RstFrame:
        control, data = cls._unwrap(data)

        if data:
            raise ParsingError(f"Invalid data for RST frame: {data!r}")

        return cls()

    def to_bytes(self) -> bytes:
        return self.append_crc(bytes([self.MASK_VALUE]))


@dataclasses.dataclass(frozen=True)
class RStackFrame(AshFrame):
    MASK = 0b11111111
    MASK_VALUE = 0b11000001

    version: t.uint8_t
    reset_code: t.NcpResetCode

    @classmethod
    def from_bytes(cls, data: bytes) -> RStackFrame:
        control, data = cls._unwrap(data)

        if len(data) != 2:
            raise ParsingError(f"Invalid data length for RSTACK frame: {data!r}")

        version = data[0]

        if version != 0x02:
            raise ParsingError(f"Invalid version for RSTACK frame: {data!r}")

        reset_code = t.NcpResetCode(data[1])

        return cls(
            version=version,
            reset_code=reset_code,
        )

    def to_bytes(self) -> bytes:
        return self.append_crc(bytes([self.MASK_VALUE, self.version, self.reset_code]))


@dataclasses.dataclass(frozen=True)
class ErrorFrame(AshFrame):
    MASK = 0b11111111
    MASK_VALUE = 0b11000010

    version: t.uint8_t
    reset_code: t.NcpResetCode

    # We do not want to inherit from `RStackFrame`
    from_bytes = classmethod(RStackFrame.from_bytes.__func__)
    to_bytes = RStackFrame.to_bytes


def parse_frame(
    data: bytes,
) -> DataFrame | AckFrame | NakFrame | RstFrame | RStackFrame | ErrorFrame:
    """Parse a frame from the given data, looking at the control byte."""
    control_byte = data[0]

    # In order of use
    for frame in [
        DataFrame,
        AckFrame,
        NakFrame,
        RstFrame,
        RStackFrame,
        ErrorFrame,
    ]:
        if control_byte & frame.MASK == frame.MASK_VALUE:
            return frame.from_bytes(data)
    else:
        raise ParsingError(f"Could not determine frame type: {data!r}")


class AshProtocol(asyncio.Protocol):
    def __init__(self, ezsp_protocol) -> None:
        self._ezsp_protocol = ezsp_protocol
        self._transport = None
        self._buffer = bytearray()
        self._discarding_until_next_flag: bool = False
        self._pending_data_frames: dict[int, asyncio.Future] = {}
        self._send_data_frame_semaphore = asyncio.Semaphore(TX_K)
        self._tx_seq: int = 0
        self._rx_seq: int = 0
        self._t_rx_ack = T_RX_ACK_INIT

        self._ncp_reset_code: t.NcpResetCode | None = None
        self._ncp_state: NcpState = NcpState.CONNECTED

    def connection_made(self, transport):
        self._transport = transport
        self._ezsp_protocol.connection_made(self)

    def connection_lost(self, exc: Exception | None) -> None:
        self._transport = None
        self._cancel_pending_data_frames()
        self._ezsp_protocol.connection_lost(exc)

    def eof_received(self):
        self._ezsp_protocol.eof_received()

    def _cancel_pending_data_frames(
        self, exc: BaseException = RuntimeError("Connection has been closed")
    ):
        for fut in self._pending_data_frames.values():
            if not fut.done():
                fut.set_exception(exc)

    def close(self):
        self._cancel_pending_data_frames()

        if self._transport is not None:
            self._transport.close()
            self._transport = None

    @staticmethod
    def _stuff_bytes(data: bytes) -> bytes:
        """Stuff bytes for transmission"""
        out = bytearray()

        for c in data:
            if c in RESERVED_BYTES:
                out.extend([Reserved.ESCAPE, c ^ 0b00100000])
            else:
                out.append(c)

        return out

    @staticmethod
    def _unstuff_bytes(data: bytes) -> bytes:
        """Unstuff bytes after receipt"""
        out = bytearray()
        escaped = False

        for c in data:
            if escaped:
                byte = c ^ 0b00100000
                if byte not in RESERVED_BYTES:
                    raise ParsingError(f"Invalid escaped byte: 0x{byte:02X}")

                out.append(byte)
                escaped = False
            elif c == Reserved.ESCAPE:
                escaped = True
            else:
                out.append(c)

        return out

    def data_received(self, data: bytes) -> None:
        _LOGGER.debug("Received data %s", data.hex())
        self._buffer.extend(data)

        if len(self._buffer) > MAX_BUFFER_SIZE:
            _LOGGER.debug(
                "Truncating buffer to %s bytes, it is growing too fast", MAX_BUFFER_SIZE
            )
            self._buffer = self._buffer[-MAX_BUFFER_SIZE:]

        while self._buffer:
            if self._discarding_until_next_flag:
                if bytes([Reserved.FLAG]) not in self._buffer:
                    self._buffer.clear()
                    break

                self._discarding_until_next_flag = False
                _, _, self._buffer = self._buffer.partition(bytes([Reserved.FLAG]))

            try:
                # Find the index of the first reserved byte that isn't an escape byte
                reserved_index, reserved_byte = next(
                    (index, byte)
                    for index, byte in enumerate(self._buffer)
                    if byte in RESERVED_WITHOUT_ESCAPE
                )
            except StopIteration:
                break

            if reserved_byte == Reserved.FLAG:
                # Flag Byte marks the end of a frame
                frame_bytes = self._buffer[:reserved_index]
                self._buffer = self._buffer[reserved_index + 1 :]

                # Consecutive EOFs can be received, empty frames are ignored
                if not frame_bytes:
                    continue

                try:
                    data = self._unstuff_bytes(frame_bytes)
                    frame = parse_frame(data)
                except Exception:
                    _LOGGER.debug(
                        "Failed to parse frame %r", frame_bytes, exc_info=True
                    )

                    with contextlib.suppress(NcpFailure):
                        self._write_frame(
                            NakFrame(res=0, ncp_ready=0, ack_num=self._rx_seq),
                            prefix=(Reserved.CANCEL,),
                        )
                else:
                    self.frame_received(frame)
            elif reserved_byte == Reserved.CANCEL:
                _LOGGER.debug("Received cancel byte, clearing buffer")
                # All data received since the previous Flag Byte to be ignored
                self._buffer = self._buffer[reserved_index + 1 :]
            elif reserved_byte == Reserved.SUBSTITUTE:
                _LOGGER.debug("Received substitute byte, marking buffer as corrupted")
                # The data between the previous and the next Flag Byte is ignored
                self._discarding_until_next_flag = True
                self._buffer = self._buffer[reserved_index + 1 :]
            elif reserved_byte == Reserved.XON:
                # Resume transmission: not implemented!
                _LOGGER.debug("Received XON byte, resuming transmission")
                self._buffer.pop(reserved_index)
            elif reserved_byte == Reserved.XOFF:
                # Pause transmission: not implemented!
                _LOGGER.debug("Received XOFF byte, pausing transmission")
                self._buffer.pop(reserved_index)
            else:
                raise RuntimeError(
                    f"Unexpected reserved byte found: 0x{reserved_byte:02X}"
                )  # pragma: no cover

    def _handle_ack(self, frame: DataFrame | AckFrame | NakFrame) -> None:
        # Note that ackNum is the number of the next frame the receiver expects and it
        # is one greater than the last frame received.
        for ack_num_offset in range(-TX_K, 0):
            ack_num = (frame.ack_num + ack_num_offset) % 8
            fut = self._pending_data_frames.get(ack_num)

            if fut is None or fut.done():
                continue

            self._pending_data_frames[ack_num].set_result(True)

    def frame_received(self, frame: AshFrame) -> None:
        _LOGGER.debug("Received frame %r", frame)

        # If a frame has ACK information (DATA, ACK, or NAK), it should be used even if
        # the frame is out of sequence or invalid
        if isinstance(frame, DataFrame):
            self._handle_ack(frame)
            self.data_frame_received(frame)
        elif isinstance(frame, AckFrame):
            self._handle_ack(frame)
            self.ack_frame_received(frame)
        elif isinstance(frame, NakFrame):
            self._handle_ack(frame)
            self.nak_frame_received(frame)
        elif isinstance(frame, RStackFrame):
            self.rstack_frame_received(frame)
        elif isinstance(frame, RstFrame):
            self.rst_frame_received(frame)
        elif isinstance(frame, ErrorFrame):
            self.error_frame_received(frame)
        else:
            raise TypeError(f"Unknown frame received: {frame}")  # pragma: no cover

    def data_frame_received(self, frame: DataFrame) -> None:
        # The Host may not piggyback acknowledgments and should promptly send an ACK
        # frame when it receives a DATA frame.
        if frame.frm_num == self._rx_seq:
            self._rx_seq = (frame.frm_num + 1) % 8
            self._write_frame(AckFrame(res=0, ncp_ready=0, ack_num=self._rx_seq))

            self._ezsp_protocol.data_received(frame.ezsp_frame)
        elif frame.re_tx:
            # Retransmitted frames must be immediately ACKed even if they are out of
            # sequence
            self._write_frame(AckFrame(res=0, ncp_ready=0, ack_num=self._rx_seq))
        else:
            _LOGGER.debug("Received an out of sequence frame: %r", frame)
            self._write_frame(NakFrame(res=0, ncp_ready=0, ack_num=self._rx_seq))

    def rstack_frame_received(self, frame: RStackFrame) -> None:
        self._ncp_reset_code = None
        self._ncp_state = NcpState.CONNECTED

        self._tx_seq = 0
        self._rx_seq = 0
        self._change_ack_timeout(T_RX_ACK_INIT)
        self._ezsp_protocol.reset_received(frame.reset_code)

    def ack_frame_received(self, frame: AckFrame) -> None:
        pass

    def nak_frame_received(self, frame: NakFrame) -> None:
        self._cancel_pending_data_frames(NotAcked(frame=frame))

    def rst_frame_received(self, frame: RstFrame) -> None:
        self._ncp_reset_code = None
        self._ncp_state = NcpState.CONNECTED

    def error_frame_received(self, frame: ErrorFrame) -> None:
        _LOGGER.debug("NCP has entered failed state: %s", frame.reset_code)
        self._ncp_reset_code = frame.reset_code
        self._ncp_state = NcpState.FAILED

        # Cancel all pending requests
        self._enter_failed_state(self._ncp_reset_code)

    def _enter_failed_state(self, reset_code: t.NcpResetCode) -> None:
        self._ncp_state = NcpState.FAILED
        self._cancel_pending_data_frames(NcpFailure(code=reset_code))
        self._ezsp_protocol.reset_received(reset_code)

    def _write_frame(
        self,
        frame: AshFrame,
        *,
        prefix: tuple[Reserved] = (),
        suffix: tuple[Reserved] = (Reserved.FLAG,),
    ) -> None:
        if self._transport is None or self._transport.is_closing():
            raise NcpFailure("Transport is closed, cannot send frame")

        if _LOGGER.isEnabledFor(logging.DEBUG):
            prefix_str = "".join([f"{r.name} + " for r in prefix])
            suffix_str = "".join([f" + {r.name}" for r in suffix])
            _LOGGER.debug("Sending frame %s%r%s", prefix_str, frame, suffix_str)

        data = bytes(prefix) + self._stuff_bytes(frame.to_bytes()) + bytes(suffix)
        _LOGGER.debug("Sending data  %s", data.hex())
        self._transport.write(data)

    def _change_ack_timeout(self, new_value: float) -> None:
        new_value = max(T_RX_ACK_MIN, min(new_value, T_RX_ACK_MAX))

        if abs(new_value - self._t_rx_ack) > 0.01:
            _LOGGER.debug(
                "Changing ACK timeout from %0.2f to %0.2f", self._t_rx_ack, new_value
            )

        self._t_rx_ack = new_value

    async def _send_data_frame(self, frame: AshFrame) -> None:
        if self._send_data_frame_semaphore.locked():
            _LOGGER.debug("Semaphore is locked, waiting")

        async with self._send_data_frame_semaphore:
            frm_num = None

            try:
                for attempt in range(ACK_TIMEOUTS):
                    if self._ncp_state == NcpState.FAILED:
                        _LOGGER.debug(
                            "NCP is in a failed state, not sending: %r", frame
                        )
                        raise NcpFailure(
                            t.NcpResetCode.ERROR_EXCEEDED_MAXIMUM_ACK_TIMEOUT_COUNT
                        )

                    if frm_num is None:
                        frm_num = self._tx_seq
                        self._tx_seq = (self._tx_seq + 1) % 8

                    # Use a fresh ACK number on every retry
                    frame = frame.replace(
                        frm_num=frm_num,
                        re_tx=(attempt > 0),
                        ack_num=self._rx_seq,
                    )

                    send_time = time.monotonic()

                    ack_future = asyncio.get_running_loop().create_future()
                    self._pending_data_frames[frm_num] = ack_future
                    self._write_frame(frame)

                    try:
                        async with asyncio_timeout(self._t_rx_ack):
                            await ack_future
                    except NotAcked:
                        _LOGGER.debug(
                            "NCP responded with NAK to %r. Retrying (attempt %d)",
                            frame,
                            attempt + 1,
                        )

                        # For timing purposes, NAK can be treated as an ACK
                        delta = time.monotonic() - send_time
                        self._change_ack_timeout((7 / 8) * self._t_rx_ack + 0.5 * delta)

                        if attempt >= ACK_TIMEOUTS - 1:
                            self._enter_failed_state(
                                t.NcpResetCode.ERROR_EXCEEDED_MAXIMUM_ACK_TIMEOUT_COUNT
                            )
                            raise
                    except NcpFailure:
                        _LOGGER.debug(
                            "NCP has entered into a failed state, not retrying"
                        )
                        raise
                    except asyncio.TimeoutError:
                        _LOGGER.debug(
                            "No ACK received in %0.2fs (attempt %d) for %r",
                            self._t_rx_ack,
                            attempt + 1,
                            frame,
                        )
                        # If a DATA frame acknowledgement is not received within the
                        # current timeout value, then t_rx_ack is doubled.
                        self._change_ack_timeout(2 * self._t_rx_ack)

                        if attempt >= ACK_TIMEOUTS - 1:
                            self._enter_failed_state(
                                t.NcpResetCode.ERROR_EXCEEDED_MAXIMUM_ACK_TIMEOUT_COUNT
                            )
                            raise
                    else:
                        # Whenever an acknowledgement is received, t_rx_ack is set to
                        # 7/8 of its current value plus 1/2 of the measured time for the
                        # acknowledgement.
                        delta = time.monotonic() - send_time
                        self._change_ack_timeout((7 / 8) * self._t_rx_ack + 0.5 * delta)

                        break
            finally:
                if frm_num is not None:
                    self._pending_data_frames.pop(frm_num)

    async def send_data(self, data: bytes) -> None:
        # Sending data is a critical operation and cannot really be cancelled
        await asyncio.shield(
            create_eager_task(
                self._send_data_frame(
                    # All of the other fields will be set during transmission/retries
                    DataFrame(frm_num=None, re_tx=None, ack_num=None, ezsp_frame=data)
                )
            )
        )

    def send_reset(self) -> None:
        self._write_frame(RstFrame(), prefix=(Reserved.CANCEL,))
