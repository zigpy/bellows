"""Protocol version 6 named types."""

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
