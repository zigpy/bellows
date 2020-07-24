"""Protocol version 6 specific structs."""

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
    EmberTokTypeStackZllData,
    EmberTokTypeStackZllSecurity,
    EmberTransientKeyData,
    EmberZigbeeNetwork,
    EmberZllAddressAssignment,
    EmberZllDeviceInfoRecord,
    EmberZllInitialSecurityState,
    EmberZllNetwork,
    EmberZllSecurityAlgorithmData,
    EzspStruct,
)

from . import named


class EmberKeyStruct(EzspStruct):
    # A structure containing a key and its associated data.
    # A bitmask indicating the presence of data within the various fields
    # in the structure.
    bitmask: named.EmberKeyStructBitmask
    # The type of the key.
    type: named.EmberKeyType
    # The actual key data.
    key: named.EmberKeyData
    # The outgoing frame counter associated with the key.
    outgoingFrameCounter: basic.uint32_t
    # The frame counter of the partner device associated with the key.
    incomingFrameCounter: basic.uint32_t
    # The sequence number associated with the key.
    sequenceNumber: basic.uint8_t
    # The IEEE address of the partner device also in possession of the key.
    partnerEUI64: named.EmberEUI64


class EmberGpSinkListEntry(EzspStruct):
    # A sink list entry
    # The sink list type.
    type: basic.uint8_t
    # The EUI64 of the target sink.
    sinkEUI: named.EmberEUI64
    # The short address of the target sink.
    sinkNodeId: named.EmberNodeId


class EmberDutyCycleLimits(EzspStruct):
    """A structure containing duty cycle limit configurations.

    All limits are absolute, and are required to be as follows:
    suspLimit > critThresh > limitThresh
    For example:
    suspLimit = 250 (2.5%), critThresh = 180 (1.8%), limitThresh 100 (1.00%).
    """

    # The vendor identifier field shall contain the vendor identifier of the node.
    vendorId: basic.uint16_t
    # The vendor string field shall contain the vendor string of the node.
    vendorString: basic.fixed_list(7, basic.uint8_t)


class EmberPerDeviceDutyCycle(EzspStruct):
    """A structure containing per device overall duty cycle consumed

    up to the suspend limit).
    """

    # Node Id of device whose duty cycle is reported.
    nodeId: named.EmberNodeId
    # Amount of overall duty cycle consumed (up to suspend limit).
    dutyCycleConsumed: named.EmberDutyCycleHectoPct
