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


@pytest.mark.parametrize(
    "payload",
    [
        # Moes 3-gang switch
        "06da700091e30d6d91e30d6dd300000000ffffffffe0ffffffffff2b0289f3b9acc88b1df3fe4e503c0be422f6f3530a9c4ed0700600007165726837706f78404750303030318d",
        "03dd790091e30d6d91e30d6dd3030100007906000052e6f26ed3ff00",
        # EnOcean PTM-216Z (DB)
        "03da1b0043f4550143f45501d3020100001b000000696fd093d0ff0101",
        # EnOcean PTM-216Z, direct commissioning on channel 11 (long press B0):
        # the commissioning telegram, DeviceID GenericSwitch with switch information
        "06dd760043f4550143f45501d300000000ffffffffe0ffffffffff1f0785f26761efc264c893701987babda7238ce9102e934a7600000010020504",
        # the AI+B0 radio channel confirmation, sent as ShortPress2of2 with no payload
        "03dc770043f4550143f45501d302010000770000006875db8e85ff00",
        # subsequent press/release pairs, one per rocker contact
        "03db780043f4550143f45501d30201000078000000692a661d3eff0101",
        "03da790043f4550143f45501d302010000790000006a3861bf27ff0100",
        "03d67c0043f4550143f45501d3020100007c0000006977b4fb0bff0102",
        "03d87e0043f4550143f45501d3020100007e0000006999877c4dff0106",
    ],
)
def test_gpep_incoming_frame(payload: str, ezsp_f) -> None:
    """Parse incoming GP frames."""

    ezsp_frame = (
        bytes([0x42, 0x00, 0x01])  # seq + control bytes
        + t.uint16_t(0x00C5).serialize()  # frame_id LE
        + bytes.fromhex(payload)
    )

    ezsp_f(ezsp_frame)
