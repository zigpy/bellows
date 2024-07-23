from __future__ import annotations

from zigpy.types import Struct as EzspStruct, StructField

from . import basic, named


class EmberNetworkParameters(EzspStruct):
    # Network parameters.
    # The network's extended PAN identifier.
    extendedPanId: named.ExtendedPanId
    # The network's PAN identifier.
    panId: named.EmberPanId
    # A power setting, in dBm.
    radioTxPower: basic.uint8_t
    # A radio channel.
    radioChannel: basic.uint8_t
    # The method used to initially join the network.
    joinMethod: named.EmberJoinMethod
    # NWK Manager ID. The ID of the network manager in the current network.
    # This may only be set at joining when using USE_NWK_COMMISSIONING as
    # the join method.
    nwkManagerId: named.EmberNodeId
    # NWK Update ID. The value of the ZigBee nwkUpdateId known by the
    # stack. This is used to determine the newest instance of the network
    # after a PAN ID or channel change. This may only be set at joining
    # when using USE_NWK_COMMISSIONING as the join method.
    nwkUpdateId: basic.uint8_t
    # NWK channel mask. The list of preferred channels that the NWK manager
    # has told this device to use when searching for the network. This may
    # only be set at joining when using USE_NWK_COMMISSIONING as the join
    # method.
    channels: named.Channels


class EmberZigbeeNetwork(EzspStruct):
    # The parameters of a ZigBee network.
    # The 802.15.4 channel associated with the network.
    channel: basic.uint8_t
    # The network's PAN identifier.
    panId: named.EmberPanId
    # The network's extended PAN identifier.
    extendedPanId: named.ExtendedPanId
    # Whether the network is allowing MAC associations.
    allowingJoin: named.Bool
    # The Stack Profile associated with the network.
    stackProfile: basic.uint8_t
    # The instance of the Network.
    nwkUpdateId: basic.uint8_t


class EmberApsFrame(EzspStruct):
    # ZigBee APS frame parameters.
    # The application profile ID that describes the format of the message.
    profileId: basic.uint16_t
    # The cluster ID for this message.
    clusterId: basic.uint16_t
    # The source endpoint.
    sourceEndpoint: basic.uint8_t
    # The destination endpoint.
    destinationEndpoint: basic.uint8_t
    # A bitmask of options.
    options: named.EmberApsOption
    # The group ID for this message, if it is multicast mode.
    groupId: basic.uint16_t
    # The sequence number.
    sequence: basic.uint8_t


class EmberBindingTableEntry(EzspStruct):
    # An entry in the binding table.
    # The type of binding.
    type: named.EmberBindingType
    # The endpoint on the local node.
    local: basic.uint8_t
    # A cluster ID that matches one from the local endpoint's simple
    # descriptor. This cluster ID is set by the provisioning application to
    # indicate which part an endpoint's functionality is bound to this
    # particular remote node and is used to distinguish between unicast and
    # multicast bindings. Note that a binding can be used to send messages
    # with any cluster ID, not just that listed in the binding.
    clusterId: basic.uint16_t
    # The endpoint on the remote node (specified by identifier).
    remote: basic.uint8_t
    # A 64-bit identifier. This is either the destination EUI64 (for
    # unicasts) or the 64-bit group address (for multicasts).
    identifier: named.EUI64
    # The index of the network the binding belongs to.
    networkIndex: basic.uint8_t


class EmberMulticastTableEntry(EzspStruct):
    # A multicast table entry indicates that a particular endpoint is a member
    # of a particular multicast group.  Only devices with an endpoint in a
    # multicast group will receive messages sent to that multicast group.
    # The multicast group ID.
    multicastId: named.EmberMulticastId
    # The endpoint that is a member, or 0 if this entry is not in use (the
    # ZDO is not a member of any multicast groups.)
    endpoint: basic.uint8_t
    # The network index of the network the entry is related to.
    networkIndex: basic.uint8_t = StructField(optional=True)


class EmberTransientKeyDataV5(EzspStruct):
    """The transient key data structure, introduced in EZSPv5."""

    # The IEEE address paired with the transient link key.
    eui64: named.EUI64
    # The key data structure matching the transient key.
    keyData: named.KeyData
    # The incoming frame counter associated with this key.
    incomingFrameCounter: basic.uint32_t
    # The number of milliseconds remaining before the key
    # is automatically timed out of the transient key table.
    countdownTimerMs: basic.uint32_t


class EmberTransientKeyDataV8(EzspStruct):
    """The transient key data structure, revised in EZSPv8."""

    # The IEEE address paired with the transient link key.
    eui64: named.EUI64
    # The key data structure matching the transient key.
    keyData: named.KeyData
    # This bitmask indicates whether various fields in the structure contain valid data.
    bitmask: named.EmberKeyStructBitmask
    # The number of seconds remaining before the key is automatically timed out of the
    # transient key table.
    remainingTimeSeconds: basic.uint16_t


class EmberAesMmoHashContext(EzspStruct):
    # The hash context for an ongoing hash operation.
    # The result of ongoing the hash operation.
    result: basic.FixedList[basic.uint8_t, 16]
    # The total length of the data that has been hashed so far.
    length: basic.uint32_t


class EmberNeighborTableEntry(EzspStruct):
    # A neighbor table entry stores information about the reliability of RF
    # links to and from neighboring nodes.
    # The neighbor's two byte network id
    shortId: named.EmberNodeId
    # An exponentially weighted moving average of the link quality values
    # of incoming packets from this neighbor as reported by the PHY.
    averageLqi: basic.uint8_t
    # The incoming cost for this neighbor, computed from the average LQI.
    # Values range from 1 for a good link to 7 for a bad link.
    inCost: basic.uint8_t
    # The outgoing cost for this neighbor, obtained from the most recently
    # received neighbor exchange message from the neighbor. A value of zero
    # means that a neighbor exchange message from the neighbor has not been
    # received recently enough, or that our id was not present in the most
    # recently received one.
    outCost: basic.uint8_t
    # The number of aging periods elapsed since a link status message was
    # last received from this neighbor. The aging period is 16 seconds.
    age: basic.uint8_t
    # The 8 byte EUI64 of the neighbor.
    longId: named.EUI64


class EmberRouteTableEntry(EzspStruct):
    # A route table entry stores information about the next hop along the route
    # to the destination.
    # The short id of the destination. A value of 0xFFFF indicates the
    # entry is unused.
    destination: named.EmberNodeId
    # The short id of the next hop to this destination.
    nextHop: basic.uint16_t
    # Indicates whether this entry is active (0), being discovered (1)),
    # unused (3), or validating (4).
    status: basic.uint8_t
    # The number of seconds since this route entry was last used to send a
    # packet.
    age: basic.uint8_t
    # Indicates whether this destination is a High RAM Concentrator (2), a
    # Low RAM Concentrator (1), or not a concentrator (0).
    concentratorType: basic.uint8_t
    # For a High RAM Concentrator, indicates whether a route record is
    # needed (2), has been sent (1), or is no long needed (0) because a
    # source routed message from the concentrator has been received.
    routeRecordState: basic.uint8_t


class EmberInitialSecurityState(EzspStruct):
    # The security data used to set the configuration for the stack, or the
    # retrieved configuration currently in use.
    # A bitmask indicating the security state used to indicate what the
    # security configuration will be when the device forms or joins the
    # network.
    bitmask: named.EmberInitialSecurityBitmask
    # The pre-configured Key data that should be used when forming or
    # joining the network. The security bitmask must be set with the
    # HAVE_PRECONFIGURED_KEY bit to indicate that the key contains valid
    # data.
    preconfiguredKey: named.KeyData
    # The Network Key that should be used by the Trust Center when it forms
    # the network, or the Network Key currently in use by a joined device.
    # The security bitmask must be set with HAVE_NETWORK_KEY to indicate
    # that the key contains valid data.
    networkKey: named.KeyData
    # The sequence number associated with the network key. This is only
    # valid if the HAVE_NETWORK_KEY has been set in the security bitmask.
    networkKeySequenceNumber: basic.uint8_t
    # This is the long address of the trust center on the network that will
    # be joined. It is usually NOT set prior to joining the network and
    # instead it is learned during the joining message exchange. This field
    # is only examined if HAVE_TRUST_CENTER_EUI64 is set in the
    # EmberInitialSecurityState::bitmask. Most devices should clear that
    # bit and leave this field alone. This field must be set when using
    # commissioning mode.
    preconfiguredTrustCenterEui64: named.EUI64


class EmberCurrentSecurityState(EzspStruct):
    # The security options and information currently used by the stack.
    # A bitmask indicating the security options currently in use by a
    # device joined in the network.
    bitmask: named.EmberCurrentSecurityBitmask
    # The IEEE Address of the Trust Center device.
    trustCenterLongAddress: named.EUI64


class EmberZllSecurityAlgorithmData(EzspStruct):
    # Data associated with the ZLL security algorithm.
    # Transaction identifier.
    transactionId: basic.uint32_t
    # Response identifier.
    responseId: basic.uint32_t
    # Bitmask.
    bitmask: basic.uint16_t


class EmberZllNetwork(EzspStruct):
    # The parameters of a ZLL network.
    # The parameters of a ZigBee network.
    zigbeeNetwork: EmberZigbeeNetwork
    # Data associated with the ZLL security algorithm.
    securityAlgorithm: EmberZllSecurityAlgorithmData
    # Associated EUI64.
    eui64: named.EUI64
    # The node id.
    nodeId: named.EmberNodeId
    # The ZLL state.
    state: named.EmberZllState
    # The node type.
    nodeType: named.EmberNodeType
    # The number of sub devices.
    numberSubDevices: basic.uint8_t
    # The total number of group identifiers.
    totalGroupIdentifiers: basic.uint8_t
    # RSSI correction value.
    rssiCorrection: basic.uint8_t


class EmberZllInitialSecurityState(EzspStruct):
    # Describes the initial security features and requirements that will be
    # used when forming or joining ZLL networks.
    # Unused bitmask; reserved for future use.
    bitmask: basic.uint32_t
    # The key encryption algorithm advertised by the application.
    keyIndex: named.EmberZllKeyIndex
    # The encryption key for use by algorithms that require it.
    encryptionKey: named.KeyData
    # The pre-configured link key used during classical ZigBee
    # commissioning.
    preconfiguredKey: named.KeyData


class EmberZllDeviceInfoRecord(EzspStruct):
    # Information about a specific ZLL Device.
    # EUI64 associated with the device.
    ieeeAddress: named.EUI64
    # Endpoint id.
    endpointId: basic.uint8_t
    # Profile id.
    profileId: basic.uint16_t
    # Device id.
    deviceId: basic.uint16_t
    # Associated version.
    version: basic.uint8_t
    # Number of relevant group ids.
    groupIdCount: basic.uint8_t


class EmberZllAddressAssignment(EzspStruct):
    # ZLL address assignment data.
    # Relevant node id.
    nodeId: named.EmberNodeId
    # Minimum free node id.
    freeNodeIdMin: named.EmberNodeId
    # Maximum free node id.
    freeNodeIdMax: named.EmberNodeId
    # Minimum group id.
    groupIdMin: named.EmberMulticastId
    # Maximum group id.
    groupIdMax: named.EmberMulticastId
    # Minimum free group id.
    freeGroupIdMin: named.EmberMulticastId
    # Maximum free group id.
    freeGroupIdMax: named.EmberMulticastId


class EmberTokenData(EzspStruct):
    # Token Data
    # Token data size in bytes
    size: basic.uint32_t
    # Token data pointer
    data: basic.uint8_t


class EmberTokenInfo(EzspStruct):
    # Information of a token in the token table
    # NVM3 key of the token
    nvm3Key: named.NV3KeyId
    # Token is a counter type
    isCnt: named.Bool
    # Token is an indexed token
    isIdx: named.Bool
    # Size of the token
    size: basic.uint8_t
    # Array size of the token
    arraySize: basic.uint8_t


class EmberTokTypeStackZllData(EzspStruct):
    # Public API for ZLL stack data token.
    # Token bitmask.
    bitmask: basic.uint32_t
    # Minimum free node id.
    freeNodeIdMin: basic.uint16_t
    # Maximum free node id.
    freeNodeIdMax: basic.uint16_t
    # Local minimum group id.
    myGroupIdMin: basic.uint16_t
    # Minimum free group id.
    freeGroupIdMin: basic.uint16_t
    # Maximum free group id.
    freeGroupIdMax: basic.uint16_t
    # RSSI correction value.
    rssiCorrection: basic.uint8_t


class EmberTokTypeStackZllSecurity(EzspStruct):
    # Public API for ZLL stack security token.
    # Token bitmask.
    bitmask: basic.uint32_t
    # Key index.
    keyIndex: basic.uint8_t
    # Encryption key.
    encryptionKey: named.KeyData
    # Preconfigured key.
    preconfiguredKey: named.KeyData


class EmberGpAddress(EzspStruct):
    # A GP address structure.
    # The GPD's EUI64.
    gpdIeeeAddress: named.EUI64
    # The GPD's source ID.
    sourceId: basic.uint32_t
    # The GPD Application ID.
    applicationId: basic.uint8_t
    # The GPD endpoint.
    endpoint: basic.uint8_t


class NV3StackTrustCenterToken(EzspStruct):
    """NV3 stack trust center token value."""

    mode: basic.uint16_t
    eui64: named.EUI64
    key: named.KeyData


class EmberKeyStruct(EzspStruct):
    # A structure containing a key and its associated data.
    # A bitmask indicating the presence of data within the various fields
    # in the structure.
    bitmask: named.EmberKeyStructBitmask
    # The type of the key.
    type: named.EmberKeyType
    # The actual key data.
    key: named.KeyData
    # The outgoing frame counter associated with the key.
    outgoingFrameCounter: basic.uint32_t
    # The frame counter of the partner device associated with the key.
    incomingFrameCounter: basic.uint32_t
    # The sequence number associated with the key.
    sequenceNumber: basic.uint8_t
    # The IEEE address of the partner device also in possession of the key.
    partnerEUI64: named.EUI64

    @classmethod
    def deserialize(cls, data: bytes) -> tuple[EmberKeyStruct, bytes]:
        if len(data) == 24:
            # XXX: `key` can seemingly be replaced with the uint32_t `psa_id` field in
            # an invalid response. Pad it with zeroes so it deserializes.
            data = data[:7] + b"\x00" * 12 + data[7:]

        return super().deserialize(data)


class EmberRf4ceVendorInfo(EzspStruct):
    # The RF4CE vendor information block.
    # The vendor identifier field shall contain the vendor identifier of
    # the node.
    vendorId: basic.uint16_t
    # The vendor string field shall contain the vendor string of the node.
    vendorString: basic.FixedList[basic.uint8_t, 7]


class EmberRf4ceApplicationInfo(EzspStruct):
    # The RF4CE application information block.
    # The application capabilities field shall contain information relating
    # to the capabilities of the application of the node.
    capabilities: named.EmberRf4ceApplicationCapabilities
    # The user string field shall contain the user specified identification
    # string.
    userString: basic.FixedList[basic.uint8_t, 15]
    # The device type list field shall contain the list of device types
    # supported by the node.
    deviceTypeList: basic.FixedList[basic.uint8_t, 3]
    # The profile ID list field shall contain the list of profile
    # identifiers disclosed as supported by the node.
    profileIdList: basic.FixedList[basic.uint8_t, 7]


class EmberRf4cePairingTableEntry(EzspStruct):
    # The internal representation of an RF4CE pairing table entry.
    # The link key to be used to secure this pairing link.
    securityLinkKey: named.KeyData
    # The IEEE address of the destination device.
    destLongId: named.EUI64
    # The frame counter last received from the recipient node.
    frameCounter: basic.uint32_t
    # The network address to be assumed by the source device.
    sourceNodeId: named.EmberNodeId
    # The PAN identifier of the destination device.
    destPanId: named.EmberPanId
    # The network address of the destination device.
    destNodeId: named.EmberNodeId
    # The vendor ID of the destination device.
    destVendorId: basic.uint16_t
    # The list of profiles supported by the destination device.
    destProfileIdList: basic.FixedList[basic.uint8_t, 7]
    # The length of the list of supported profiles.
    destProfileIdListLength: basic.uint8_t
    # Info byte.
    info: basic.uint8_t
    # The expected channel of the destination device.
    channel: basic.uint8_t
    # The node capabilities of the recipient node.
    capabilities: basic.uint8_t
    # Last MAC sequence number seen on this pairing link.
    lastSeqn: basic.uint8_t


class EmberGpSinkListEntry(EzspStruct):
    # A sink list entry
    # The sink list type.
    type: basic.uint8_t
    # The EUI64 of the target sink.
    sinkEUI: named.EUI64
    # The short address of the target sink.
    sinkNodeId: named.EmberNodeId


class EmberGpProxyTableEntry(EzspStruct):
    """The internal representation of a proxy table entry."""

    # The link key to be used to secure this pairing link.
    securityLinkKey: named.KeyData
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
    gpdSecurityFrameCounter: basic.uint32_t
    # The key to use for GPD.
    gpdKey: named.KeyData
    # The list of sinks (hardcoded to 2 which is the spec minimum).
    sinkList: basic.FixedList[EmberGpSinkListEntry, 2]
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
    sinkList: basic.FixedList[EmberGpSinkListEntry, 2]
    # The assigned alias for the GPD.
    assignedAlias: named.EmberNodeId
    # The groupcast radius.
    groupcastRadius: basic.uint8_t
    # The security options field.
    securityOptions: basic.uint8_t
    # The security frame counter of the GPD.
    gpdSecurityFrameCounter: basic.uint32_t
    # The key to use for GPD.
    gpdKey: named.KeyData


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
    vendorString: basic.FixedList[basic.uint8_t, 7]


class EmberPerDeviceDutyCycle(EzspStruct):
    """A structure containing per device overall duty cycle consumed

    up to the suspend limit).
    """

    # Node Id of device whose duty cycle is reported.
    nodeId: named.EmberNodeId
    # Amount of overall duty cycle consumed (up to suspend limit).
    dutyCycleConsumed: basic.uint16_t


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


class EmberChildDataV7(EzspStruct):
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


class EmberChildDataV10(EzspStruct):
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


class SecurityManagerContextV12(EzspStruct):
    """Context for Zigbee Security Manager operations."""

    # The type of key being referenced.
    core_key_type: named.SecurityManagerKeyType
    # The index of the referenced key.
    key_index: basic.uint8_t
    # The type of key derivation operation to perform on a key.
    derived_type: named.SecurityManagerDerivedKeyTypeV12
    # The EUI64 associated with this key.
    eui64: named.EUI64
    # Multi-network index.
    multi_network_index: basic.uint8_t
    # Flag bitmask.
    flags: named.SecurityManagerContextFlags
    # Algorithm to use with this key (for PSA APIs)
    psa_key_alg_permission: basic.uint32_t


class SecurityManagerContextV13(EzspStruct):
    """Context for Zigbee Security Manager operations."""

    # The type of key being referenced.
    core_key_type: named.SecurityManagerKeyType
    # The index of the referenced key.
    key_index: basic.uint8_t
    # The type of key derivation operation to perform on a key.
    derived_type: named.SecurityManagerDerivedKeyTypeV13
    # The EUI64 associated with this key.
    eui64: named.EUI64
    # Multi-network index.
    multi_network_index: basic.uint8_t
    # Flag bitmask.
    flags: named.SecurityManagerContextFlags
    # Algorithm to use with this key (for PSA APIs)
    psa_key_alg_permission: basic.uint32_t


class SecurityManagerAPSKeyMetadata(EzspStruct):
    """Metadata for APS link keys."""

    # Bitmask of key properties
    bitmask: named.EmberKeyStructBitmask
    # Outgoing frame counter.
    outgoing_frame_counter: basic.uint32_t
    # Incoming frame counter.
    incoming_frame_counter: basic.uint32_t
    # Remaining lifetime (for transient keys).
    ttl_in_seconds: basic.uint16_t


class SecurityManagerNetworkKeyInfo(EzspStruct):
    """The metadata pertaining to an network key."""

    network_key_set: named.Bool
    alternate_network_key_set: named.Bool
    network_key_sequence_number: basic.uint8_t
    alt_network_key_sequence_number: basic.uint8_t
    network_key_frame_counter: basic.uint32_t


class EmberMultiPhyRadioParameters(EzspStruct):
    """Holds radio parameters."""

    radioTxPower: basic.int8s
    radioPage: basic.uint8_t
    radioChannel: basic.uint8_t
