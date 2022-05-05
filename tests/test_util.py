import pytest
import zigpy.state
import zigpy.types as t
import zigpy.zdo.types as zdo_t

import bellows.types as bellows_t
import bellows.zigbee.util as util

from tests.test_application import ezsp_mock


@pytest.fixture
def node_info():
    return zigpy.state.NodeInfo(
        nwk=t.NWK(0x0000),
        ieee=t.EUI64.convert("93:2C:A9:34:D9:D0:5D:12"),
        logical_type=zdo_t.LogicalType.Coordinator,
    )


@pytest.fixture
def network_info(node_info):
    return zigpy.state.NetworkInfo(
        extended_pan_id=t.ExtendedPanId.convert("0D:49:91:99:AE:CD:3C:35"),
        pan_id=t.PanId(0x9BB0),
        nwk_update_id=0x12,
        nwk_manager_id=t.NWK(0x0000),
        channel=t.uint8_t(15),
        channel_mask=t.Channels.from_channel_list([15, 20, 25]),
        security_level=t.uint8_t(5),
        network_key=zigpy.state.Key(
            key=t.KeyData.convert("9A:79:D6:9A:DA:EC:45:C6:F2:EF:EB:AF:DA:A3:07:B6"),
            seq=108,
            tx_counter=39009277,
        ),
        tc_link_key=zigpy.state.Key(
            key=t.KeyData(b"ZigBeeAlliance09"),
            partner_ieee=node_info.ieee,
            tx_counter=8712428,
        ),
        key_table=[],
        children=[],
        nwk_addresses={},
        stack_specific={"ezsp": {"hashed_tclk": "71e31105bb92a2d15747a0d0a042dbfd"}},
    )


@pytest.fixture
def zigpy_key():
    return zigpy.state.Key(
        key=t.KeyData.convert("9A:79:D6:9A:DA:EC:45:C6:F2:EF:EB:AF:DA:A3:07:B6"),
        seq=108,
        tx_counter=39009277,
        rx_counter=1234567,
        partner_ieee=t.EUI64.convert("0D:49:91:99:AE:CD:3C:35"),
    )


@pytest.fixture
def ezsp_key(ezsp_mock):
    ezsp = ezsp_mock
    return ezsp.types.EmberKeyStruct(
        bitmask=(
            ezsp.types.EmberKeyStructBitmask.KEY_HAS_SEQUENCE_NUMBER
            | ezsp.types.EmberKeyStructBitmask.KEY_HAS_OUTGOING_FRAME_COUNTER
            | ezsp.types.EmberKeyStructBitmask.KEY_HAS_INCOMING_FRAME_COUNTER
            | ezsp.types.EmberKeyStructBitmask.KEY_HAS_PARTNER_EUI64
        ),
        key=ezsp.types.EmberKeyData(bytes.fromhex("9A79D69ADAEC45C6F2EFEBAFDAA307B6")),
        sequenceNumber=108,
        outgoingFrameCounter=39009277,
        incomingFrameCounter=1234567,
        partnerEUI64=bellows_t.EmberEUI64.convert("0D:49:91:99:AE:CD:3C:35"),
    )


def test_zha_security_normal(network_info, node_info):
    security = util.zha_security(
        network_info=network_info, node_info=node_info, use_hashed_tclk=True
    )

    assert (
        security.preconfiguredTrustCenterEui64 == network_info.tc_link_key.partner_ieee
    )
    assert (
        security.bitmask & bellows_t.EmberInitialSecurityBitmask.HAVE_TRUST_CENTER_EUI64
        == bellows_t.EmberInitialSecurityBitmask.HAVE_TRUST_CENTER_EUI64
    )

    assert (
        security.preconfiguredKey.serialize().hex()
        == network_info.stack_specific["ezsp"]["hashed_tclk"]
    )
    assert (
        security.bitmask
        & bellows_t.EmberInitialSecurityBitmask.TRUST_CENTER_USES_HASHED_LINK_KEY
        == bellows_t.EmberInitialSecurityBitmask.TRUST_CENTER_USES_HASHED_LINK_KEY
    )


def test_zha_security_router(network_info, node_info):
    router_node_info = node_info.replace(logical_type=zdo_t.LogicalType.Router)
    security = util.zha_security(
        network_info=network_info, node_info=router_node_info, use_hashed_tclk=False
    )

    assert security.preconfiguredTrustCenterEui64 == bellows_t.EmberEUI64([0x00] * 8)
    assert (
        security.bitmask & bellows_t.EmberInitialSecurityBitmask.HAVE_TRUST_CENTER_EUI64
        != bellows_t.EmberInitialSecurityBitmask.HAVE_TRUST_CENTER_EUI64
    )

    assert security.preconfiguredKey == network_info.tc_link_key.key
    assert (
        security.bitmask
        & bellows_t.EmberInitialSecurityBitmask.TRUST_CENTER_USES_HASHED_LINK_KEY
        != bellows_t.EmberInitialSecurityBitmask.TRUST_CENTER_USES_HASHED_LINK_KEY
    )


def test_ezsp_key_to_zigpy_key(zigpy_key, ezsp_key, ezsp_mock):
    return util.ezsp_key_to_zigpy_key(ezsp_key, ezsp_mock) == zigpy_key


def test_zigpy_key_to_ezsp_key(zigpy_key, ezsp_key, ezsp_mock):
    return util.zigpy_key_to_ezsp_key(zigpy_key, ezsp_mock) == ezsp_key
