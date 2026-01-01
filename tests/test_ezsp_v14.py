from unittest.mock import MagicMock, call

import pytest
import zigpy.exceptions
import zigpy.state
import zigpy.types

import bellows.ezsp.v14
import bellows.types as t

from tests.common import mock_ezsp_commands


@pytest.fixture
def ezsp_f():
    """EZSP v14 protocol handler."""
    ezsp = bellows.ezsp.v14.EZSPv14(MagicMock(), MagicMock())
    mock_ezsp_commands(ezsp)

    return ezsp


def test_ezsp_frame(ezsp_f):
    ezsp_f._seq = 0x22
    data = ezsp_f._ezsp_frame("version", 14)
    assert data == b"\x22\x00\x01\x00\x00\x0e"


def test_ezsp_frame_rx(ezsp_f):
    """Test receiving a version frame."""
    ezsp_f(b"\x01\x01\x80\x00\x00\x01\x02\x34\x12")
    assert ezsp_f._handle_callback.call_count == 1
    assert ezsp_f._handle_callback.call_args[0][0] == "version"
    assert ezsp_f._handle_callback.call_args[0][1] == [0x01, 0x02, 0x1234]


async def test_read_address_table(ezsp_f):
    def get_addr_table_info(index):
        default = (
            t.sl_Status.OK,
            t.EmberNodeId(0xFFFF),
            t.EUI64.convert("ff:ff:ff:ff:ff:ff:ff:ff"),
        )
        return {
            16: (
                t.sl_Status.OK,
                t.EmberNodeId(0x44CB),
                t.EUI64.convert("cc:cc:cc:ff:fe:e6:8e:ca"),
            ),
            17: (
                t.sl_Status.OK,
                t.EmberNodeId(0x0702),
                t.EUI64.convert("ec:1b:bd:ff:fe:2f:41:a4"),
            ),
            # Not actually seen with a real adapter
            18: (
                t.sl_Status.FAIL,
                t.EmberNodeId(0x1234),
                t.EUI64.convert("ab:cd:ab:cd:ab:cd:ab:cd"),
            ),
        }.get(index, default)

    ezsp_f.getAddressTableInfo.side_effect = get_addr_table_info
    ezsp_f.getConfigurationValue.return_value = (t.sl_Status.OK, 20)

    address_table = [key async for key in ezsp_f.read_address_table()]
    assert address_table == [
        (0x44CB, t.EUI64.convert("cc:cc:cc:ff:fe:e6:8e:ca")),
        (0x0702, t.EUI64.convert("ec:1b:bd:ff:fe:2f:41:a4")),
    ]


async def test_get_network_key_and_tc_link_key(ezsp_f):
    def export_key(context):
        if context.core_key_type == t.SecurityManagerKeyType.NETWORK:
            return (
                t.sl_Status.OK,
                t.KeyData.convert("2ccade06b3090c310315b3d574d3c85a"),
                t.SecurityManagerContextV13(
                    core_key_type=t.SecurityManagerKeyType.NETWORK,
                    key_index=0,
                    derived_type=t.SecurityManagerDerivedKeyTypeV13.NONE,
                    eui64=t.EUI64.convert("00:00:00:00:00:00:00:00"),
                    multi_network_index=0,
                    flags=t.SecurityManagerContextFlags.NONE,
                    psa_key_alg_permission=0,
                ),
            )
        elif context.core_key_type == t.SecurityManagerKeyType.TC_LINK:
            return (
                t.sl_Status.OK,
                t.KeyData.convert("abcdabcdabcdabcdabcdabcdabcdabcd"),
                t.SecurityManagerContextV13(
                    core_key_type=t.SecurityManagerKeyType.NETWORK,
                    key_index=0,
                    derived_type=t.SecurityManagerDerivedKeyTypeV13.NONE,
                    eui64=t.EUI64.convert("00:00:00:00:00:00:00:00"),
                    multi_network_index=0,
                    flags=t.SecurityManagerContextFlags.NONE,
                    psa_key_alg_permission=0,
                ),
            )
        else:
            pytest.fail("Invalid core_key_type")

    ezsp_f.exportKey.side_effect = export_key
    ezsp_f.getNetworkKeyInfo.return_value = [
        t.sl_Status.OK,
        t.SecurityManagerNetworkKeyInfo(
            network_key_set=True,
            alternate_network_key_set=False,
            network_key_sequence_number=108,
            alt_network_key_sequence_number=0,
            network_key_frame_counter=118785,
        ),
    ]

    assert (await ezsp_f.get_network_key()) == zigpy.state.Key(
        key=t.KeyData.convert("2ccade06b3090c310315b3d574d3c85a"),
        seq=108,
        tx_counter=118785,
    )

    assert (await ezsp_f.get_tc_link_key()) == zigpy.state.Key(
        key=t.KeyData.convert("abcdabcdabcdabcdabcdabcdabcdabcd"),
    )


async def test_get_network_key_without_network(ezsp_f):
    ezsp_f.getNetworkKeyInfo.return_value = [
        t.sl_Status.OK,
        t.SecurityManagerNetworkKeyInfo(
            network_key_set=False,  # Not set
            alternate_network_key_set=False,
            network_key_sequence_number=108,
            alt_network_key_sequence_number=0,
            network_key_frame_counter=118785,
        ),
    ]

    ezsp_f.exportKey.return_value = [
        t.sl_Status.OK,
        t.KeyData.convert("00000000000000000000000000000000"),
        t.SecurityManagerContextV13(
            core_key_type=t.SecurityManagerKeyType.NETWORK,
            key_index=0,
            derived_type=t.SecurityManagerDerivedKeyTypeV13.NONE,
            eui64=t.EUI64.convert("00:00:00:00:00:00:00:00"),
            multi_network_index=0,
            flags=t.SecurityManagerContextFlags.NONE,
            psa_key_alg_permission=0,
        ),
    ]

    with pytest.raises(zigpy.exceptions.NetworkNotFormed):
        await ezsp_f.get_network_key()


async def test_send_unicast(ezsp_f) -> None:
    ezsp_f.sendUnicast.return_value = (t.sl_Status.OK, 0x0042)
    status, message_tag = await ezsp_f.send_unicast(
        nwk=0x1234,
        aps_frame=t.EmberApsFrame(),
        message_tag=0x42,
        data=b"hello",
    )

    assert status == t.sl_Status.OK
    assert message_tag == 0x42
    assert ezsp_f.sendUnicast.mock_calls == [
        call(
            message_type=t.EmberOutgoingMessageType.OUTGOING_DIRECT,
            nwk=0x1234,
            aps_frame=t.EmberApsFrame(),
            message_tag=0x42,
            message=b"hello",
        )
    ]


async def test_send_multicast(ezsp_f) -> None:
    ezsp_f.sendMulticast.return_value = (t.sl_Status.OK, 0x0042)
    status, message_tag = await ezsp_f.send_multicast(
        aps_frame=t.EmberApsFrame(sequence=0x34),
        radius=12,
        non_member_radius=34,
        message_tag=0x42,
        data=b"hello",
    )

    assert status == t.sl_Status.OK
    assert message_tag == 0x42
    assert ezsp_f.sendMulticast.mock_calls == [
        call(
            aps_frame=t.EmberApsFrame(sequence=0x34),
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
    status, message_tag = await ezsp_f.send_broadcast(
        address=t.BroadcastAddress.ALL_ROUTERS_AND_COORDINATOR,
        aps_frame=t.EmberApsFrame(),
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
            aps_frame=t.EmberApsFrame(),
            radius=12,
            message_tag=0x42,
            message=b"hello",
        )
    ]


@pytest.mark.parametrize(
    "message_type, expected_dst",
    [
        (
            t.EmberIncomingMessageType.INCOMING_UNICAST,
            None,
        ),
        (
            t.EmberIncomingMessageType.INCOMING_BROADCAST,
            zigpy.types.AddrModeAddress(
                addr_mode=zigpy.types.AddrMode.Broadcast,
                address=zigpy.types.BroadcastAddress.ALL_ROUTERS_AND_COORDINATOR,
            ),
        ),
        (
            t.EmberIncomingMessageType.INCOMING_MULTICAST,
            zigpy.types.AddrModeAddress(
                addr_mode=zigpy.types.AddrMode.Group,
                address=0x1234,
            ),
        ),
    ],
)
def test_incoming_message_handler(ezsp_f, message_type, expected_dst) -> None:
    """Test incomingMessageHandler emits packet_received event."""
    received_packets = []
    ezsp_f.on_event("packet_received", lambda pkt: received_packets.append(pkt))

    aps_frame = t.EmberApsFrame(
        profileId=0x0104,
        clusterId=0x0006,
        sourceEndpoint=1,
        destinationEndpoint=2,
        options=t.EmberApsOption.APS_OPTION_NONE,
        groupId=0x1234,
        sequence=0x42,
    )

    ezsp_f.handle_parsed_callback(
        "incomingMessageHandler",
        [
            message_type,
            aps_frame,
            t.EmberNodeId(0x1234),  # sender nwk
            t.EUI64.convert("aa:bb:cc:dd:ee:ff:00:11"),  # sender eui64
            0,  # binding_index
            0,  # address_index
            200,  # lqi
            -40,  # rssi
            12345678,  # timestamp
            b"test message",  # message
        ],
    )

    assert len(received_packets) == 1
    packet = received_packets[0]
    assert packet.src == zigpy.types.AddrModeAddress(
        addr_mode=zigpy.types.AddrMode.NWK,
        address=zigpy.types.NWK(0x1234),
    )
    assert packet.src_ep == 1
    assert packet.dst == expected_dst
    assert packet.dst_ep == 2
    assert packet.profile_id == 0x0104
    assert packet.cluster_id == 0x0006
    assert packet.data == zigpy.types.SerializableBytes(b"test message")
    assert packet.lqi == 200
    assert packet.rssi == -40


def test_incoming_message_handler_ignored_type(ezsp_f) -> None:
    """Test incomingMessageHandler ignores unknown message types."""
    received_packets = []
    ezsp_f.on_event("packet_received", lambda pkt: received_packets.append(pkt))

    aps_frame = t.EmberApsFrame(options=t.EmberApsOption.APS_OPTION_NONE)
    ezsp_f.handle_parsed_callback(
        "incomingMessageHandler",
        [
            t.EmberIncomingMessageType.INCOMING_MANY_TO_ONE_ROUTE_REQUEST,
            aps_frame,
            t.EmberNodeId(0x1234),
            t.EUI64.convert("aa:bb:cc:dd:ee:ff:00:11"),
            0,
            0,
            200,
            -40,
            12345678,
            b"test",
        ],
    )

    assert len(received_packets) == 0
    # Legacy callback should still be called
    assert ezsp_f._handle_callback.mock_calls == [
        call(
            "incomingMessageHandler",
            [
                t.EmberIncomingMessageType.INCOMING_MANY_TO_ONE_ROUTE_REQUEST,
                aps_frame,
                t.EmberNodeId(0x1234),
                t.EUI64.convert("aa:bb:cc:dd:ee:ff:00:11"),
                0,
                0,
                200,
                -40,
                12345678,
                b"test",
            ],
        )
    ]


def test_message_sent_handler(ezsp_f) -> None:
    """Test messageSentHandler emits message_sent event."""
    sent_messages = []
    ezsp_f.on_event("message_sent", lambda msg: sent_messages.append(msg))

    aps_frame = t.EmberApsFrame(
        profileId=0x0104,
        clusterId=0x0006,
        sourceEndpoint=1,
        destinationEndpoint=2,
        options=t.EmberApsOption.APS_OPTION_NONE,
        groupId=0x0000,
        sequence=0x42,
    )

    ezsp_f.handle_parsed_callback(
        "messageSentHandler",
        [
            t.sl_Status.OK,
            t.EmberOutgoingMessageType.OUTGOING_DIRECT,
            t.EmberNodeId(0x1234),
            aps_frame,
            0x42,  # message_tag
            b"sent message",
        ],
    )

    assert len(sent_messages) == 1
    status, msg_type, destination, frame, tag, message = sent_messages[0]
    assert status == t.sl_Status.OK
    assert msg_type == t.EmberOutgoingMessageType.OUTGOING_DIRECT
    assert destination == t.EmberNodeId(0x1234)
    assert frame == aps_frame
    assert tag == 0x42
    assert message == b"sent message"
