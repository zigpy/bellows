from __future__ import annotations

import asyncio
import logging
import random
from unittest.mock import MagicMock, call, patch

import pytest

from bellows import ash
import bellows.types as t


class AshNcpProtocol(ash.AshProtocol):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.nak_state = False

    def frame_received(self, frame: ash.AshFrame) -> None:
        if self._ncp_reset_code is not None and not isinstance(frame, ash.RstFrame):
            ash._LOGGER.debug(
                "NCP in failure state %r, ignoring frame: %r",
                self._ncp_reset_code,
                frame,
            )
            self._write_frame(
                ash.ErrorFrame(version=2, reset_code=self._ncp_reset_code)
            )
            return

        if self.nak_state:
            asyncio.get_running_loop().call_later(
                2 * self._t_rx_ack,
                lambda: self._write_frame(
                    ash.NakFrame(res=0, ncp_ready=0, ack_num=self._rx_seq)
                ),
            )
            return

        super().frame_received(frame)

    def _enter_ncp_error_state(self, code: t.NcpResetCode | None) -> None:
        self._ncp_reset_code = code

        if code is None:
            self._ncp_state = ash.NcpState.CONNECTED
        else:
            self._ncp_state = ash.NcpState.FAILED

        ash._LOGGER.debug("Changing connectivity state: %r", self._ncp_state)
        ash._LOGGER.debug("Changing reset code: %r", self._ncp_reset_code)

        if self._ncp_state == ash.NcpState.FAILED:
            self._write_frame(
                ash.ErrorFrame(version=2, reset_code=self._ncp_reset_code)
            )

    def rst_frame_received(self, frame: ash.RstFrame) -> None:
        super().rst_frame_received(frame)

        self._tx_seq = 0
        self._rx_seq = 0
        self._change_ack_timeout(ash.T_RX_ACK_INIT)

        self._enter_ncp_error_state(None)
        self._write_frame(
            ash.RStackFrame(version=2, reset_code=t.NcpResetCode.RESET_SOFTWARE)
        )

    async def _send_data_frame(self, frame: ash.AshFrame) -> None:
        try:
            return await super()._send_data_frame(frame)
        except asyncio.TimeoutError:
            self._enter_ncp_error_state(
                t.NcpResetCode.ERROR_EXCEEDED_MAXIMUM_ACK_TIMEOUT_COUNT
            )
            raise

    def send_reset(self) -> None:
        raise NotImplementedError()


class FakeTransport:
    def __init__(self, receiver) -> None:
        self.receiver = receiver
        self.paused: bool = False
        self.closing: bool = False

    def write(self, data: bytes) -> None:
        if not self.paused:
            self.receiver.data_received(data)

    def close(self) -> None:
        self.closing = True

    def is_closing(self) -> bool:
        return self.closing


class FakeTransportOneByteAtATime(FakeTransport):
    def write(self, data: bytes) -> None:
        for byte in data:
            super().write(bytes([byte]))


class FakeTransportRandomLoss(FakeTransport):
    def write(self, data: bytes) -> None:
        if random.random() < 0.20:
            return

        super().write(data)


class FakeTransportWithDelays(FakeTransport):
    def write(self, data):
        asyncio.get_running_loop().call_later(0, super().write, data)


def test_ash_exception_repr() -> None:
    assert (
        repr(ash.NotAcked(ash.NakFrame(res=0, ncp_ready=0, ack_num=1)))
        == "<NotAcked(frame=NakFrame(res=0, ncp_ready=0, ack_num=1))>"
    )
    assert (
        repr(ash.NcpFailure(t.NcpResetCode.RESET_SOFTWARE))
        == "<NcpFailure(code=<NcpResetCode.RESET_SOFTWARE: 11>)>"
    )


@pytest.mark.parametrize(
    "frame",
    [
        ash.RstFrame(),
        ash.AckFrame(res=0, ncp_ready=0, ack_num=1),
        ash.NakFrame(res=0, ncp_ready=0, ack_num=1),
        ash.RStackFrame(version=2, reset_code=t.NcpResetCode.RESET_SOFTWARE),
        ash.ErrorFrame(version=2, reset_code=t.NcpResetCode.RESET_SOFTWARE),
        ash.DataFrame(frm_num=0, re_tx=False, ack_num=1, ezsp_frame=b"test"),
    ],
)
def test_parse_frame(frame: ash.AshFrame) -> None:
    assert ash.parse_frame(frame.to_bytes()) == frame


def test_parse_frame_failure() -> None:
    with pytest.raises(ash.ParsingError):
        ash.parse_frame(b"test")


def test_ash_protocol_event_propagation() -> None:
    ezsp = MagicMock()
    protocol = ash.AshProtocol(ezsp)

    err = RuntimeError("test")
    protocol.connection_lost(err)
    assert ezsp.connection_lost.mock_calls == [call(err)]

    protocol.eof_received()
    assert ezsp.eof_received.mock_calls == [call()]


def test_stuffing():
    assert ash.AshProtocol._stuff_bytes(b"\x7E") == b"\x7D\x5E"
    assert ash.AshProtocol._stuff_bytes(b"\x11") == b"\x7D\x31"
    assert ash.AshProtocol._stuff_bytes(b"\x13") == b"\x7D\x33"
    assert ash.AshProtocol._stuff_bytes(b"\x18") == b"\x7D\x38"
    assert ash.AshProtocol._stuff_bytes(b"\x1A") == b"\x7D\x3A"
    assert ash.AshProtocol._stuff_bytes(b"\x7D") == b"\x7D\x5D"

    assert ash.AshProtocol._unstuff_bytes(b"\x7D\x5E") == b"\x7E"
    assert ash.AshProtocol._unstuff_bytes(b"\x7D\x31") == b"\x11"
    assert ash.AshProtocol._unstuff_bytes(b"\x7D\x33") == b"\x13"
    assert ash.AshProtocol._unstuff_bytes(b"\x7D\x38") == b"\x18"
    assert ash.AshProtocol._unstuff_bytes(b"\x7D\x3A") == b"\x1A"
    assert ash.AshProtocol._unstuff_bytes(b"\x7D\x5D") == b"\x7D"

    assert ash.AshProtocol._stuff_bytes(b"\x7F") == b"\x7F"
    assert ash.AshProtocol._unstuff_bytes(b"\x7F") == b"\x7F"

    with pytest.raises(ash.ParsingError):
        # AB is not a sequence of bytes that can be unescaped
        assert ash.AshProtocol._unstuff_bytes(b"\x7D\xAB")


def test_pseudo_random_data_sequence():
    assert ash.PSEUDO_RANDOM_DATA_SEQUENCE.startswith(b"\x42\x21\xA8\x54\x2A")


def test_frame_parsing_errors():
    with pytest.raises(ash.ParsingError, match=r"Frame is too short:"):
        assert ash.RstFrame.from_bytes(b"\xC0\x38")

    with pytest.raises(ash.ParsingError, match=r"Invalid CRC bytes in frame"):
        assert ash.RstFrame.from_bytes(b"\xC0\xAB\xCD")


def test_rst_frame():
    assert ash.RstFrame() == ash.RstFrame()
    assert ash.RstFrame().to_bytes() == b"\xC0\x38\xBC"
    assert ash.RstFrame.from_bytes(b"\xC0\x38\xBC") == ash.RstFrame()
    assert str(ash.RstFrame()) == "RstFrame()"

    with pytest.raises(ash.ParsingError, match=r"Invalid data for RST frame:"):
        ash.RstFrame.from_bytes(ash.AshFrame.append_crc(b"\xC0\xAB"))


def test_rstack_frame():
    frm = ash.RStackFrame(version=2, reset_code=t.NcpResetCode.RESET_SOFTWARE)

    assert frm.to_bytes() == b"\xc1\x02\x0b\x0a\x52"
    assert ash.RStackFrame.from_bytes(frm.to_bytes()) == frm
    assert (
        str(frm)
        == "RStackFrame(version=2, reset_code=<NcpResetCode.RESET_SOFTWARE: 11>)"
    )

    with pytest.raises(
        ash.ParsingError, match=r"Invalid data length for RSTACK frame:"
    ):
        # Adding \xAB in the middle of the frame makes it invalid
        ash.RStackFrame.from_bytes(ash.AshFrame.append_crc(b"\xc1\x02\xab\x0b"))

    with pytest.raises(ash.ParsingError, match=r"Invalid version for RSTACK frame:"):
        # Version 3 is unknown
        ash.RStackFrame.from_bytes(ash.AshFrame.append_crc(b"\xc1\x03\x0b"))


def test_cancel_byte():
    ezsp = MagicMock()
    protocol = ash.AshProtocol(ezsp)
    protocol.frame_received = MagicMock(wraps=protocol.frame_received)

    protocol.data_received(bytes.fromhex("ddf9ff"))
    protocol.data_received(bytes.fromhex("1ac1020b0a527e"))  # starts with a CANCEL byte

    # We still parse out the RSTACK frame
    assert protocol.frame_received.mock_calls == [
        call(ash.RStackFrame(version=2, reset_code=t.NcpResetCode.RESET_SOFTWARE))
    ]
    assert not protocol._buffer

    # Parse byte-by-byte
    protocol.frame_received.reset_mock()

    for byte in bytes.fromhex("ddf9ff 1ac1020b0a527e"):
        protocol.data_received(bytes([byte]))

    # We still parse out the RSTACK frame
    assert protocol.frame_received.mock_calls == [
        call(ash.RStackFrame(version=2, reset_code=t.NcpResetCode.RESET_SOFTWARE))
    ]
    assert not protocol._buffer


def test_substitute_byte():
    ezsp = MagicMock()
    protocol = ash.AshProtocol(ezsp)
    protocol.frame_received = MagicMock(wraps=protocol.frame_received)

    protocol.data_received(bytes.fromhex("c0        38bc 7e"))  # RST frame
    assert protocol.frame_received.mock_calls == [call(ash.RstFrame())]
    protocol.data_received(bytes.fromhex("c0 18     38bc 7e"))  # RST frame + SUBSTITUTE
    assert protocol.frame_received.mock_calls == [call(ash.RstFrame())]  # ignored!
    protocol.data_received(bytes.fromhex("c1 020b   0a52 7e"))  # RSTACK frame
    assert protocol.frame_received.mock_calls == [
        call(ash.RstFrame()),
        call(ash.RStackFrame(version=2, reset_code=t.NcpResetCode.RESET_SOFTWARE)),
    ]

    assert not protocol._buffer


def test_xon_xoff_bytes():
    ezsp = MagicMock()
    protocol = ash.AshProtocol(ezsp)
    protocol.frame_received = MagicMock(wraps=protocol.frame_received)

    protocol.data_received(bytes.fromhex("c0 11 38bc 13 7e"))  # RST frame + XON + XOFF
    assert protocol.frame_received.mock_calls == [call(ash.RstFrame())]


def test_multiple_eof():
    ezsp = MagicMock()
    protocol = ash.AshProtocol(ezsp)
    protocol.frame_received = MagicMock(wraps=protocol.frame_received)

    protocol.data_received(bytes.fromhex("c0 38bc 7e 7e 7e"))  # RST frame
    assert protocol.frame_received.mock_calls == [call(ash.RstFrame())]


def test_discarding():
    ezsp = MagicMock()
    protocol = ash.AshProtocol(ezsp)
    protocol.frame_received = MagicMock(wraps=protocol.frame_received)

    # RST frame with embedded SUBSTITUTE
    protocol.data_received(bytes.fromhex("c0 18 38bc"))

    # Garbage: still ignored
    protocol.data_received(bytes.fromhex("aa bb cc dd ee ff"))

    # Frame boundary: we now will handle data
    protocol.data_received(bytes.fromhex("7e"))

    # Normal RST frame
    protocol.data_received(bytes.fromhex("c0    38bc 7e 7e 7e"))
    assert protocol.frame_received.mock_calls == [call(ash.RstFrame())]


def test_buffer_growth():
    ezsp = MagicMock()
    protocol = ash.AshProtocol(ezsp)

    # Receive a lot of bogus data
    for i in range(1000):
        protocol.data_received(b"\xEE" * 100)

    # Make sure our internal buffer doesn't blow up
    assert len(protocol._buffer) == ash.MAX_BUFFER_SIZE


async def test_sequence():
    loop = asyncio.get_running_loop()
    ezsp = MagicMock()
    transport = MagicMock()
    transport.is_closing.return_value = False

    protocol = ash.AshProtocol(ezsp)
    protocol._write_frame = MagicMock(wraps=protocol._write_frame)
    protocol.connection_made(transport)

    # Normal send/receive
    loop.call_later(
        0,
        protocol.frame_received,
        ash.DataFrame(frm_num=0, re_tx=False, ack_num=1, ezsp_frame=b"rx 1"),
    )
    await protocol.send_data(b"tx 1")
    assert protocol._write_frame.mock_calls[-1] == call(
        ash.AckFrame(res=0, ncp_ready=0, ack_num=1)
    )

    assert protocol._rx_seq == 1
    assert protocol._tx_seq == 1
    assert ezsp.data_received.mock_calls == [call(b"rx 1")]

    # Skip ACK 2: we are out of sync!
    protocol.frame_received(
        ash.DataFrame(frm_num=2, re_tx=False, ack_num=1, ezsp_frame=b"out of sequence")
    )

    # We NAK it, it is out of sequence!
    assert protocol._write_frame.mock_calls[-1] == call(
        ash.NakFrame(res=0, ncp_ready=0, ack_num=1)
    )

    # Sequence numbers remain intact
    assert protocol._rx_seq == 1
    assert protocol._tx_seq == 1

    # Re-sync properly
    protocol.frame_received(
        ash.DataFrame(frm_num=1, re_tx=False, ack_num=1, ezsp_frame=b"rx 2")
    )

    assert ezsp.data_received.mock_calls == [call(b"rx 1"), call(b"rx 2")]

    # Trigger an error
    loop.call_later(
        0,
        protocol.frame_received,
        ash.ErrorFrame(version=2, reset_code=t.NcpResetCode.RESET_SOFTWARE),
    )

    with pytest.raises(ash.NcpFailure):
        await protocol.send_data(b"tx 2")


async def test_frame_parsing_failure_recovery(caplog) -> None:
    ezsp = MagicMock()
    protocol = ash.AshProtocol(ezsp)
    protocol.frame_received = MagicMock(spec_set=protocol.frame_received)

    protocol.data_received(
        ash.DataFrame(frm_num=0, re_tx=0, ack_num=0, ezsp_frame=b"frame 1").to_bytes()
        + bytes([ash.Reserved.FLAG])
    )

    with caplog.at_level(logging.DEBUG):
        protocol.data_received(
            ash.AshFrame.append_crc(b"\xFESome unknown frame")
            + bytes([ash.Reserved.FLAG])
        )

    assert "Some unknown frame" in caplog.text

    protocol.data_received(
        ash.DataFrame(frm_num=1, re_tx=0, ack_num=0, ezsp_frame=b"frame 2").to_bytes()
        + bytes([ash.Reserved.FLAG])
    )

    assert protocol.frame_received.mock_calls == [
        call(ash.DataFrame(frm_num=0, re_tx=0, ack_num=0, ezsp_frame=b"frame 1")),
        call(ash.DataFrame(frm_num=1, re_tx=0, ack_num=0, ezsp_frame=b"frame 2")),
    ]


async def test_ash_protocol_startup(caplog):
    """Simple EZSP startup: reset, version(4), then version(8)."""

    # We have branching dependent on `_LOGGER.isEnabledFor` so test it here
    caplog.set_level(logging.DEBUG)

    loop = asyncio.get_running_loop()

    ezsp = MagicMock()
    transport = MagicMock()
    transport.is_closing.return_value = False

    protocol = ash.AshProtocol(ezsp)
    protocol._write_frame = MagicMock(wraps=protocol._write_frame)
    protocol.connection_made(transport)

    assert ezsp.connection_made.mock_calls == [call(protocol)]

    assert protocol._rx_seq == 0
    assert protocol._tx_seq == 0

    # ASH reset
    protocol.send_reset()
    loop.call_later(
        0,
        protocol.frame_received,
        ash.RStackFrame(version=2, reset_code=t.NcpResetCode.RESET_SOFTWARE),
    )

    await asyncio.sleep(0.01)

    assert ezsp.reset_received.mock_calls == [call(t.NcpResetCode.RESET_SOFTWARE)]
    assert protocol._write_frame.mock_calls == [
        call(ash.RstFrame(), prefix=(ash.Reserved.CANCEL,))
    ]

    protocol._write_frame.reset_mock()

    # EZSP version(4)
    loop.call_later(
        0,
        protocol.frame_received,
        ash.DataFrame(
            frm_num=0, re_tx=False, ack_num=1, ezsp_frame=b"\x00\x80\x00\x08\x02\x80g"
        ),
    )
    await protocol.send_data(b"\x00\x00\x00\x04")
    assert protocol._write_frame.mock_calls == [
        call(
            ash.DataFrame(
                frm_num=0, re_tx=False, ack_num=0, ezsp_frame=b"\x00\x00\x00\x04"
            )
        ),
        call(ash.AckFrame(res=0, ncp_ready=0, ack_num=1)),
    ]

    protocol._write_frame.reset_mock()

    # EZSP version(8)
    loop.call_later(
        0,
        protocol.frame_received,
        ash.DataFrame(
            frm_num=1,
            re_tx=False,
            ack_num=2,
            ezsp_frame=b"\x00\x80\x01\x00\x00\x08\x02\x80g",
        ),
    )
    await protocol.send_data(b"\x00\x00\x01\x00\x00\x08")
    assert protocol._write_frame.mock_calls == [
        call(
            ash.DataFrame(
                frm_num=1,
                re_tx=False,
                ack_num=1,
                ezsp_frame=b"\x00\x00\x01\x00\x00\x08",
            )
        ),
        call(ash.AckFrame(res=0, ncp_ready=0, ack_num=2)),
    ]


@patch("bellows.ash.T_RX_ACK_INIT", ash.T_RX_ACK_INIT / 1000)
@patch("bellows.ash.T_RX_ACK_MIN", ash.T_RX_ACK_MIN / 1000)
@patch("bellows.ash.T_RX_ACK_MAX", ash.T_RX_ACK_MAX / 1000)
@pytest.mark.parametrize(
    "transport_cls",
    [
        FakeTransport,
        FakeTransportOneByteAtATime,
        FakeTransportRandomLoss,
        FakeTransportWithDelays,
    ],
)
async def test_ash_end_to_end(transport_cls: type[FakeTransport]) -> None:
    random.seed(2)

    host_ezsp = MagicMock()
    ncp_ezsp = MagicMock()

    host = ash.AshProtocol(host_ezsp)
    ncp = AshNcpProtocol(ncp_ezsp)

    host_transport = transport_cls(ncp)
    ncp_transport = transport_cls(host)

    host.connection_made(host_transport)
    ncp.connection_made(ncp_transport)

    # Ping pong works
    await asyncio.gather(
        host.send_data(b"Hello 1!"),
        host.send_data(b"Hello 2!"),
    )
    assert ncp_ezsp.data_received.mock_calls == [call(b"Hello 1!"), call(b"Hello 2!")]

    await ncp.send_data(b"World!")
    assert host_ezsp.data_received.mock_calls == [call(b"World!")]

    ncp_ezsp.data_received.reset_mock()
    host_ezsp.data_received.reset_mock()

    # Let's pause the ncp so it can't ACK
    with patch.object(ncp_transport, "paused", True):
        send_task = asyncio.create_task(host.send_data(b"delayed"))
        await asyncio.sleep(host._t_rx_ack * 2)

    # It'll still succeed
    await send_task

    assert ncp_ezsp.data_received.mock_calls == [call(b"delayed")]

    ncp_ezsp.data_received.reset_mock()
    host_ezsp.data_received.reset_mock()

    # Let's let a request fail due to a connectivity issue
    with patch.object(ncp_transport, "paused", True):
        send_task = asyncio.create_task(host.send_data(b"host failure"))
        await asyncio.sleep(host._t_rx_ack * 15)

    with pytest.raises(asyncio.TimeoutError):
        await send_task

    ncp_ezsp.data_received.reset_mock()
    host_ezsp.data_received.reset_mock()

    # Simulate OOM on the NCP and send NAKs for a bit
    with patch.object(ncp, "nak_state", True):
        send_task = asyncio.create_task(host.send_data(b"ncp NAKing"))
        await asyncio.sleep(host._t_rx_ack)

    # The NCP is in a failed state, we can't send it
    with pytest.raises(ash.NcpFailure):
        await send_task

    ncp_ezsp.data_received.reset_mock()
    host_ezsp.data_received.reset_mock()

    # When the NCP fails to receive a reply, it enters a failed state
    assert host._ncp_reset_code is None
    assert ncp._ncp_reset_code is None

    with patch.object(host_transport, "paused", True):
        send_task = asyncio.create_task(ncp.send_data(b"ncp failure"))
        await asyncio.sleep(ncp._t_rx_ack * 15)

    with pytest.raises(asyncio.TimeoutError):
        await send_task

    assert (
        host._ncp_reset_code is t.NcpResetCode.ERROR_EXCEEDED_MAXIMUM_ACK_TIMEOUT_COUNT
    )
    assert (
        ncp._ncp_reset_code is t.NcpResetCode.ERROR_EXCEEDED_MAXIMUM_ACK_TIMEOUT_COUNT
    )

    ncp_ezsp.data_received.reset_mock()
    host_ezsp.data_received.reset_mock()

    # All communication attempts with it will fail until it is reset
    with pytest.raises(ash.NcpFailure):
        await host.send_data(b"test")

    host.send_reset()
    await asyncio.sleep(0.01)
    await host.send_data(b"test")

    # Trigger a failure caused by excessive NAKs
    ncp._t_rx_ack = ash.T_RX_ACK_INIT / 1000
    host._t_rx_ack = ash.T_RX_ACK_INIT / 1000

    with patch.object(ncp, "nak_state", True):
        with pytest.raises(ash.NotAcked):
            await host.send_data(b"ncp NAKing until failure")


def test_ncp_failure_comparison() -> None:
    exc1 = ash.NcpFailure(code=t.NcpResetCode.ERROR_EXCEEDED_MAXIMUM_ACK_TIMEOUT_COUNT)
    exc2 = ash.NcpFailure(code=t.NcpResetCode.RESET_POWER_ON)

    assert exc1 == exc1
    assert exc1 != exc2
    assert exc2 != t.NcpResetCode.RESET_POWER_ON
