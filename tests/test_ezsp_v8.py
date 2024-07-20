from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from bellows.ash import DataFrame
import bellows.ezsp.v8
import bellows.types as t


@pytest.fixture
def ezsp_f():
    """EZSP v8 protocol handler."""
    return bellows.ezsp.v8.EZSPv8(MagicMock(), MagicMock())


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
    p1 = patch.object(ezsp_f, "setPolicy", new=AsyncMock())
    p2 = patch.object(
        ezsp_f,
        "addTransientLinkKey",
        new=AsyncMock(return_value=[ezsp_f.types.EmberStatus.SUCCESS]),
    )
    with p1 as pre_permit_mock, p2 as tclk_mock:
        await ezsp_f.pre_permit(-1.9)
    assert pre_permit_mock.await_count == 2
    assert tclk_mock.await_count == 1


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
