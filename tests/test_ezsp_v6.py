from unittest.mock import MagicMock, call

import pytest
import zigpy.state

import bellows.ezsp.v6
import bellows.types as t

from tests.common import mock_ezsp_commands


@pytest.fixture
def ezsp_f():
    """EZSP v6 protocol handler."""
    ezsp = bellows.ezsp.v6.EZSPv6(MagicMock(), MagicMock())
    mock_ezsp_commands(ezsp)

    return ezsp


def test_ezsp_frame(ezsp_f):
    ezsp_f._seq = 0x22
    data = ezsp_f._ezsp_frame("version", 6)
    assert data == b"\x22\x00\xff\x00\x00\x06"


def test_ezsp_frame_rx(ezsp_f):
    """Test receiving a version frame."""
    ezsp_f(b"\x01\x00\xff\x00\x00\x01\x02\x34\x12")
    assert ezsp_f._handle_callback.call_count == 1
    assert ezsp_f._handle_callback.call_args[0][0] == "version"
    assert ezsp_f._handle_callback.call_args[0][1] == [0x01, 0x02, 0x1234]


async def test_initialize_network(ezsp_f) -> None:
    ezsp_f.networkInit.return_value = (t.EmberStatus.SUCCESS,)
    assert await ezsp_f.initialize_network() == t.sl_Status.OK
    assert ezsp_f.networkInit.mock_calls == [
        call(networkInitBitmask=t.EmberNetworkInitBitmask.NETWORK_INIT_NO_OPTIONS)
    ]
