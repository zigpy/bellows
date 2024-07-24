import importlib
import logging

import pytest
import zigpy.state
from zigpy.types import PanId
import zigpy.zdo.types as zdo_t

import bellows.types as t
import bellows.zigbee.util as util

from tests.test_application import ieee


@pytest.fixture
def node_info():
    return zigpy.state.NodeInfo(
        nwk=t.NWK(0x0000),
        ieee=t.EUI64.convert("00:12:4b:00:1c:a1:b8:46"),
        logical_type=zdo_t.LogicalType.Coordinator,
        model="Mock board",
        manufacturer="Mock Manufacturer",
        version="Mock version",
    )


@pytest.fixture
def network_info(node_info):
    return zigpy.state.NetworkInfo(
        extended_pan_id=t.ExtendedPanId.convert("bd:27:0b:38:37:95:dc:87"),
        pan_id=PanId(0x9BB0),
        nwk_update_id=18,
        nwk_manager_id=t.NWK(0x0000),
        channel=t.uint8_t(15),
        channel_mask=t.Channels.ALL_CHANNELS,
        security_level=t.uint8_t(5),
        network_key=zigpy.state.Key(
            key=t.KeyData.convert("2ccade06b3090c310315b3d574d3c85a"),
            seq=108,
            tx_counter=118785,
        ),
        tc_link_key=zigpy.state.Key(
            key=t.KeyData(b"ZigBeeAlliance09"),
            partner_ieee=node_info.ieee,
            tx_counter=8712428,
        ),
        key_table=[
            zigpy.state.Key(
                key=t.KeyData.convert(
                    "85:7C:05:00:3E:76:1A:F9:68:9A:49:41:6A:60:5C:76"
                ),
                tx_counter=3792973670,
                rx_counter=1083290572,
                seq=147,
                partner_ieee=t.EUI64.convert("CC:CC:CC:FF:FE:E6:8E:CA"),
            ),
            zigpy.state.Key(
                key=t.KeyData.convert(
                    "CA:02:E8:BB:75:7C:94:F8:93:39:D3:9C:B3:CD:A7:BE"
                ),
                tx_counter=2597245184,
                rx_counter=824424412,
                seq=19,
                partner_ieee=t.EUI64.convert("EC:1B:BD:FF:FE:2F:41:A4"),
            ),
        ],
        children=[
            t.EUI64.convert("00:0B:57:FF:FE:2B:D4:57"),
        ],
        # If exposed by the stack, NWK addresses of other connected devices on the network
        nwk_addresses={
            # Two routers
            t.EUI64.convert("CC:CC:CC:FF:FE:E6:8E:CA"): t.NWK(0x44CB),
            t.EUI64.convert("EC:1B:BD:FF:FE:2F:41:A4"): t.NWK(0x0702),
            # Child device
            t.EUI64.convert("00:0b:57:ff:fe:2b:d4:57"): t.NWK(0xC06B),
        },
        stack_specific={"ezsp": {"hashed_tclk": "abcdabcdabcdabcdabcdabcdabcdabcd"}},
        source=f"bellows@{importlib.metadata.version('bellows')}",
    )


@pytest.fixture
def zigpy_key(network_info, node_info):
    return network_info.network_key.replace(
        rx_counter=1234567,
        partner_ieee=node_info.ieee,
    )


@pytest.fixture
def ezsp_key(network_info, node_info, zigpy_key):
    return t.EmberKeyStruct(
        bitmask=(
            t.EmberKeyStructBitmask.KEY_HAS_SEQUENCE_NUMBER
            | t.EmberKeyStructBitmask.KEY_HAS_OUTGOING_FRAME_COUNTER
            | t.EmberKeyStructBitmask.KEY_HAS_INCOMING_FRAME_COUNTER
            | t.EmberKeyStructBitmask.KEY_HAS_PARTNER_EUI64
        ),
        key=t.KeyData(network_info.network_key.key),
        sequenceNumber=zigpy_key.seq,
        outgoingFrameCounter=zigpy_key.tx_counter,
        incomingFrameCounter=zigpy_key.rx_counter,
        partnerEUI64=t.EUI64(node_info.ieee),
    )


def test_zha_security_normal(network_info, node_info):
    security = util.zha_security(network_info=network_info, use_hashed_tclk=True)

    assert security.preconfiguredTrustCenterEui64 == node_info.ieee
    assert t.EmberInitialSecurityBitmask.HAVE_TRUST_CENTER_EUI64 in security.bitmask

    assert (
        security.preconfiguredKey.serialize().hex()
        == network_info.stack_specific["ezsp"]["hashed_tclk"]
    )
    assert (
        t.EmberInitialSecurityBitmask.TRUST_CENTER_USES_HASHED_LINK_KEY
        in security.bitmask
    )


def test_zha_security_router_unknown_tclk_partner_ieee(network_info):
    security = util.zha_security(
        network_info=network_info.replace(
            tc_link_key=network_info.tc_link_key.replace(partner_ieee=t.EUI64.UNKNOWN)
        ),
        use_hashed_tclk=False,
    )

    # Not set, since we don't know it
    assert security.preconfiguredTrustCenterEui64 == t.EUI64([0x00] * 8)
    assert t.EmberInitialSecurityBitmask.HAVE_TRUST_CENTER_EUI64 not in security.bitmask


def test_zha_security_hashed_nonstandard_tclk_warning(network_info, caplog):
    # Nothing should be logged normally
    with caplog.at_level(logging.WARNING):
        util.zha_security(
            network_info=network_info,
            use_hashed_tclk=True,
        )

    assert "Only the well-known TC Link Key is supported" not in caplog.text

    # But it will be when a non-standard TCLK is used along with TCLK hashing
    with caplog.at_level(logging.WARNING):
        util.zha_security(
            network_info=network_info.replace(
                tc_link_key=network_info.tc_link_key.replace(
                    key=t.KeyData(b"ANonstandardTCLK")
                )
            ),
            use_hashed_tclk=True,
        )

    assert "Only the well-known TC Link Key is supported" in caplog.text


def test_ezsp_key_to_zigpy_key(zigpy_key, ezsp_key):
    assert util.ezsp_key_to_zigpy_key(ezsp_key) == zigpy_key


def test_zigpy_key_to_ezsp_key(zigpy_key, ezsp_key):
    assert util.zigpy_key_to_ezsp_key(zigpy_key) == ezsp_key


def test_map_rssi_to_energy():
    assert 0 <= util.map_rssi_to_energy(-200) <= 0.01
    assert 254 <= util.map_rssi_to_energy(100) <= 255

    # Make sure the two functions are inverses
    for rssi in range(-100, 100):
        energy = util.map_rssi_to_energy(rssi)
        assert abs(util.map_energy_to_rssi(energy) - rssi) < 0.1
