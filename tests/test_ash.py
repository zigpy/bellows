import asyncio
from unittest.mock import MagicMock, call, patch

import pytest

from bellows import ash
import bellows.types as t


class AshNcpProtocol(ash.AshProtocol):
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

    async def _send_frame(self, frame: ash.AshFrame) -> None:
        try:
            return await super()._send_frame(frame)
        except asyncio.TimeoutError:
            self._enter_ncp_error_state(
                t.NcpResetCode.ERROR_EXCEEDED_MAXIMUM_ACK_TIMEOUT_COUNT
            )
            raise
        if not isinstance(frame, ash.DataFrame):
            # Non-DATA frames can be sent immediately and do not require an ACK
            self._write_frame(frame)
            return

    def send_reset(self) -> None:
        raise NotImplementedError()


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


def test_pseudo_random_data_sequence():
    assert ash.PSEUDO_RANDOM_DATA_SEQUENCE.startswith(b"\x42\x21\xA8\x54\x2A")


def test_rst_frame():
    assert ash.RstFrame() == ash.RstFrame()
    assert ash.RstFrame().to_bytes() == bytes.fromhex("c038bc")
    assert ash.RstFrame.from_bytes(bytes.fromhex("c038bc")) == ash.RstFrame()
    assert str(ash.RstFrame()) == "RstFrame()"


async def test_ash_protocol_startup():
    """Simple EZSP startup: reset, version(4), then version(8)."""

    loop = asyncio.get_running_loop()

    ezsp = MagicMock()
    transport = MagicMock()

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
    assert protocol._write_frame.mock_calls == [call(ash.RstFrame())]

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


@patch("bellows.ash.T_RX_ACK_INIT", ash.T_RX_ACK_INIT / 100)
@patch("bellows.ash.T_RX_ACK_MIN", ash.T_RX_ACK_MIN / 100)
@patch("bellows.ash.T_RX_ACK_MAX", ash.T_RX_ACK_MAX / 100)
async def test_ash_end_to_end():
    asyncio.get_running_loop()

    host_ezsp = MagicMock()
    ncp_ezsp = MagicMock()

    class FakeTransport:
        def __init__(self, receiver):
            self.receiver = receiver
            self.paused = False

        def write(self, data):
            if not self.paused:
                self.receiver.data_received(data)

    host = ash.AshProtocol(host_ezsp)
    ncp = AshNcpProtocol(ncp_ezsp)

    host_transport = FakeTransport(ncp)
    ncp_transport = FakeTransport(host)

    host.connection_made(host_transport)
    ncp.connection_made(ncp_transport)

    # Ping pong works
    await host.send_data(b"Hello!")
    assert ncp_ezsp.data_received.mock_calls == [call(b"Hello!")]

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

    # When the NCP fail to receive a reply, it enters a failed state
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
