from unittest.mock import MagicMock, call

import pytest
import zigpy.exceptions
import zigpy.state

from bellows.exception import InvalidCommandError
import bellows.ezsp.v17
import bellows.types as t

from tests.common import mock_ezsp_commands


@pytest.fixture
def ezsp_f():
    """EZSP v17 protocol handler."""
    ezsp = bellows.ezsp.v17.EZSPv17(MagicMock(), MagicMock())
    mock_ezsp_commands(ezsp)

    return ezsp


def test_ezsp_frame(ezsp_f):
    ezsp_f._seq = 0x22
    data = ezsp_f._ezsp_frame("version", 17)
    assert data == b"\x22\x00\x01\x00\x00\x11"


def test_ezsp_frame_rx(ezsp_f):
    """Test receiving a version frame."""
    ezsp_f(b"\x01\x01\x80\x00\x00\x01\x02\x34\x12")
    assert ezsp_f._handle_callback.call_count == 1
    assert ezsp_f._handle_callback.call_args[0][0] == "version"
    assert ezsp_f._handle_callback.call_args[0][1] == [0x01, 0x02, 0x1234]


async def test_clear_gp_tables(ezsp_f) -> None:
    ezsp_f.gpSinkTableClearAll.return_value = []
    ezsp_f.gpClearProxyTable.return_value = []

    await ezsp_f.clear_gp_tables()

    assert ezsp_f.gpSinkTableClearAll.mock_calls == [call()]
    assert ezsp_f.gpClearProxyTable.mock_calls == [call()]


async def test_clear_gp_tables_unsupported(ezsp_f, caplog) -> None:
    ezsp_f.gpSinkTableClearAll.side_effect = InvalidCommandError("No GP")

    await ezsp_f.clear_gp_tables()

    assert len(ezsp_f.gpClearProxyTable.mock_calls) == 0
    assert "no Green Power tables" in caplog.text
