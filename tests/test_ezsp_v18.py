from unittest.mock import MagicMock, call

import pytest

import bellows.ezsp.v18
import bellows.types as t

from tests.common import mock_ezsp_commands


@pytest.fixture
def ezsp_f():
    """EZSP v18 protocol handler."""
    ezsp = bellows.ezsp.v18.EZSPv18(MagicMock(), MagicMock())
    mock_ezsp_commands(ezsp)

    return ezsp


def test_ezsp_frame(ezsp_f):
    ezsp_f._seq = 0x22
    data = ezsp_f._ezsp_frame("version", 18)
    assert data == b"\x22\x00\x01\x00\x00\x12"


def test_ezsp_frame_rx(ezsp_f):
    """Test receiving a version frame."""
    ezsp_f(b"\x01\x01\x80\x00\x00\x01\x02\x34\x12")
    assert ezsp_f._handle_callback.call_count == 1
    assert ezsp_f._handle_callback.call_args[0][0] == "version"
    assert ezsp_f._handle_callback.call_args[0][1] == [0x01, 0x02, 0x1234]


async def test_send_unicast(ezsp_f) -> None:
    ezsp_f.sendUnicast.return_value = (t.sl_Status.OK, 0x0042)

    aps_frame = t.EmberApsFrame(
        profileId=0x0104,
        clusterId=0x0006,
        sourceEndpoint=1,
        destinationEndpoint=2,
        options=t.EmberApsOption.APS_OPTION_RETRY,
        groupId=0x0000,
        sequence=0x34,
    )

    status, message_tag = await ezsp_f.send_unicast(
        nwk=0x1234,
        aps_frame=aps_frame,
        message_tag=0x42,
        data=b"hello",
    )

    assert status == t.sl_Status.OK
    assert message_tag == 0x42
    assert ezsp_f.sendUnicast.mock_calls == [
        call(
            message_type=t.EmberOutgoingMessageType.OUTGOING_DIRECT,
            nwk=0x1234,
            aps_frame=t.EmberApsFrameV18(
                profileId=0x0104,
                clusterId=0x0006,
                sourceEndpoint=1,
                destinationEndpoint=2,
                options=t.EmberApsOption.APS_OPTION_RETRY,
                groupId=0x0000,
                sequence=0x34,
                radius=0,
            ),
            message_tag=0x42,
            message=b"hello",
        )
    ]


async def test_send_multicast(ezsp_f) -> None:
    ezsp_f.sendMulticast.return_value = (t.sl_Status.OK, 0x0042)

    aps_frame = t.EmberApsFrame(
        profileId=0x0104,
        clusterId=0x0006,
        sourceEndpoint=1,
        destinationEndpoint=2,
        options=t.EmberApsOption.APS_OPTION_RETRY,
        groupId=0x1234,
        sequence=0x34,
    )

    status, message_tag = await ezsp_f.send_multicast(
        aps_frame=aps_frame,
        radius=12,
        non_member_radius=34,
        message_tag=0x42,
        data=b"hello",
    )

    assert status == t.sl_Status.OK
    assert message_tag == 0x42
    assert ezsp_f.sendMulticast.mock_calls == [
        call(
            aps_frame=t.EmberApsFrameV18(
                profileId=0x0104,
                clusterId=0x0006,
                sourceEndpoint=1,
                destinationEndpoint=2,
                options=t.EmberApsOption.APS_OPTION_RETRY,
                groupId=0x1234,
                sequence=0x34,
                radius=12,
            ),
            hops=12,
            broadcast_addr=t.BroadcastAddress.RX_ON_WHEN_IDLE,
            alias=0x0000,
            sequence=0x34,
            message_tag=0x0042,
            message=b"hello",
        )
    ]


async def test_send_broadcast(ezsp_f) -> None:
    ezsp_f.sendBroadcast.return_value = (t.sl_Status.OK, 0x0042)

    aps_frame = t.EmberApsFrame(
        profileId=0x0104,
        clusterId=0x0006,
        sourceEndpoint=1,
        destinationEndpoint=2,
        options=t.EmberApsOption.APS_OPTION_RETRY,
        groupId=0x0000,
        sequence=0x34,
    )

    status, message_tag = await ezsp_f.send_broadcast(
        address=t.BroadcastAddress.ALL_ROUTERS_AND_COORDINATOR,
        aps_frame=aps_frame,
        radius=12,
        message_tag=0x42,
        aps_sequence=34,
        data=b"hello",
    )

    assert status == t.sl_Status.OK
    assert message_tag == 0x42
    assert ezsp_f.sendBroadcast.mock_calls == [
        call(
            alias=0x0000,
            destination=t.BroadcastAddress.ALL_ROUTERS_AND_COORDINATOR,
            sequence=34,
            aps_frame=t.EmberApsFrameV18(
                profileId=0x0104,
                clusterId=0x0006,
                sourceEndpoint=1,
                destinationEndpoint=2,
                options=t.EmberApsOption.APS_OPTION_RETRY,
                groupId=0x0000,
                sequence=0x34,
                radius=12,
            ),
            radius=12,
            message_tag=0x42,
            message=b"hello",
        )
    ]
