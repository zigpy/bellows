from unittest.mock import MagicMock, call

import pytest
import zigpy.exceptions
import zigpy.state

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
