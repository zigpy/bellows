from unittest.mock import MagicMock

import pytest

from bellows.ash import DataFrame
import bellows.ezsp.v7
import bellows.types as t

from tests.common import mock_ezsp_commands


@pytest.fixture
def ezsp_f():
    """EZSP v7 protocol handler."""
    ezsp = bellows.ezsp.v7.EZSPv7(MagicMock(), MagicMock())
    mock_ezsp_commands(ezsp)

    return ezsp


def test_ezsp_frame(ezsp_f):
    ezsp_f._seq = 0x22
    data = ezsp_f._ezsp_frame("version", 7)
    assert data == b"\x22\x00\xff\x00\x00\x07"


def test_ezsp_frame_rx(ezsp_f):
    """Test receiving a version frame."""
    ezsp_f(b"\x01\x00\xff\x00\x00\x01\x02\x34\x12")
    assert ezsp_f._handle_callback.call_count == 1
    assert ezsp_f._handle_callback.call_args[0][0] == "version"
    assert ezsp_f._handle_callback.call_args[0][1] == [0x01, 0x02, 0x1234]


async def test_read_child_data(ezsp_f):
    def get_child_data(index):
        if index == 0:
            status = t.EmberStatus.SUCCESS
        else:
            status = t.EmberStatus.NOT_JOINED

        return (
            status,
            t.EmberChildDataV7(
                eui64=t.EUI64.convert("00:0b:57:ff:fe:2b:d4:57"),
                type=t.EmberNodeType.SLEEPY_END_DEVICE,
                id=t.EmberNodeId(0xC06B),
                phy=0,
                power=128,
                timeout=3,
            ),
        )

    ezsp_f.getChildData.side_effect = get_child_data

    child_data = [row async for row in ezsp_f.read_child_data()]
    assert child_data == [
        (
            0xC06B,
            t.EUI64.convert("00:0b:57:ff:fe:2b:d4:57"),
            t.EmberNodeType.SLEEPY_END_DEVICE,
        )
    ]
