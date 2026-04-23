from unittest.mock import MagicMock

import pytest
import zigpy.exceptions
import zigpy.state

import bellows.ezsp.v16
import bellows.types as t

from tests.common import mock_ezsp_commands


@pytest.fixture
def ezsp_f():
    """EZSP v16 protocol handler."""
    ezsp = bellows.ezsp.v16.EZSPv16(MagicMock(), MagicMock())
    mock_ezsp_commands(ezsp)

    return ezsp


def test_ezsp_frame(ezsp_f):
    ezsp_f._seq = 0x22
    data = ezsp_f._ezsp_frame("version", 16)
    assert data == b"\x22\x00\x01\x00\x00\x10"


def test_ezsp_frame_rx(ezsp_f):
    """Test receiving a version frame."""
    ezsp_f(b"\x01\x01\x80\x00\x00\x01\x02\x34\x12")
    assert ezsp_f._handle_callback.call_count == 1
    assert ezsp_f._handle_callback.call_args[0][0] == "version"
    assert ezsp_f._handle_callback.call_args[0][1] == [0x01, 0x02, 0x1234]


def test_gpep_incoming_v16_expects_trailing_packet_info(ezsp_f):
    """v16 appends an ``SlRxPacketInfo`` struct after the LVBytes payload.

    zigbee-herdsman gates the read on ``version >= 0x10``. We simulate
    that wire format by taking the v13 payload captured from a real
    Busch-Jaeger 6716 U and appending a synthetic packet info trailer.
    """
    from tests.test_ezsp_v13 import BJ6716U_GPEP_PAYLOAD

    packet_info = t.SlRxPacketInfo(
        sender_short_id=t.NWK(0x1234),
        sender_long_id=t.EUI64.convert("00:11:22:33:44:55:66:77"),
        binding_index=0xFF,
        address_index=0xFF,
        last_hop_lqi=200,
        last_hop_rssi=-45,
        last_hop_timestamp=0xDEADBEEF,
    ).serialize()

    envelope = (
        bytes([0x42, 0x00, 0x01])
        + t.uint16_t(0x00C5).serialize()
        + BJ6716U_GPEP_PAYLOAD
        + packet_info
    )

    ezsp_f(envelope)

    assert ezsp_f._handle_callback.call_count == 1
    assert ezsp_f._handle_callback.call_args[0][0] == "gpepIncomingMessageHandler"
    parsed = ezsp_f._handle_callback.call_args[0][1]
    assert parsed[3].source_id == 0x0171F886
    assert parsed[9] == 0xE0  # gpdCommandId
    assert parsed[-1].sender_short_id == 0x1234
    assert parsed[-1].last_hop_lqi == 200
    assert parsed[-1].last_hop_rssi == -45
