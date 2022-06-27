"""Protocol version 7 specific structs."""

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


class EmberBeaconData(EzspStruct):
    """Beacon data structure."""

    # The channel of the received beacon.
    channel: basic.uint8_t
    # The LQI of the received beacon.
    lqi: basic.uint8_t
    # The RSSI of the received beacon.
    rssi: basic.int8s
    # The depth of the received beacon.
    depth: basic.uint8_t
    # The network update ID of the received beacon.
    nwkUpdateId: basic.uint8_t
    # The power level of the received beacon. This field is valid only if the beacon is
    # an enhanced beacon
    power: basic.int8s
    # The TC connectivity and long uptime from capacity field.
    parentPriority: basic.int8s
    # The PAN ID of the received beacon.
    panId: named.EmberPanId
    # The extended PAN ID of the received beacon.
    extendedPanId: named.ExtendedPanId
    # The sender of the received beacon.
    sender: named.EmberNodeId
    # Whether or not the beacon is enhanced.
    enhanced: named.Bool
    # Whether the beacon is advertising permit join.
    permitJoin: named.Bool
    # Whether the beacon is advertising capacity.
    hasCapacity: named.Bool


class EmberBeaconIterator(EzspStruct):
    """Defines an iterator that is used to loop over cached beacons. Do not write to
    fields denoted as Private.
    """

    # The retrieved beacon.
    beacon: EmberBeaconData
    # (Private) The index of the retrieved beacon.
    index: basic.uint8_t


class EmberBeaconClassificationParams(EzspStruct):
    """The parameters related to beacon prioritization."""

    # The minimum RSSI value for receiving packets that is used in some beacon
    # prioritization algorithms.
    minRssiForReceivingPkts: basic.int8s
    # The beacon classification mask that identifies which beacon prioritization
    # algorithm to pick and defines the relevant parameters.
    beaconClassificationMask: basic.uint16_t


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


class EmberGpProxyTableEntry(EzspStruct):
    """The internal representation of a proxy table entry."""

    # The link key to be used to secure this pairing link.
    securityLinkKey: named.EmberKeyData
    # Internal status of the proxy table entry.
    status: named.EmberGpProxyTableEntryStatus
    # The tunneling options
    # (this contains both options and extendedOptions from the spec).
    options: basic.uint32_t
    # The addressing info of the GPD.
    gpd: EmberGpAddress
    # The assigned alias for the GPD.
    assignedAlias: named.EmberNodeId
    # The security options field.
    securityOptions: basic.uint8_t
    # The security frame counter of the GPD.
    gpdSecurityFrameCounter: named.EmberGpSecurityFrameCounter
    # The key to use for GPD.
    gpdKey: named.EmberKeyData
    # The list of sinks (hardcoded to 2 which is the spec minimum).
    sinkList: basic.fixed_list(2, EmberGpSinkListEntry)
    # The groupcast radius.
    groupcastRadius: basic.uint8_t
    # The search counter
    searchCounter: basic.uint8_t


class EmberGpSinkTableEntry(EzspStruct):
    """The internal representation of a sink table entry."""

    # Internal status of the sink table entry
    status: named.EmberGpSinkTableEntryStatus
    # The tunneling options
    # (this contains both options and extendedOptions from the spec).
    options: basic.uint32_t
    # The addressing info of the GPD.
    gpd: EmberGpAddress
    # The device id for the GPD.
    deviceId: basic.uint8_t
    # The list of sinks (hardcoded to 2 which is the spec minimum).
    sinkList: basic.fixed_list(2, EmberGpSinkListEntry)
    # The assigned alias for the GPD.
    assignedAlias: named.EmberNodeId
    # The groupcast radius.
    groupcastRadius: basic.uint8_t
    # The security options field.
    securityOptions: basic.uint8_t
    # The security frame counter of the GPD.
    gpdSecurityFrameCounter: named.EmberGpSecurityFrameCounter
    # The key to use for GPD.
    gpdKey: named.EmberKeyData


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


class EmberChildData(EzspStruct):
    """A structure containing a child node's data."""

    # The EUI64 of the child
    eui64: named.EmberEUI64
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

    # The GPD's EUI64.
    # gpdIeeeAddress: named.EmberEUI64
    # The GPD's source ID.
    # sourceId: basic.uint32_t
