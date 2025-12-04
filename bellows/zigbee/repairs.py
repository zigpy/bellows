"""Coordinator state repairs."""

import logging

import zigpy.types

from bellows.exception import InvalidCommandError
from bellows.ezsp import EZSP
import bellows.types as t

LOGGER = logging.getLogger(__name__)


async def fix_invalid_tclk_partner_ieee(ezsp: EZSP) -> bool:
    """Fix invalid TCLK partner IEEE address."""
    (ieee,) = await ezsp.getEui64()
    ieee = zigpy.types.EUI64(ieee)

    (status, state) = await ezsp.getCurrentSecurityState()
    assert t.sl_Status.from_ember_status(status) == t.sl_Status.OK

    if state.trustCenterLongAddress == ieee:
        return False

    LOGGER.warning(
        "Fixing invalid TCLK partner IEEE (%s => %s)",
        state.trustCenterLongAddress,
        ieee,
    )

    try:
        rsp = await ezsp.getTokenData(
            token=t.NV3KeyId.NVM3KEY_STACK_TRUST_CENTER, index=0
        )
        assert t.sl_Status.from_ember_status(rsp.status) == t.sl_Status.OK
    except (InvalidCommandError, AttributeError, AssertionError):
        LOGGER.warning("NV3 interface not available in this firmware, please upgrade!")
        return False

    token, remaining = t.NV3StackTrustCenterToken.deserialize(rsp.value)
    assert not remaining
    assert token.eui64 == state.trustCenterLongAddress

    (status,) = await ezsp.setTokenData(
        token=t.NV3KeyId.NVM3KEY_STACK_TRUST_CENTER,
        index=0,
        token_data=token.replace(eui64=ieee).serialize(),
    )
    assert t.sl_Status.from_ember_status(status) == t.sl_Status.OK

    return True


async def update_tx_power(ezsp: EZSP, tx_power: int) -> bool:
    """Persist transmit power in NVRAM."""

    try:
        rsp = await ezsp.getTokenData(token=t.NV3KeyId.NVM3KEY_STACK_NODE_DATA, index=0)
        assert t.sl_Status.from_ember_status(rsp.status) == t.sl_Status.OK
    except (InvalidCommandError, AttributeError, AssertionError):
        LOGGER.debug("NV3 interface not available in this firmware, please upgrade!")
        return False

    token, remaining = t.NV3StackNodeData.deserialize(rsp.value)
    assert not remaining

    # No point in writing to NVRAM if the TX power is correct
    if token.radioTxPower == tx_power:
        return False

    status, node_type, nwk_params = await ezsp.getNetworkParameters()
    assert t.sl_Status.from_ember_status(status) == t.sl_Status.OK

    # Sanity check
    assert token.panId == nwk_params.panId
    assert token.radioFreqChannel == nwk_params.radioChannel
    assert token.stackProfile == 0x02
    assert token.nodeType == node_type
    assert token.extendedPanId == nwk_params.extendedPanId

    (status,) = await ezsp.setTokenData(
        token=t.NV3KeyId.NVM3KEY_STACK_NODE_DATA,
        index=0,
        token_data=token.replace(radioTxPower=tx_power).serialize(),
    )
    assert t.sl_Status.from_ember_status(status) == t.sl_Status.OK

    LOGGER.debug("Persisted TX power %d to NVRAM", tx_power)

    return True
