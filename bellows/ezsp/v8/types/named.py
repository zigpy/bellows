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
    EmberIncomingMessageType,
    EmberInitialSecurityBitmask,
    EmberJoinDecision,
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


class EmberJoinMethod(basic.enum8):
    # The type of method used for joining.

    # Normally devices use MAC Association to join a network, which respects
    # the "permit joining" flag in the MAC Beacon. For mobile nodes this value
    # causes the device to use an Ember Mobile Node Join, which is functionally
    # equivalent to a MAC association. This value should be used by default.
    USE_MAC_ASSOCIATION = 0x0
    # For those networks where the "permit joining" flag is never turned on,
    # they will need to use a ZigBee NWK Rejoin. This value causes the rejoin
    # to be sent without NWK security and the Trust Center will be asked to
    # send the NWK key to the device. The NWK key sent to the device can be
    # encrypted with the device's corresponding Trust Center link key. That is
    # determined by the ::EmberJoinDecision on the Trust Center returned by the
    # ::emberTrustCenterJoinHandler(). For a mobile node this value will cause
    # it to use an Ember Mobile node rejoin, which is functionally equivalent.
    USE_NWK_REJOIN = 0x1
    # For those networks where the "permit joining" flag is never turned on,
    # they will need to use a NWK Rejoin. If those devices have been
    # preconfigured with the NWK key (including sequence number) they can use a
    # secured rejoin. This is only necessary for end devices since they need a
    # parent. Routers can simply use the ::USE_NWK_COMMISSIONING join method
    # below.
    USE_NWK_REJOIN_HAVE_NWK_KEY = 0x2
    # For those networks where all network and security information is known
    # ahead of time, a router device may be commissioned such that it does not
    # need to send any messages to begin communicating on the network.
    USE_CONFIGURED_NWK_STATE = 0x3


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


class EmberGpSecurityFrameCounter(basic.uint32_t):
    """The security frame counter"""


class EmberGpSinkTableEntryStatus(basic.uint8_t):
    """The sink table entry status."""
