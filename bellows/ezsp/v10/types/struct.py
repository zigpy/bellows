"""Protocol version 10 specific structs."""

from __future__ import annotations

from bellows.ezsp.v9.types.struct import (  # noqa: F401
    EmberBeaconClassificationParams,
    EmberBeaconData,
    EmberBeaconIterator,
    EmberDutyCycleLimits,
    EmberGpProxyTableEntry,
    EmberGpSinkListEntry,
    EmberGpSinkTableEntry,
    EmberKeyStruct,
    EmberPerDeviceDutyCycle,
    EmberTransientKeyData,
)
import bellows.types.basic as basic
from bellows.types.struct import (  # noqa: F401
    EmberAesMmoHashContext,
    EmberApsFrame,
    EmberBindingTableEntry,
    EmberCurrentSecurityState,
    EmberGpAddress,
    EmberInitialSecurityState,
    EmberMulticastTableEntry,
    EmberNeighborTableEntry,
    EmberNetworkParameters,
    EmberRouteTableEntry,
    EmberTokenData,
    EmberTokenInfo,
    EmberTokTypeStackZllData,
    EmberTokTypeStackZllSecurity,
    EmberZigbeeNetwork,
    EmberZllAddressAssignment,
    EmberZllDeviceInfoRecord,
    EmberZllInitialSecurityState,
    EmberZllNetwork,
    EmberZllSecurityAlgorithmData,
    EzspStruct,
)

from . import named


class EmberChildData(EzspStruct):
    """A structure containing a child node's data."""

    # The EUI64 of the child
    eui64: named.EUI64
    # The node type of the child
    type: named.EmberNodeType
    # The short address of the child
    id: named.EmberNodeId
    # The phy of the child
    phy: basic.uint8_t
    # The power of the child
    power: basic.uint8_t
    # The timeout of the child
    timeout: basic.uint8_t
    timeout_remaining: basic.uint32_t

    # The GPD's EUI64.
    # gpdIeeeAddress: named.EUI64
    # The GPD's source ID.
    # sourceId: basic.uint32_t
