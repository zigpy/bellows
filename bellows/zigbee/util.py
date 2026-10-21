import logging
import math

import zigpy.state
import zigpy.types as zigpy_t

import bellows.types as t

LOGGER = logging.getLogger(__name__)

# Test tone at 8dBm power level produced a max RSSI of -3dB
# -21dB corresponds to 100% LQI on the ZZH!
RSSI_MAX = -5

# Grounded antenna and then shielded produced a min RSSI of -92
# -89dB corresponds to 0% LQI on the ZZH!
RSSI_MIN = -92


def zha_security(
    *,
    network_info: zigpy.state.NetworkInfo,
    use_hashed_tclk: bool,
) -> t.EmberInitialSecurityState:
    """Construct an `EmberInitialSecurityState` out of zigpy network state."""
    isc = t.EmberInitialSecurityState()
    isc.bitmask = (
        t.EmberInitialSecurityBitmask.HAVE_PRECONFIGURED_KEY
        | t.EmberInitialSecurityBitmask.REQUIRE_ENCRYPTED_KEY
        | t.EmberInitialSecurityBitmask.TRUST_CENTER_GLOBAL_LINK_KEY
        | t.EmberInitialSecurityBitmask.HAVE_NETWORK_KEY
        | t.EmberInitialSecurityBitmask.NO_FRAME_COUNTER_RESET
    )
    isc.networkKey = t.KeyData(network_info.network_key.key)
    isc.networkKeySequenceNumber = t.uint8_t(network_info.network_key.seq)

    if network_info.tc_link_key.partner_ieee != zigpy_t.EUI64.UNKNOWN:
        isc.bitmask |= t.EmberInitialSecurityBitmask.HAVE_TRUST_CENTER_EUI64
        isc.preconfiguredTrustCenterEui64 = t.EUI64(
            network_info.tc_link_key.partner_ieee
        )
    else:
        isc.preconfiguredTrustCenterEui64 = t.EUI64.convert("00:00:00:00:00:00:00:00")

    if use_hashed_tclk:
        if network_info.tc_link_key.key != zigpy_t.KeyData(b"ZigBeeAlliance09"):
            LOGGER.warning("Only the well-known TC Link Key is supported")

        isc.bitmask |= t.EmberInitialSecurityBitmask.TRUST_CENTER_USES_HASHED_LINK_KEY
        isc.preconfiguredKey, _ = t.KeyData.deserialize(
            bytes.fromhex(network_info.stack_specific["ezsp"]["hashed_tclk"])
        )
    else:
        isc.preconfiguredKey = t.KeyData(network_info.tc_link_key.key)

    return isc


def ezsp_key_to_zigpy_key(key) -> zigpy.state.Key:
    """Convert an `EmberKeyStruct` into a zigpy `Key`."""
    zigpy_key = zigpy.state.Key()
    zigpy_key.key = zigpy_t.KeyData(key.key)

    if t.EmberKeyStructBitmask.KEY_HAS_SEQUENCE_NUMBER in key.bitmask:
        zigpy_key.seq = key.sequenceNumber

    if t.EmberKeyStructBitmask.KEY_HAS_OUTGOING_FRAME_COUNTER in key.bitmask:
        zigpy_key.tx_counter = key.outgoingFrameCounter

    if t.EmberKeyStructBitmask.KEY_HAS_INCOMING_FRAME_COUNTER in key.bitmask:
        zigpy_key.rx_counter = key.incomingFrameCounter

    if t.EmberKeyStructBitmask.KEY_HAS_PARTNER_EUI64 in key.bitmask:
        zigpy_key.partner_ieee = key.partnerEUI64

    return zigpy_key


def zigpy_key_to_ezsp_key(zigpy_key: zigpy.state.Key):
    """Convert a zigpy `Key` into a `EmberKeyStruct`."""
    key = t.EmberKeyStruct()
    key.key = t.KeyData(zigpy_key.key)
    key.bitmask = t.EmberKeyStructBitmask(0)

    if zigpy_key.seq is not None:
        key.sequenceNumber = t.uint8_t(zigpy_key.seq)
        key.bitmask |= t.EmberKeyStructBitmask.KEY_HAS_SEQUENCE_NUMBER

    if zigpy_key.tx_counter is not None:
        key.outgoingFrameCounter = t.uint32_t(zigpy_key.tx_counter)
        key.bitmask |= t.EmberKeyStructBitmask.KEY_HAS_OUTGOING_FRAME_COUNTER

    if zigpy_key.rx_counter is not None:
        key.incomingFrameCounter = t.uint32_t(zigpy_key.rx_counter)
        key.bitmask |= t.EmberKeyStructBitmask.KEY_HAS_INCOMING_FRAME_COUNTER

    if zigpy_key.partner_ieee is not None:
        key.partnerEUI64 = t.EUI64(zigpy_key.partner_ieee)
        key.bitmask |= t.EmberKeyStructBitmask.KEY_HAS_PARTNER_EUI64

    return key


def logistic(x: float, *, L: float = 1, x_0: float = 0, k: float = 1) -> float:
    """Logistic function."""
    return L / (1 + math.exp(-k * (x - x_0)))


def map_rssi_to_energy(rssi: int) -> float:
    """Remaps RSSI (in dBm) to Energy (0-255)."""
    return logistic(
        x=rssi,
        L=255,
        x_0=RSSI_MIN + 0.45 * (RSSI_MAX - RSSI_MIN),
        k=0.13,
    )


def logit(y: float, *, L: float = 1, x_0: float = 0, k: float = 1) -> float:
    """Logit function (inverse of logistic)."""
    return x_0 - math.log(L / y - 1) / k


def map_energy_to_rssi(lqi: float) -> float:
    """Remaps Energy (0-255) back to RSSI (in dBm)."""
    return logit(
        y=lqi,
        L=255,
        x_0=RSSI_MIN + 0.45 * (RSSI_MAX - RSSI_MIN),
        k=0.13,
    )
