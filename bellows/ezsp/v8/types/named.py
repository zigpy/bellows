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
    EmberEventUnits,
    EmberGpKeyType,
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
    EmberNetworkStatus,
    EmberNodeId,
    EmberNodeType,
    EmberOutgoingMessageType,
    EmberPanId,
    EmberPrivateKey283k1Data,
    EmberPrivateKeyData,
    EmberPublicKey283k1Data,
    EmberPublicKeyData,
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


class EmberNetworkInitBitmask(basic.bitmap16):
    # Bitmask options for emberNetworkInit().

    # No options for Network Init
    NETWORK_INIT_NO_OPTIONS = 0x0000
    # Save parent info (node ID and EUI64) in a token during joining/rejoin,
    # and restore on reboot.
    NETWORK_INIT_PARENT_INFO_IN_TOKEN = 0x0001
    # Send a rejoin request as an end device on reboot if parent information is
    # persisted. ZB3 end devices must rejoin on reboot.
    NETWORK_INIT_END_DEVICE_REJOIN_ON_REBOOT = 0x0002


EmberNetworkInitStruct = EmberNetworkInitBitmask


class EmberMultiPhyNwkConfig(basic.enum8):
    """Network configuration for the desired radio interface for multi phy network."""

    # Enable broadcast support on Routers
    BROADCAST_SUPPORT = 0x01


class EmberDutyCycleState(basic.enum8):
    """Duty cycle states."""

    # No Duty cycle tracking or metrics are taking place
    DUTY_CYCLE_TRACKING_OFF = 0
    # Duty Cycle is tracked and has not exceeded any thresholds.
    DUTY_CYCLE_LBT_NORMAL = 1
    # We have exceeded the limited threshold of our total duty cycle allotment.
    DUTY_CYCLE_LBT_LIMITED_THRESHOLD_REACHED = 2
    # We have exceeded the critical threshold of our total duty cycle allotment.
    DUTY_CYCLE_LBT_CRITICAL_THRESHOLD_REACHED = 3
    # We have reached the suspend limit and are blocking all outbound transmissions.
    DUTY_CYCLE_LBT_SUSPEND_LIMIT_REACHED = 4


class EmberRadioPowerMode(basic.enum8):
    """Radio power mode."""

    # The radio receiver is switched on.
    RADIO_POWER_MODE_RX_ON = 0
    # The radio receiver is switched off.
    RADIO_POWER_MODE_OFF = 1


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


class EmberDutyCycleHectoPct(basic.uint16_t):
    """The percent of duty cycle for a limit.

    Duty Cycle, Limits, and Thresholds are reported in units of Percent * 100
    (i.e. 10000 = 100.00%, 1 = 0.01%)
    """


class EmberGpProxyTableEntryStatus(basic.uint8_t):
    """The proxy table entry status."""


class EmberGpSecurityFrameCounter(basic.uint32_t):
    """The security frame counter"""


class EmberGpSinkTableEntryStatus(basic.uint8_t):
    """The sink table entry status."""


class SecureEzspSecurityType(basic.uint32_t):
    """Security type of the Secure EZSP Protocol."""


class SecureEzspSecurityLevel(basic.uint8_t):
    """Security level of the Secure EZSP Protocol."""


class SecureEzspRandomNumber(basic.FixedList[basic.uint8_t, 16]):
    """Randomly generated 64-bit number.

    Both NCP and Host contribute this number to create the Session ID,
    which is used in the nonce.
    """


class SecureEzspSessionId(basic.FixedList[basic.uint8_t, 8]):
    """Generated 64-bit Session ID, using random numbers from Host and NCP.

    It is generated at each reboot (during negotiation phase). Having both sides
    contribute to the value prevents one side from choosing a number that might have
    been previously used (either because of a bug or by malicious intent).
    """
