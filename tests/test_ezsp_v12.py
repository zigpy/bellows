from unittest.mock import MagicMock

import pytest

import bellows.ezsp.v12
import bellows.types as t

from tests.common import mock_ezsp_commands


@pytest.fixture
def ezsp_f():
    """EZSP v12 protocol handler."""
    ezsp = bellows.ezsp.v12.EZSPv12(MagicMock(), MagicMock())
    mock_ezsp_commands(ezsp)

    return ezsp


def test_ezsp_frame(ezsp_f):
    ezsp_f._seq = 0x22
    data = ezsp_f._ezsp_frame("version", 12)
    assert data == b"\x22\x00\x01\x00\x00\x0c"


def test_ezsp_frame_rx(ezsp_f):
    """Test receiving a version frame."""
    ezsp_f(b"\x01\x01\x80\x00\x00\x01\x02\x34\x12")
    assert ezsp_f._handle_callback.call_count == 1
    assert ezsp_f._handle_callback.call_args[0][0] == "version"
    assert ezsp_f._handle_callback.call_args[0][1] == [0x01, 0x02, 0x1234]


def test_check_key_context(ezsp_f) -> None:
    """`checkKeyContext` takes a security manager context and returns an `sl_status_t`."""
    context = t.SecurityManagerContextV12(
        core_key_type=t.SecurityManagerKeyType.APP_LINK,
        key_index=0,
        derived_type=t.SecurityManagerDerivedKeyTypeV12.NONE,
        eui64=t.EUI64.convert("01:02:03:04:05:06:07:08"),
        multi_network_index=0,
        flags=t.SecurityManagerContextFlags.EUI_IS_VALID,
        psa_key_alg_permission=0,
    )
    _, tx_schema, rx_schema = ezsp_f.COMMANDS["checkKeyContext"]

    assert t.serialize_dict((), {"context": context}, tx_schema) == bytes.fromhex(
        "04" "00" "00" "0807060504030201" "00" "02" "00000000"
    )
    assert t.deserialize_dict(b"\x00\x00\x00\x00", rx_schema) == (
        {"status": t.sl_Status.OK},
        b"",
    )
