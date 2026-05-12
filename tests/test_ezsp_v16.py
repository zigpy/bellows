from unittest.mock import MagicMock

import pytest

import bellows.ezsp.v16
import bellows.types as t

from tests.common import mock_ezsp_commands


@pytest.fixture
def ezsp_f():
    """EZSP v16 protocol handler."""
    ezsp = bellows.ezsp.v16.EZSPv16(MagicMock(), MagicMock())
    mock_ezsp_commands(ezsp)

    return ezsp


def test_ezsp_frame(ezsp_f):
    ezsp_f._seq = 0x22
    data = ezsp_f._ezsp_frame("version", 16)
    assert data == b"\x22\x00\x01\x00\x00\x10"


def test_ezsp_frame_rx(ezsp_f):
    """Test receiving a version frame."""
    ezsp_f(b"\x01\x01\x80\x00\x00\x01\x02\x34\x12")
    assert ezsp_f._handle_callback.call_count == 1
    assert ezsp_f._handle_callback.call_args[0][0] == "version"
    assert ezsp_f._handle_callback.call_args[0][1] == [0x01, 0x02, 0x1234]


def test_gpep_incoming_inherits_v13_schema(ezsp_f):
    """v16 uses the v13 ``gpepIncomingMessageHandler`` layout (no trailer)."""
    from tests.test_ezsp_v13 import BJ6716U_GPEP_PAYLOAD

    envelope = (
        bytes([0x42, 0x00, 0x01])
        + t.uint16_t(0x00C5).serialize()
        + BJ6716U_GPEP_PAYLOAD
    )

    ezsp_f(envelope)

    assert ezsp_f._handle_callback.call_count == 1
    assert ezsp_f._handle_callback.call_args[0][0] == "gpepIncomingMessageHandler"
    parsed = ezsp_f._handle_callback.call_args[0][1]
    assert int.from_bytes(bytes(parsed[3].id[:4]), "little") == 0x0171F886
    assert parsed[9] == 0xE0  # gpdCommandId
