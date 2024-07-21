"""Protocol version 8 named types."""

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
    EmberDutyCycleState,
    EmberEventUnits,
    EmberGpKeyType,
    EmberGpProxyTableEntryStatus,
    EmberGpSecurityLevel,
    EmberGpSinkTableEntryStatus,
    EmberIncomingMessageType,
    EmberInitialSecurityBitmask,
    EmberJoinDecision,
    EmberJoinMethod,
    EmberKeyStatus,
    EmberKeyStructBitmask,
    EmberKeyType,
    EmberLibraryId,
    EmberLibraryStatus,
    EmberMacPassthroughType,
    EmberMessageDigest,
    EmberMulticastId,
    EmberMultiPhyNwkConfig,
    EmberNetworkInitBitmask,
    EmberNetworkStatus,
    EmberNodeId,
    EmberNodeType,
    EmberOutgoingMessageType,
    EmberPanId,
    EmberPrivateKey283k1Data,
    EmberPrivateKeyData,
    EmberPublicKey283k1Data,
    EmberPublicKeyData,
    EmberRadioPowerMode,
    EmberSignature283k1Data,
    EmberSignatureData,
    EmberSmacData,
    EmberStackError,
    EmberStatus,
    EmberZdoConfigurationFlags,
    EmberZllKeyIndex,
    EmberZllState,
    ExtendedPanId,
    EzspConfigId,
    EzspDecisionBitmask,
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
    SecureEzspSecurityLevel,
    SecureEzspSecurityType,
)


class EmberEntropySource(basic.enum8):
    """Entropy sources."""

    # Entropy source error
    ENTROPY_SOURCE_ERROR = 0
    # Entropy source is the radio.
    ENTROPY_SOURCE_RADIO = 1
    # Entropy source is the TRNG powered by mbed TLS.
    ENTROPY_SOURCE_MBEDTLS_TRNG = 2
    # Entropy source is powered by mbed TLS, the source is not TRNG.
    ENTROPY_SOURCE_MBEDTLS = 3
