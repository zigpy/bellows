import logging
from unittest.mock import AsyncMock, MagicMock, call

import pytest
import zigpy.state

import bellows.ezsp.v4
import bellows.types as t


@pytest.fixture
def ezsp_f():
    """EZSP v4 protocol handler."""
    return bellows.ezsp.v4.EZSPv4(MagicMock(), MagicMock())


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

    ezsp_f.getChildData = AsyncMock(side_effect=get_child_data)

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
                ezsp_f.types.EmberKeyStruct(
                    bitmask=(
                        t.EmberKeyStructBitmask.KEY_IS_AUTHORIZED
                        | t.EmberKeyStructBitmask.KEY_HAS_PARTNER_EUI64
                        | t.EmberKeyStructBitmask.KEY_HAS_INCOMING_FRAME_COUNTER
                        | t.EmberKeyStructBitmask.KEY_HAS_OUTGOING_FRAME_COUNTER
                    ),
                    type=ezsp_f.types.EmberKeyType.APPLICATION_LINK_KEY,
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
                ezsp_f.types.EmberKeyStruct(
                    bitmask=(
                        t.EmberKeyStructBitmask.KEY_IS_AUTHORIZED
                        | t.EmberKeyStructBitmask.KEY_HAS_PARTNER_EUI64
                        | t.EmberKeyStructBitmask.KEY_HAS_INCOMING_FRAME_COUNTER
                        | t.EmberKeyStructBitmask.KEY_HAS_OUTGOING_FRAME_COUNTER
                    ),
                    type=ezsp_f.types.EmberKeyType.APPLICATION_LINK_KEY,
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
            ezsp_f.types.EmberKeyStruct(
                bitmask=t.EmberKeyStructBitmask(244),
                type=ezsp_f.types.EmberKeyType(0x46),
                key=t.KeyData.convert("b8a11c004b1200cdabcdabcdabcdabcd"),
                outgoingFrameCounter=8192,
                incomingFrameCounter=0,
                sequenceNumber=0,
                partnerEUI64=t.EUI64.convert("00:12:4b:00:1c:a1:b8:46"),
            ),
        )

    ezsp_f.getKeyTableEntry = AsyncMock(side_effect=get_key_table_entry)
    ezsp_f.getConfigurationValue = AsyncMock(return_value=(t.EmberStatus.SUCCESS, 13))

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
    def get_key(key_type):
        key = {
            ezsp_f.types.EmberKeyType.CURRENT_NETWORK_KEY: ezsp_f.types.EmberKeyStruct(
                bitmask=(
                    t.EmberKeyStructBitmask.KEY_HAS_OUTGOING_FRAME_COUNTER
                    | t.EmberKeyStructBitmask.KEY_HAS_SEQUENCE_NUMBER
                ),
                type=ezsp_f.types.EmberKeyType.CURRENT_NETWORK_KEY,
                key=t.KeyData.convert("2ccade06b3090c310315b3d574d3c85a"),
                outgoingFrameCounter=118785,
                incomingFrameCounter=0,
                sequenceNumber=108,
                partnerEUI64=t.EUI64.convert("00:00:00:00:00:00:00:00"),
            ),
            ezsp_f.types.EmberKeyType.TRUST_CENTER_LINK_KEY: ezsp_f.types.EmberKeyStruct(
                bitmask=(
                    t.EmberKeyStructBitmask.KEY_IS_AUTHORIZED
                    | t.EmberKeyStructBitmask.KEY_HAS_PARTNER_EUI64
                    | t.EmberKeyStructBitmask.KEY_HAS_OUTGOING_FRAME_COUNTER
                ),
                type=ezsp_f.types.EmberKeyType.TRUST_CENTER_LINK_KEY,
                key=t.KeyData.convert("abcdabcdabcdabcdabcdabcdabcdabcd"),
                outgoingFrameCounter=8712428,
                incomingFrameCounter=0,
                sequenceNumber=0,
                partnerEUI64=t.EUI64.convert("00:12:4b:00:1c:a1:b8:46"),
            ),
        }[key_type]

        return (t.EmberStatus.SUCCESS, key)

    ezsp_f.getKey = AsyncMock(side_effect=get_key)

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
    ezsp_f.addOrUpdateKeyTableEntry = AsyncMock(
        side_effect=[(t.EmberStatus.SUCCESS,), (t.EmberStatus.ERR_FATAL,)]
    )

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
            t.EUI64.convert("11:11:11:11:11:11:11:11"),
            True,
            t.KeyData.convert("2ccade06b3090c310315b3d574d3c85a"),
        ),
        call(
            t.EUI64.convert("22:22:22:22:22:22:22:22"),
            True,
            t.KeyData.convert("abcdabcdabcdabcdabcdabcdabcdabcd"),
        ),
    ]

    assert (
        "Couldn't add Key(key=ab:cd:ab:cd:ab:cd:ab:cd:ab:cd:ab:cd:ab:cd:ab:cd"
        in caplog.text
    )


async def test_initialize_network(ezsp_f) -> None:
    ezsp_f.networkInitExtended = AsyncMock(return_value=(t.EmberStatus.SUCCESS,))
    assert await ezsp_f.initialize_network() == t.sl_Status.OK
    assert ezsp_f.networkInitExtended.mock_calls == [call(0x0000)]


async def test_write_nwk_frame_counter(ezsp_f) -> None:
    # No-op
    await ezsp_f.write_nwk_frame_counter(12345678)


async def test_write_aps_frame_counter(ezsp_f) -> None:
    # No-op
    await ezsp_f.write_aps_frame_counter(12345678)


async def test_factory_reset(ezsp_f) -> None:
    ezsp_f.clearKeyTable = AsyncMock(return_value=(t.EmberStatus.SUCCESS,))
    await ezsp_f.factory_reset()

    assert ezsp_f.clearKeyTable.mock_calls == [call()]
