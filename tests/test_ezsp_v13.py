from unittest.mock import AsyncMock, MagicMock, call, patch

import pytest
import zigpy.exceptions
import zigpy.state

import bellows.ezsp.v13
import bellows.types as t

from tests.common import mock_ezsp_commands


@pytest.fixture
def ezsp_f():
    """EZSP v13 protocol handler."""
    ezsp = bellows.ezsp.v13.EZSPv13(MagicMock(), MagicMock())
    mock_ezsp_commands(ezsp)

    return ezsp


def test_ezsp_frame(ezsp_f):
    ezsp_f._seq = 0x22
    data = ezsp_f._ezsp_frame("version", 13)
    assert data == b"\x22\x00\x01\x00\x00\x0d"


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
        "importTransientKey",
        new=AsyncMock(return_value=[t.sl_Status.OK]),
    )
    with p1 as pre_permit_mock, p2 as tclk_mock:
        await ezsp_f.pre_permit(-1.9)
    assert pre_permit_mock.await_count == 2
    assert tclk_mock.await_count == 1


async def test_read_link_keys(ezsp_f):
    def export_link_key_by_index(index):
        if index == 0:
            return (
                t.EUI64.convert("CC:CC:CC:FF:FE:E6:8E:CA"),
                t.KeyData.convert("857C05003E761AF9689A49416A605C76"),
                t.SecurityManagerAPSKeyMetadata(
                    bitmask=(
                        t.EmberKeyStructBitmask.KEY_IS_AUTHORIZED
                        | t.EmberKeyStructBitmask.KEY_HAS_PARTNER_EUI64
                        | t.EmberKeyStructBitmask.KEY_HAS_INCOMING_FRAME_COUNTER
                        | t.EmberKeyStructBitmask.KEY_HAS_OUTGOING_FRAME_COUNTER
                    ),
                    outgoing_frame_counter=3792973670,
                    incoming_frame_counter=1083290572,
                    ttl_in_seconds=0,
                ),
                t.sl_Status.OK,
            )
        elif index == 1:
            return (
                t.EUI64.convert("EC:1B:BD:FF:FE:2F:41:A4"),
                t.KeyData.convert("CA02E8BB757C94F89339D39CB3CDA7BE"),
                t.SecurityManagerAPSKeyMetadata(
                    bitmask=(
                        t.EmberKeyStructBitmask.KEY_IS_AUTHORIZED
                        | t.EmberKeyStructBitmask.KEY_HAS_PARTNER_EUI64
                        | t.EmberKeyStructBitmask.KEY_HAS_INCOMING_FRAME_COUNTER
                        | t.EmberKeyStructBitmask.KEY_HAS_OUTGOING_FRAME_COUNTER
                    ),
                    outgoing_frame_counter=2597245184,
                    incoming_frame_counter=824424412,
                    ttl_in_seconds=0,
                ),
                t.sl_Status.OK,
            )

        return (
            t.EUI64.convert("7f:c9:35:e1:b0:00:00:00"),
            t.KeyData.convert("80:45:38:73:55:00:00:00:08:e4:35:c9:7f:00:00:00"),
            t.SecurityManagerAPSKeyMetadata(
                bitmask=t.EmberKeyStructBitmask(43976),
                outgoing_frame_counter=85,
                incoming_frame_counter=0,
                ttl_in_seconds=0,
            ),
            t.sl_Status.NOT_FOUND,
        )

    ezsp_f.exportLinkKeyByIndex.side_effect = export_link_key_by_index
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
    def export_key(context):
        key = {
            t.SecurityManagerKeyType.NETWORK: t.KeyData.convert(
                "2ccade06b3090c310315b3d574d3c85a"
            ),
            t.SecurityManagerKeyType.TC_LINK: t.KeyData.convert(
                "abcdabcdabcdabcdabcdabcdabcdabcd"
            ),
        }[context.core_key_type]

        return (key, t.EmberStatus.SUCCESS)

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
        t.KeyData.convert("2ccade06b3090c310315b3d574d3c85a"),
        t.EmberStatus.SUCCESS,
    ]

    with pytest.raises(zigpy.exceptions.NetworkNotFormed):
        await ezsp_f.get_network_key()


async def test_write_link_keys(ezsp_f):
    ezsp_f.importLinkKey.side_effect = [
        (t.EmberStatus.SUCCESS,),
        (t.EmberStatus.INVALID_CALL,),
    ]

    await ezsp_f.write_link_keys(
        [
            zigpy.state.Key(
                key=t.KeyData.convert(
                    "85:7C:05:00:3E:76:1A:F9:68:9A:49:41:6A:60:5C:76"
                ),
                tx_counter=3792973670,
                rx_counter=1083290572,
                seq=0,  # Sequence number is 0
                partner_ieee=t.EUI64.convert("CC:CC:CC:FF:FE:E6:8E:CA"),
            ),
            zigpy.state.Key(
                key=t.KeyData.convert(
                    "CA:02:E8:BB:75:7C:94:F8:93:39:D3:9C:B3:CD:A7:BE"
                ),
                tx_counter=2597245184,
                rx_counter=824424412,
                seq=0,  # Sequence number is 0
                partner_ieee=t.EUI64.convert("EC:1B:BD:FF:FE:2F:41:A4"),
            ),
        ]
    )

    assert ezsp_f.importLinkKey.mock_calls == [
        call(
            index=0,
            address=t.EUI64.convert("CC:CC:CC:FF:FE:E6:8E:CA"),
            key=t.KeyData.convert("85:7C:05:00:3E:76:1A:F9:68:9A:49:41:6A:60:5C:76"),
        ),
        call(
            index=1,
            address=t.EUI64.convert("EC:1B:BD:FF:FE:2F:41:A4"),
            key=t.KeyData.convert("CA:02:E8:BB:75:7C:94:F8:93:39:D3:9C:B3:CD:A7:BE"),
        ),
    ]


async def test_factory_reset(ezsp_f) -> None:
    ezsp_f.clearKeyTable.return_value = (t.EmberStatus.SUCCESS,)
    ezsp_f.tokenFactoryReset.return_value = (t.EmberStatus.SUCCESS,)
    await ezsp_f.factory_reset()

    assert ezsp_f.clearKeyTable.mock_calls == [call()]
    assert ezsp_f.tokenFactoryReset.mock_calls == [
        call(excludeOutgoingFC=False, excludeBootCounter=False)
    ]
