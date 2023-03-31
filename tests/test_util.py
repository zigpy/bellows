import logging

import pytest
import zigpy.state
import zigpy.types as t
import zigpy.zdo.types as zdo_t

import bellows.types as bellows_t
import bellows.zigbee.util as util

from tests.test_application import ezsp_mock
from tests.test_application_network_state import network_info, node_info


@pytest.fixture
def zigpy_key(network_info, node_info):
    return network_info.network_key.replace(
        rx_counter=1234567,
        partner_ieee=node_info.ieee,
    )


@pytest.fixture
def ezsp_key(ezsp_mock, network_info, node_info, zigpy_key):
    ezsp = ezsp_mock
    return ezsp.types.EmberKeyStruct(
        bitmask=(
            ezsp.types.EmberKeyStructBitmask.KEY_HAS_SEQUENCE_NUMBER
            | ezsp.types.EmberKeyStructBitmask.KEY_HAS_OUTGOING_FRAME_COUNTER
            | ezsp.types.EmberKeyStructBitmask.KEY_HAS_INCOMING_FRAME_COUNTER
            | ezsp.types.EmberKeyStructBitmask.KEY_HAS_PARTNER_EUI64
        ),
        key=ezsp.types.EmberKeyData(network_info.network_key.key),
        sequenceNumber=zigpy_key.seq,
        outgoingFrameCounter=zigpy_key.tx_counter,
        incomingFrameCounter=zigpy_key.rx_counter,
        partnerEUI64=bellows_t.EmberEUI64(node_info.ieee),
    )


def test_zha_security_normal(network_info, node_info):
    security = util.zha_security(
        network_info=network_info, node_info=node_info, use_hashed_tclk=True
    )

    assert security.preconfiguredTrustCenterEui64 == bellows_t.EmberEUI64([0x00] * 8)
    assert (
        bellows_t.EmberInitialSecurityBitmask.HAVE_TRUST_CENTER_EUI64
        not in security.bitmask
    )

    assert (
        security.preconfiguredKey.serialize().hex()
        == network_info.stack_specific["ezsp"]["hashed_tclk"]
    )
    assert (
        bellows_t.EmberInitialSecurityBitmask.TRUST_CENTER_USES_HASHED_LINK_KEY
        in security.bitmask
    )


def test_zha_security_router(network_info, node_info):
    security = util.zha_security(
        network_info=network_info,
        node_info=node_info.replace(logical_type=zdo_t.LogicalType.Router),
        use_hashed_tclk=False,
    )

    assert security.preconfiguredTrustCenterEui64 == bellows_t.EmberEUI64(
        network_info.tc_link_key.partner_ieee
    )
    assert (
        bellows_t.EmberInitialSecurityBitmask.HAVE_TRUST_CENTER_EUI64
        in security.bitmask
    )

    assert security.preconfiguredKey == network_info.tc_link_key.key
    assert (
        bellows_t.EmberInitialSecurityBitmask.TRUST_CENTER_USES_HASHED_LINK_KEY
        not in security.bitmask
    )


def test_zha_security_router_unknown_tclk_partner_ieee(network_info, node_info):
    security = util.zha_security(
        network_info=network_info.replace(
            tc_link_key=network_info.tc_link_key.replace(partner_ieee=t.EUI64.UNKNOWN)
        ),
        node_info=node_info.replace(logical_type=zdo_t.LogicalType.Router),
        use_hashed_tclk=False,
    )

    # Not set, since we don't know it
    assert security.preconfiguredTrustCenterEui64 == bellows_t.EmberEUI64([0x00] * 8)
    assert (
        bellows_t.EmberInitialSecurityBitmask.HAVE_TRUST_CENTER_EUI64
        not in security.bitmask
    )


def test_zha_security_replace_missing_tc_partner_addr(network_info, node_info):
    security = util.zha_security(
        network_info=network_info.replace(
            tc_link_key=network_info.tc_link_key.replace(partner_ieee=t.EUI64.UNKNOWN)
        ),
        node_info=node_info,
        use_hashed_tclk=True,
    )

    assert node_info.ieee != t.EUI64.UNKNOWN
    assert security.preconfiguredTrustCenterEui64 == bellows_t.EmberEUI64([0x00] * 8)


def test_zha_security_hashed_nonstandard_tclk_warning(network_info, node_info, caplog):
    # Nothing should be logged normally
    with caplog.at_level(logging.WARNING):
        util.zha_security(
            network_info=network_info,
            node_info=node_info,
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
            node_info=node_info,
            use_hashed_tclk=True,
        )

    assert "Only the well-known TC Link Key is supported" in caplog.text


def test_ezsp_key_to_zigpy_key(zigpy_key, ezsp_key, ezsp_mock):
    assert util.ezsp_key_to_zigpy_key(ezsp_key, ezsp_mock) == zigpy_key


def test_zigpy_key_to_ezsp_key(zigpy_key, ezsp_key, ezsp_mock):
    assert util.zigpy_key_to_ezsp_key(zigpy_key, ezsp_mock) == ezsp_key


def test_map_rssi_to_energy():
    assert 0 <= util.map_rssi_to_energy(-200) <= 0.01
    assert 254 <= util.map_rssi_to_energy(100) <= 255

    # Make sure the two functions are inverses
    for rssi in range(-100, 100):
        energy = util.map_rssi_to_energy(rssi)
        assert abs(util.map_energy_to_rssi(energy) - rssi) < 0.1
