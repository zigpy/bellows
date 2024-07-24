from unittest.mock import MagicMock, call

import pytest

from bellows.ash import DataFrame
import bellows.ezsp.v8
import bellows.types as t

from tests.common import mock_ezsp_commands


@pytest.fixture
def ezsp_f():
    """EZSP v8 protocol handler."""
    ezsp = bellows.ezsp.v8.EZSPv8(MagicMock(), MagicMock())
    mock_ezsp_commands(ezsp)

    return ezsp


def test_ezsp_frame(ezsp_f):
    ezsp_f._seq = 0x22
    data = ezsp_f._ezsp_frame("version", 8)
    assert data == b"\x22\x00\x01\x00\x00\x08"


def test_ezsp_frame_rx(ezsp_f):
    """Test receiving a version frame."""
    ezsp_f(b"\x01\x01\x80\x00\x00\x01\x02\x34\x12")
    assert ezsp_f._handle_callback.call_count == 1
    assert ezsp_f._handle_callback.call_args[0][0] == "version"
    assert ezsp_f._handle_callback.call_args[0][1] == [0x01, 0x02, 0x1234]


async def test_pre_permit(ezsp_f):
    """Test pre permit."""
    ezsp_f.addTransientLinkKey.return_value = (t.EmberStatus.SUCCESS,)

    await ezsp_f.pre_permit(-1.9)
    assert ezsp_f.setPolicy.mock_calls == [
        call(
            policyId=t.EzspPolicyId.TRUST_CENTER_POLICY,
            decisionId=(
                t.EzspDecisionBitmask.ALLOW_JOINS
                | t.EzspDecisionBitmask.ALLOW_UNSECURED_REJOINS
            ),
        ),
        call(policyId=t.EzspPolicyId.TRUST_CENTER_POLICY, decisionId=0),
    ]
    assert ezsp_f.addTransientLinkKey.mock_calls == [
        call(
            partner=t.EUI64.convert("ff:ff:ff:ff:ff:ff:ff:ff"),
            transientKey=t.KeyData(b"ZigBeeAlliance09"),
        )
    ]


def test_get_key_table_entry_fallback_parsing(ezsp_f):
    """Test parsing of a getKeyTableEntry response with an invalid length."""
    data_frame = DataFrame.from_bytes(
        bytes.fromhex(
            "039ba1a9252a1659c6974b25aa55d1209c6e76ddedce958bfdc6f29ffc5e0d2845"
        )
    )
    ezsp_f(data_frame.ezsp_frame)

    assert len(ezsp_f._handle_callback.mock_calls) == 1
    mock_call = ezsp_f._handle_callback.mock_calls[0]
    assert mock_call.args[0] == "getKeyTableEntry"
