"""Protocol version 4 named types."""

import bellows.types.basic as basic
from bellows.types.named import (  # noqa: F401, F403
    EUI64,
    Bool,
    Channels,
    EmberApsOption,
    EmberBindingType,
    EmberCertificate283k1Data,
    EmberCertificateData,
    EmberConcentratorType,
    EmberConfigTxPowerMode,
    EmberCounterType,
    EmberCurrentSecurityBitmask,
    EmberDeviceUpdate,
    EmberEventUnits,
    EmberGpKeyType,
    EmberGpSecurityLevel,
    EmberIncomingMessageType,
    EmberInitialSecurityBitmask,
    EmberJoinDecision,
    EmberJoinMethod,
    EmberKeyStatus,
    EmberKeyStructBitmask,
    EmberKeyType,
    EmberLibraryStatus,
    EmberMacPassthroughType,
    EmberMessageDigest,
    EmberMulticastId,
    EmberNetworkStatus,
    EmberNodeId,
    EmberNodeType,
    EmberOutgoingMessageType,
    EmberPanId,
    EmberPrivateKey283k1Data,
    EmberPrivateKeyData,
    EmberPublicKey283k1Data,
    EmberPublicKeyData,
    EmberRf4ceApplicationCapabilities,
    EmberRf4ceNodeCapabilities,
    EmberRf4ceTxOption,
    EmberSignature283k1Data,
    EmberSignatureData,
    EmberSmacData,
    EmberStatus,
    EmberZdoConfigurationFlags,
    EmberZllKeyIndex,
    EmberZllState,
    ExtendedPanId,
    EzspConfigId,
    EzspDecisionId,
    EzspEndpointFlags,
    EzspExtendedValueId,
    EzspMfgTokenId,
    EzspNetworkScanType,
    EzspPolicyId,
    EzspSourceRouteOverheadInformation,
    EzspStatus,
    EzspValueId,
    EzspZllNetworkOperation,
    KeyData,
)


class EmberNetworkInitBitmask(basic.bitmap16):
    # Bitmask options for emberNetworkInit().

    # No options for Network Init
    NETWORK_INIT_NO_OPTIONS = 0x0000
    # Save parent info (node ID and EUI64) in a token during joining/rejoin,
    # and restore on reboot.
    NETWORK_INIT_PARENT_INFO_IN_TOKEN = 0x0001


EmberNetworkInitStruct = EmberNetworkInitBitmask
