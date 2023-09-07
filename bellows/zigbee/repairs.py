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
    assert status == t.EmberStatus.SUCCESS

    if state.trustCenterLongAddress == ieee:
        return False

    LOGGER.warning(
        "Fixing invalid TCLK partner IEEE (%s => %s)",
        state.trustCenterLongAddress,
        ieee,
    )

    try:
        (status, value) = await ezsp.getTokenData(
            t.NV3KeyId.NVM3KEY_STACK_TRUST_CENTER, 0
        )
        assert status == t.EmberStatus.SUCCESS
    except (InvalidCommandError, AttributeError, AssertionError):
        LOGGER.warning("NV3 interface not available in this firmware, please upgrade!")
        return False

    token, remaining = t.NV3StackTrustCenterToken.deserialize(value)
    assert not remaining
    assert token.eui64 == state.trustCenterLongAddress

    (status,) = await ezsp.setTokenData(
        t.NV3KeyId.NVM3KEY_STACK_TRUST_CENTER,
        0,
        token.replace(eui64=ieee).serialize(),
    )
    assert status == t.EmberStatus.SUCCESS

    return True
