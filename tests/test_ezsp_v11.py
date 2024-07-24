from unittest.mock import MagicMock

import pytest

import bellows.ezsp.v11

from tests.common import mock_ezsp_commands


@pytest.fixture
def ezsp_f():
    """EZSP v11 protocol handler."""
    ezsp = bellows.ezsp.v11.EZSPv11(MagicMock(), MagicMock())
    mock_ezsp_commands(ezsp)

    return ezsp


def test_ezsp_frame(ezsp_f):
    ezsp_f._seq = 0x22
    data = ezsp_f._ezsp_frame("version", 11)
    assert data == b"\x22\x00\x01\x00\x00\x0b"


def test_ezsp_frame_rx(ezsp_f):
    """Test receiving a version frame."""
    ezsp_f(b"\x01\x01\x80\x00\x00\x01\x02\x34\x12")
    assert ezsp_f._handle_callback.call_count == 1
    assert ezsp_f._handle_callback.call_args[0][0] == "version"
    assert ezsp_f._handle_callback.call_args[0][1] == [0x01, 0x02, 0x1234]
