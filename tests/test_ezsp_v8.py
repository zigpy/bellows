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


@pytest.mark.parametrize(
    "kwargs, decision",
    [
        (
            {"allow_joins": True},
            t.EzspDecisionBitmask.DEFER_JOINS
            | t.EzspDecisionBitmask.ALLOW_JOINS
            | t.EzspDecisionBitmask.ALLOW_UNSECURED_REJOINS,
        ),
        (
            {"allow_joins": True, "install_codes_only": True},
            t.EzspDecisionBitmask.DEFER_JOINS
            | t.EzspDecisionBitmask.ALLOW_JOINS
            | t.EzspDecisionBitmask.ALLOW_UNSECURED_REJOINS
            | t.EzspDecisionBitmask.JOINS_USE_INSTALL_CODE_KEY,
        ),
        # Closing restores the configured policy
        ({"allow_joins": False}, t.EzspDecisionBitmask.DEFER_JOINS),
    ],
)
async def test_set_join_policy(ezsp_f, kwargs, decision) -> None:
    ezsp_f.setPolicy.return_value = [t.EmberStatus.SUCCESS]

    # Join windows build on top of the user's policy
    await ezsp_f.update_policies(
        {t.EzspPolicyId.TRUST_CENTER_POLICY.name: t.EzspDecisionBitmask.DEFER_JOINS}
    )
    ezsp_f.setPolicy.reset_mock()

    await ezsp_f.set_join_policy(**kwargs)

    assert ezsp_f.setPolicy.mock_calls == [
        call(policyId=t.EzspPolicyId.TRUST_CENTER_POLICY, decisionId=decision)
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
