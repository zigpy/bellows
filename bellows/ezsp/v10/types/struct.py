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
from bellows.types.struct import (  # noqa: F401
    EmberAesMmoHashContext,
    EmberApsFrame,
    EmberBindingTableEntry,
    EmberChildDataV10,
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
