"""Protocol version 5 named types."""

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


class EmberCounterType(basic.enum8):
    # Defines the events reported to the application by the
    # readAndClearCounters command.

    # The MAC received a broadcast.
    COUNTER_MAC_RX_BROADCAST = 0
    # The MAC transmitted a broadcast.
    COUNTER_MAC_TX_BROADCAST = 1
    # The MAC received a unicast.
    COUNTER_MAC_RX_UNICAST = 2
    # The MAC successfully transmitted a unicast.
    COUNTER_MAC_TX_UNICAST_SUCCESS = 3
    # The MAC retried a unicast.
    COUNTER_MAC_TX_UNICAST_RETRY = 4
    # The MAC unsuccessfully transmitted a unicast.
    COUNTER_MAC_TX_UNICAST_FAILED = 5
    # The APS layer received a data broadcast.
    COUNTER_APS_DATA_RX_BROADCAST = 6
    # The APS layer transmitted a data broadcast.
    COUNTER_APS_DATA_TX_BROADCAST = 7
    # The APS layer received a data unicast.
    COUNTER_APS_DATA_RX_UNICAST = 8
    # The APS layer successfully transmitted a data unicast.
    COUNTER_APS_DATA_TX_UNICAST_SUCCESS = 9
    # The APS layer retried a data unicast.
    COUNTER_APS_DATA_TX_UNICAST_RETRY = 10
    # The APS layer unsuccessfully transmitted a data unicast.
    COUNTER_APS_DATA_TX_UNICAST_FAILED = 11
    # The network layer successfully submitted a new route discovery to the MAC.
    COUNTER_ROUTE_DISCOVERY_INITIATED = 12
    # An entry was added to the neighbor table.
    COUNTER_NEIGHBOR_ADDED = 13
    # An entry was removed from the neighbor table.
    COUNTER_NEIGHBOR_REMOVED = 14
    # A neighbor table entry became stale because it had not been heard from.
    COUNTER_NEIGHBOR_STALE = 15
    # A node joined or rejoined to the network via this node.
    COUNTER_JOIN_INDICATION = 16
    # An entry was removed from the child table.
    COUNTER_CHILD_REMOVED = 17
    # EZSP-UART only. An overflow error occurred in the UART.
    COUNTER_ASH_OVERFLOW_ERROR = 18
    # EZSP-UART only. A framing error occurred in the UART.
    COUNTER_ASH_FRAMING_ERROR = 19
    # EZSP-UART only. An overrun error occurred in the UART.
    COUNTER_ASH_OVERRUN_ERROR = 20
    # A message was dropped at the network layer because the NWK frame counter
    # was not higher than the last message seen from that source.
    COUNTER_NWK_FRAME_COUNTER_FAILURE = 21
    # A message was dropped at the APS layer because the APS frame counter was
    # not higher than the last message seen from that source.
    COUNTER_APS_FRAME_COUNTER_FAILURE = 22
    # Utility counter for general debugging use.
    COUNTER_UTILITY = 23
    # A message was dropped at the APS layer because it had APS encryption but
    # the key associated with the sender has not been authenticated, and thus
    # the key is not authorized for use in APS data messages.
    COUNTER_APS_LINK_KEY_NOT_AUTHORIZED = 24
    # A NWK encrypted message was received but dropped because decryption
    # failed.
    COUNTER_NWK_DECRYPTION_FAILURE = 25
    # An APS encrypted message was received but dropped because decryption
    # failed.
    COUNTER_APS_DECRYPTION_FAILURE = 26
    # The number of times we failed to allocate a set of linked packet buffers.
    # This doesn't necessarily mean that the packet buffer count was 0 at the
    # time, but that the number requested was greater than the number free.
    COUNTER_ALLOCATE_PACKET_BUFFER_FAILURE = 27
    # The number of relayed unicast packets.
    COUNTER_RELAYED_UNICAST = 28
    # The number of times we dropped a packet due to reaching
    # the preset PHY to MAC queue limit (emMaxPhyToMacQueueLength).
    COUNTER_PHY_TO_MAC_QUEUE_LIMIT_REACHED = 29
    # The number of times we dropped a packet due to the
    # packet-validate library checking a packet and rejecting it
    # due to length or other formatting problems.
    COUNTER_PACKET_VALIDATE_LIBRARY_DROPPED_COUNT = 30
    # The number of times the NWK retry queue is full and a
    # new message failed to be added.
    COUNTER_TYPE_NWK_RETRY_OVERFLOW = 31
    # The number of times the PHY layer was unable to transmit
    # due to a failed CCA.
    COUNTER_PHY_CCA_FAIL_COUNT = 32
    # The number of times a NWK broadcast was dropped because
    # the broadcast table was full.
    COUNTER_BROADCAST_TABLE_FULL = 33
    # The number of low priority packet traffic arbitration requests.
    COUNTER_PTA_LO_PRI_REQUESTED = 34
    # The number of high priority packet traffic arbitration requests.
    COUNTER_PTA_HI_PRI_REQUESTED = 35
    # The number of low priority packet traffic arbitration requests denied.
    COUNTER_PTA_LO_PRI_DENIED = 36
    # The number of high priority packet traffic arbitration requests denied.
    COUNTER_PTA_HI_PRI_DENIED = 37
    # The number of aborted low priority packet traffic arbitration transmissions.
    COUNTER_PTA_LO_PRI_TX_ABORTED = 38
    # The number of aborted high priority packet traffic arbitration transmissions.
    COUNTER_PTA_HI_PRI_TX_ABORTED = 39


class EmberNetworkInitBitmask(basic.bitmap16):
    # Bitmask options for emberNetworkInit().

    # No options for Network Init
    NETWORK_INIT_NO_OPTIONS = 0x0000
    # Save parent info (node ID and EUI64) in a token during joining/rejoin,
    # and restore on reboot.
    NETWORK_INIT_PARENT_INFO_IN_TOKEN = 0x0001


EmberNetworkInitStruct = EmberNetworkInitBitmask


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
