from unittest.mock import MagicMock

import pytest

import bellows.ezsp
import bellows.ezsp.v18
import bellows.types as t

from tests.common import mock_ezsp_commands
from tests.test_ezsp_v14 import PACKET_INFO, PACKET_INFO_BYTES


@pytest.fixture
def ezsp_f():
    """EZSP v18 protocol handler."""
    ezsp = bellows.ezsp.v18.EZSPv18(MagicMock(), MagicMock())
    mock_ezsp_commands(ezsp)

    return ezsp


def test_ezsp_frame(ezsp_f):
    ezsp_f._seq = 0x22
    data = ezsp_f._ezsp_frame("version", 18)
    assert data == b"\x22\x00\x01\x00\x00\x12"


def test_ezsp_frame_rx(ezsp_f):
    """Test receiving a version frame."""
    ezsp_f(b"\x01\x01\x80\x00\x00\x01\x02\x34\x12")
    assert ezsp_f._handle_callback.call_count == 1
    assert ezsp_f._handle_callback.call_args[0][0] == "version"
    assert ezsp_f._handle_callback.call_args[0][1] == [0x01, 0x02, 0x1234]


V18_AND_LATER = [v for v in bellows.ezsp.EZSP._BY_VERSION if v >= 18]


@pytest.mark.parametrize("version", V18_AND_LATER)
def test_mac_filter_match_message_handler(version: int) -> None:
    _, _, rx_schema = bellows.ezsp.EZSP._BY_VERSION[version].COMMANDS[
        "macFilterMatchMessageHandler"
    ]
    result, rest = t.deserialize_dict(
        b"\x34\x12" + b"\x01" + PACKET_INFO_BYTES + b"\x03abc", rx_schema
    )

    assert rest == b""
    assert result == {
        "filterValueMatch": 0x1234,
        "legacyPassthroughType": t.EmberMacPassthroughType.MAC_PASSTHROUGH_SE_INTERPAN,
        "packetInfo": PACKET_INFO,
        "messageContents": b"abc",
    }


@pytest.mark.parametrize("version", V18_AND_LATER)
def test_get_token_count(version: int) -> None:
    _, _, rx_schema = bellows.ezsp.EZSP._BY_VERSION[version].COMMANDS["getTokenCount"]
    result, rest = t.deserialize_dict(b"\x2a\x00\x00\x00", rx_schema)

    assert rest == b""
    assert result == {"count": 42}
