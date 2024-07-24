import logging
from unittest.mock import MagicMock, call

import pytest
import zigpy.state

import bellows.ezsp.v4
import bellows.types as t

from tests.common import mock_ezsp_commands


@pytest.fixture
def ezsp_f():
    """EZSP v4 protocol handler."""
    ezsp = bellows.ezsp.v4.EZSPv4(MagicMock(), MagicMock())
    mock_ezsp_commands(ezsp)

    return ezsp


def test_ezsp_frame(ezsp_f):
    ezsp_f._seq = 0x22
    data = ezsp_f._ezsp_frame("version", 6)
    assert data == b"\x22\x00\x00\x06"


def test_ezsp_frame_rx(ezsp_f):
    """Test receiving a version frame."""
    ezsp_f(b"\x01\x00\x00\x01\x02\x34\x12")
    assert ezsp_f._handle_callback.call_count == 1
    assert ezsp_f._handle_callback.call_args[0][0] == "version"
    assert ezsp_f._handle_callback.call_args[0][1] == [0x01, 0x02, 0x1234]


async def test_pre_permit(ezsp_f):
    """Test pre permit."""
    await ezsp_f.pre_permit(1.9)


async def test_read_child_data(ezsp_f):
    def get_child_data(index):
        if index == 0:
            status = t.EmberStatus.SUCCESS
        else:
            status = t.EmberStatus.NOT_JOINED

        return (
            status,
            t.EmberNodeId(0xC06B),
            t.EUI64.convert("00:0b:57:ff:fe:2b:d4:57"),
            t.EmberNodeType.SLEEPY_END_DEVICE,
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


async def test_read_link_keys(ezsp_f):
    def get_key_table_entry(index):
        if index == 0:
            return (
                t.EmberStatus.SUCCESS,
                t.EmberKeyStruct(
                    bitmask=(
                        t.EmberKeyStructBitmask.KEY_IS_AUTHORIZED
                        | t.EmberKeyStructBitmask.KEY_HAS_PARTNER_EUI64
                        | t.EmberKeyStructBitmask.KEY_HAS_INCOMING_FRAME_COUNTER
                        | t.EmberKeyStructBitmask.KEY_HAS_OUTGOING_FRAME_COUNTER
                    ),
                    type=t.EmberKeyType.APPLICATION_LINK_KEY,
                    key=t.KeyData.convert("857C05003E761AF9689A49416A605C76"),
                    outgoingFrameCounter=3792973670,
                    incomingFrameCounter=1083290572,
                    sequenceNumber=147,
                    partnerEUI64=t.EUI64.convert("CC:CC:CC:FF:FE:E6:8E:CA"),
                ),
            )
        elif index == 1:
            return (
                t.EmberStatus.SUCCESS,
                t.EmberKeyStruct(
                    bitmask=(
                        t.EmberKeyStructBitmask.KEY_IS_AUTHORIZED
                        | t.EmberKeyStructBitmask.KEY_HAS_PARTNER_EUI64
                        | t.EmberKeyStructBitmask.KEY_HAS_INCOMING_FRAME_COUNTER
                        | t.EmberKeyStructBitmask.KEY_HAS_OUTGOING_FRAME_COUNTER
                    ),
                    type=t.EmberKeyType.APPLICATION_LINK_KEY,
                    key=t.KeyData.convert("CA02E8BB757C94F89339D39CB3CDA7BE"),
                    outgoingFrameCounter=2597245184,
                    incomingFrameCounter=824424412,
                    sequenceNumber=19,
                    partnerEUI64=t.EUI64.convert("EC:1B:BD:FF:FE:2F:41:A4"),
                ),
            )
        elif index >= 12:
            status = t.EmberStatus.INDEX_OUT_OF_RANGE
        else:
            status = t.EmberStatus.TABLE_ENTRY_ERASED

        return (
            status,
            t.EmberKeyStruct(
                bitmask=t.EmberKeyStructBitmask(244),
                type=t.EmberKeyType(0x46),
                key=t.KeyData.convert("b8a11c004b1200cdabcdabcdabcdabcd"),
                outgoingFrameCounter=8192,
                incomingFrameCounter=0,
                sequenceNumber=0,
                partnerEUI64=t.EUI64.convert("00:12:4b:00:1c:a1:b8:46"),
            ),
        )

    ezsp_f.getKeyTableEntry.side_effect = get_key_table_entry
    ezsp_f.getConfigurationValue.return_value = (t.EmberStatus.SUCCESS, 13)

    link_keys = [key async for key in ezsp_f.read_link_keys()]
    assert link_keys == [
        zigpy.state.Key(
            key=t.KeyData.convert("85:7C:05:00:3E:76:1A:F9:68:9A:49:41:6A:60:5C:76"),
            tx_counter=3792973670,
            rx_counter=1083290572,
            seq=0,  # Sequence number is 0
            partner_ieee=t.EUI64.convert("CC:CC:CC:FF:FE:E6:8E:CA"),
        ),
        zigpy.state.Key(
            key=t.KeyData.convert("CA:02:E8:BB:75:7C:94:F8:93:39:D3:9C:B3:CD:A7:BE"),
            tx_counter=2597245184,
            rx_counter=824424412,
            seq=0,  # Sequence number is 0
            partner_ieee=t.EUI64.convert("EC:1B:BD:FF:FE:2F:41:A4"),
        ),
    ]


async def test_get_network_key_and_tc_link_key(ezsp_f):
    def get_key(keyType):
        key = {
            t.EmberKeyType.CURRENT_NETWORK_KEY: t.EmberKeyStruct(
                bitmask=(
                    t.EmberKeyStructBitmask.KEY_HAS_OUTGOING_FRAME_COUNTER
                    | t.EmberKeyStructBitmask.KEY_HAS_SEQUENCE_NUMBER
                ),
                type=t.EmberKeyType.CURRENT_NETWORK_KEY,
                key=t.KeyData.convert("2ccade06b3090c310315b3d574d3c85a"),
                outgoingFrameCounter=118785,
                incomingFrameCounter=0,
                sequenceNumber=108,
                partnerEUI64=t.EUI64.convert("00:00:00:00:00:00:00:00"),
            ),
            t.EmberKeyType.TRUST_CENTER_LINK_KEY: t.EmberKeyStruct(
                bitmask=(
                    t.EmberKeyStructBitmask.KEY_IS_AUTHORIZED
                    | t.EmberKeyStructBitmask.KEY_HAS_PARTNER_EUI64
                    | t.EmberKeyStructBitmask.KEY_HAS_OUTGOING_FRAME_COUNTER
                ),
                type=t.EmberKeyType.TRUST_CENTER_LINK_KEY,
                key=t.KeyData.convert("abcdabcdabcdabcdabcdabcdabcdabcd"),
                outgoingFrameCounter=8712428,
                incomingFrameCounter=0,
                sequenceNumber=0,
                partnerEUI64=t.EUI64.convert("00:12:4b:00:1c:a1:b8:46"),
            ),
        }[keyType]

        return (t.EmberStatus.SUCCESS, key)

    ezsp_f.getKey.side_effect = get_key

    assert (await ezsp_f.get_network_key()) == zigpy.state.Key(
        key=t.KeyData.convert("2ccade06b3090c310315b3d574d3c85a"),
        seq=108,
        tx_counter=118785,
    )

    assert (await ezsp_f.get_tc_link_key()) == zigpy.state.Key(
        key=t.KeyData.convert("abcdabcdabcdabcdabcdabcdabcdabcd"),
        seq=0,
        tx_counter=8712428,
        partner_ieee=t.EUI64.convert("00:12:4b:00:1c:a1:b8:46"),
    )


async def test_write_child_data(ezsp_f) -> None:
    # It's a no-op
    await ezsp_f.write_child_data(
        {
            t.EUI64.convert("00:0b:57:ff:fe:2b:d4:57"): 0xC06B,
            t.EUI64.convert("00:18:4b:00:1c:a1:b8:46"): 0x1234,
        }
    )


async def test_read_address_table(ezsp_f) -> None:
    # It's a no-op but still an async generator
    async for nwk, eui64 in ezsp_f.read_address_table():
        pass


async def test_write_link_keys(ezsp_f, caplog) -> None:
    ezsp_f.addOrUpdateKeyTableEntry.side_effect = [
        (t.EmberStatus.SUCCESS,),
        (t.EmberStatus.ERR_FATAL,),
    ]

    with caplog.at_level(logging.WARNING):
        await ezsp_f.write_link_keys(
            [
                zigpy.state.Key(
                    key=t.KeyData.convert("2ccade06b3090c310315b3d574d3c85a"),
                    seq=108,
                    tx_counter=1234,
                    rx_counter=5678,
                    partner_ieee=t.EUI64.convert("11:11:11:11:11:11:11:11"),
                ),
                zigpy.state.Key(
                    key=t.KeyData.convert("abcdabcdabcdabcdabcdabcdabcdabcd"),
                    seq=123,
                    tx_counter=2345,
                    rx_counter=98314,
                    partner_ieee=t.EUI64.convert("22:22:22:22:22:22:22:22"),
                ),
            ]
        )

    assert ezsp_f.addOrUpdateKeyTableEntry.mock_calls == [
        call(
            address=t.EUI64.convert("11:11:11:11:11:11:11:11"),
            linkKey=True,
            keyData=t.KeyData.convert("2ccade06b3090c310315b3d574d3c85a"),
        ),
        call(
            address=t.EUI64.convert("22:22:22:22:22:22:22:22"),
            linkKey=True,
            keyData=t.KeyData.convert("abcdabcdabcdabcdabcdabcdabcdabcd"),
        ),
    ]

    assert (
        "Couldn't add Key(key=ab:cd:ab:cd:ab:cd:ab:cd:ab:cd:ab:cd:ab:cd:ab:cd"
        in caplog.text
    )


async def test_initialize_network(ezsp_f) -> None:
    ezsp_f.networkInitExtended.return_value = (t.EmberStatus.SUCCESS,)
    assert await ezsp_f.initialize_network() == t.sl_Status.OK
    assert ezsp_f.networkInitExtended.mock_calls == [
        call(networkInitStruct=t.EmberNetworkInitBitmask.NETWORK_INIT_NO_OPTIONS)
    ]


async def test_write_nwk_frame_counter(ezsp_f) -> None:
    # No-op
    await ezsp_f.write_nwk_frame_counter(12345678)


async def test_write_aps_frame_counter(ezsp_f) -> None:
    # No-op
    await ezsp_f.write_aps_frame_counter(12345678)


async def test_factory_reset(ezsp_f) -> None:
    ezsp_f.clearKeyTable.return_value = (t.EmberStatus.SUCCESS,)
    await ezsp_f.factory_reset()

    assert ezsp_f.clearKeyTable.mock_calls == [call()]


async def test_send_unicast(ezsp_f) -> None:
    ezsp_f.sendUnicast.return_value = (t.EmberStatus.SUCCESS, 0x42)
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
            type=t.EmberOutgoingMessageType.OUTGOING_DIRECT,
            indexOrDestination=t.EmberNodeId(0x1234),
            apsFrame=t.EmberApsFrame(),
            messageTag=0x42,
            messageContents=b"hello",
        )
    ]


async def test_send_multicast(ezsp_f) -> None:
    ezsp_f.sendMulticast.return_value = (t.EmberStatus.SUCCESS, 0x42)
    status, message_tag = await ezsp_f.send_multicast(
        aps_frame=t.EmberApsFrame(),
        radius=12,
        non_member_radius=34,
        message_tag=0x42,
        data=b"hello",
    )

    assert status == t.sl_Status.OK
    assert message_tag == 0x42
    assert ezsp_f.sendMulticast.mock_calls == [
        call(
            apsFrame=t.EmberApsFrame(),
            hops=12,
            nonmemberRadius=34,
            messageTag=0x42,
            messageContents=b"hello",
        )
    ]


async def test_send_broadcast(ezsp_f) -> None:
    ezsp_f.sendBroadcast.return_value = (t.EmberStatus.SUCCESS, 0x42)
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
            destination=t.BroadcastAddress.ALL_ROUTERS_AND_COORDINATOR,
            apsFrame=t.EmberApsFrame(),
            radius=12,
            messageTag=0x42,
            messageContents=b"hello",
        )
    ]


async def test_source_route(ezsp_f) -> None:
    ezsp_f.setSourceRoute.return_value = (t.EmberStatus.SUCCESS,)

    status = await ezsp_f.set_source_route(nwk=0x1234, relays=[0x5678, 0xABCD])
    assert status == t.sl_Status.OK

    assert ezsp_f.setSourceRoute.mock_calls == [
        call(destination=0x1234, relayList=[0x5678, 0xABCD])
    ]


async def test_add_transient_link_key(ezsp_f) -> None:
    # It's a no-op
    status = await ezsp_f.add_transient_link_key(
        ieee=t.EUI64.convert("ff:ff:ff:ff:ff:ff:ff:ff"),
        key=t.KeyData("ZigBeeAlliance09"),
    )
    assert status == t.sl_Status.OK
