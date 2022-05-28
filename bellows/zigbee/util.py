import logging

import zigpy.state
import zigpy.types as zigpy_t
import zigpy.zdo.types as zdo_t

import bellows.types as t

LOGGER = logging.getLogger(__name__)


def zha_security(
    *,
    network_info: zigpy.state.NetworkInfo,
    node_info: zigpy.state.NodeInfo,
    use_hashed_tclk: bool,
) -> t.EmberInitialSecurityState:
    """Construct an `EmberInitialSecurityState` out of zigpy network state."""
    isc = t.EmberInitialSecurityState()
    isc.bitmask = (
        t.EmberInitialSecurityBitmask.HAVE_PRECONFIGURED_KEY
        | t.EmberInitialSecurityBitmask.REQUIRE_ENCRYPTED_KEY
        | t.EmberInitialSecurityBitmask.TRUST_CENTER_GLOBAL_LINK_KEY
        | t.EmberInitialSecurityBitmask.HAVE_NETWORK_KEY
    )
    isc.networkKey = t.EmberKeyData(network_info.network_key.key)
    isc.networkKeySequenceNumber = t.uint8_t(network_info.network_key.seq)

    if (
        node_info.logical_type != zdo_t.LogicalType.Coordinator
        and network_info.tc_link_key.partner_ieee != zigpy_t.EUI64.UNKNOWN
    ):
        isc.bitmask |= t.EmberInitialSecurityBitmask.HAVE_TRUST_CENTER_EUI64
        isc.preconfiguredTrustCenterEui64 = t.EmberEUI64(
            network_info.tc_link_key.partner_ieee
        )
    else:
        isc.preconfiguredTrustCenterEui64 = t.EmberEUI64([0x00] * 8)

    if use_hashed_tclk:
        if network_info.tc_link_key.key != zigpy_t.KeyData(b"ZigBeeAlliance09"):
            LOGGER.warning("Only the well-known TC Link Key is supported")

        isc.bitmask |= t.EmberInitialSecurityBitmask.TRUST_CENTER_USES_HASHED_LINK_KEY
        isc.preconfiguredKey, _ = t.EmberKeyData.deserialize(
            bytes.fromhex(network_info.stack_specific["ezsp"]["hashed_tclk"])
        )
    else:
        isc.preconfiguredKey = t.EmberKeyData(network_info.tc_link_key.key)

    return isc


def ezsp_key_to_zigpy_key(key, ezsp) -> zigpy.state.Key:
    """Convert an `EmberKeyStruct` into a zigpy `Key`."""
    zigpy_key = zigpy.state.Key()
    zigpy_key.key = zigpy_t.KeyData(key.key)

    if ezsp.types.EmberKeyStructBitmask.KEY_HAS_SEQUENCE_NUMBER in key.bitmask:
        zigpy_key.seq = key.sequenceNumber

    if ezsp.types.EmberKeyStructBitmask.KEY_HAS_OUTGOING_FRAME_COUNTER in key.bitmask:
        zigpy_key.tx_counter = key.outgoingFrameCounter

    if ezsp.types.EmberKeyStructBitmask.KEY_HAS_INCOMING_FRAME_COUNTER in key.bitmask:
        zigpy_key.rx_counter = key.incomingFrameCounter

    if ezsp.types.EmberKeyStructBitmask.KEY_HAS_PARTNER_EUI64 in key.bitmask:
        zigpy_key.partner_ieee = key.partnerEUI64

    return zigpy_key


def zigpy_key_to_ezsp_key(zigpy_key: zigpy.state.Key, ezsp):
    """Convert a zigpy `Key` into a `EmberKeyStruct`."""
    key = ezsp.types.EmberKeyStruct()
    key.key = ezsp.types.EmberKeyData(zigpy_key.key)
    key.bitmask = ezsp.types.EmberKeyStructBitmask(0)

    if zigpy_key.seq is not None:
        key.sequenceNumber = t.uint8_t(zigpy_key.seq)
        key.bitmask |= ezsp.types.EmberKeyStructBitmask.KEY_HAS_SEQUENCE_NUMBER

    if zigpy_key.tx_counter is not None:
        key.outgoingFrameCounter = t.uint32_t(zigpy_key.tx_counter)
        key.bitmask |= ezsp.types.EmberKeyStructBitmask.KEY_HAS_OUTGOING_FRAME_COUNTER

    if zigpy_key.rx_counter is not None:
        key.outgoingFrameCounter = t.uint32_t(zigpy_key.rx_counter)
        key.bitmask |= ezsp.types.EmberKeyStructBitmask.KEY_HAS_INCOMING_FRAME_COUNTER

    if zigpy_key.partner_ieee is not None:
        key.partnerEUI64 = t.EmberEUI64(zigpy_key.partner_ieee)
        key.bitmask |= ezsp.types.EmberKeyStructBitmask.KEY_HAS_PARTNER_EUI64

    return key
