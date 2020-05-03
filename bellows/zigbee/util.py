import os
from typing import Any, Dict

import bellows.types as t
import zigpy.config


def zha_security(config: Dict[str, Any], controller: bool = False) -> None:

    isc = t.EmberInitialSecurityState()
    isc.bitmask = t.uint16_t(
        t.EmberInitialSecurityBitmask.HAVE_PRECONFIGURED_KEY
        | t.EmberInitialSecurityBitmask.REQUIRE_ENCRYPTED_KEY
    )
    isc.preconfiguredKey = t.EmberKeyData(config[zigpy.config.CONF_NWK_TC_LINK_KEY])
    nwk_key = config[zigpy.config.CONF_NWK_KEY]
    if nwk_key is None:
        nwk_key = os.urandom(16)
    isc.networkKey = t.EmberKeyData(nwk_key)
    isc.networkKeySequenceNumber = t.uint8_t(config[zigpy.config.CONF_NWK_KEY_SEQ])
    tc_addr = config[zigpy.config.CONF_NWK_TC_ADDRESS]
    if tc_addr is None:
        tc_addr = [0x00] * 8
    isc.preconfiguredTrustCenterEui64 = t.EmberEUI64(tc_addr)

    if controller:
        isc.bitmask |= (
            t.EmberInitialSecurityBitmask.TRUST_CENTER_GLOBAL_LINK_KEY
            | t.EmberInitialSecurityBitmask.HAVE_NETWORK_KEY
        )
        isc.bitmask = t.uint16_t(isc.bitmask)
    return isc
