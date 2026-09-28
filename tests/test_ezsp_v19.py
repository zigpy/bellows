from unittest.mock import MagicMock

import pytest

import bellows.ezsp
import bellows.ezsp.v19
import bellows.types as t

from tests.common import mock_ezsp_commands


@pytest.fixture
def ezsp_f():
    """EZSP v19 protocol handler."""
    ezsp = bellows.ezsp.v19.EZSPv19(MagicMock(), MagicMock())
    mock_ezsp_commands(ezsp)

    return ezsp


def test_ezsp_frame(ezsp_f):
    ezsp_f._seq = 0x22
    data = ezsp_f._ezsp_frame("version", 19)
    assert data == b"\x22\x00\x01\x00\x00\x13"


def test_ezsp_frame_rx(ezsp_f):
    """Test receiving a version frame."""
    ezsp_f(b"\x01\x01\x80\x00\x00\x01\x02\x34\x12")
    assert ezsp_f._handle_callback.call_count == 1
    assert ezsp_f._handle_callback.call_args[0][0] == "version"
    assert ezsp_f._handle_callback.call_args[0][1] == [0x01, 0x02, 0x1234]


@pytest.mark.parametrize(
    "version", [v for v in bellows.ezsp.EZSP._BY_VERSION if v >= 19]
)
def test_get_token_info(version: int) -> None:
    _, _, rx_schema = bellows.ezsp.EZSP._BY_VERSION[version].COMMANDS["getTokenInfo"]
    result, rest = t.deserialize_dict(
        bytes.fromhex("00000000" "01000000" "00" "01" "2c010000" "05"), rx_schema
    )

    assert rest == b""
    assert result["status"] == t.sl_Status.OK
    assert result["token_info"].nvm3Key == 0x00000001
    assert result["token_info"].isCnt == t.Bool.false
    assert result["token_info"].isIdx == t.Bool.true
    assert result["token_info"].size == 300
    assert result["token_info"].arraySize == 5
