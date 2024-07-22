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
