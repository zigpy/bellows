"""Protocol version 4 specific structs."""

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


class EmberRf4ceVendorInfo(EzspStruct):
    # The RF4CE vendor information block.
    # The vendor identifier field shall contain the vendor identifier of
    # the node.
    vendorId: basic.uint16_t
    # The vendor string field shall contain the vendor string of the node.
    vendorString: basic.fixed_list(7, basic.uint8_t)


class EmberRf4ceApplicationInfo(EzspStruct):
    # The RF4CE application information block.
    # The application capabilities field shall contain information relating
    # to the capabilities of the application of the node.
    capabilities: named.EmberRf4ceApplicationCapabilities
    # The user string field shall contain the user specified identification
    # string.
    userString: basic.fixed_list(15, basic.uint8_t)
    # The device type list field shall contain the list of device types
    # supported by the node.
    deviceTypeList: basic.fixed_list(3, basic.uint8_t)
    # The profile ID list field shall contain the list of profile
    # identifiers disclosed as supported by the node.
    profileIdList: basic.fixed_list(7, basic.uint8_t)


class EmberRf4cePairingTableEntry(EzspStruct):
    # The internal representation of an RF4CE pairing table entry.
    # The link key to be used to secure this pairing link.
    securityLinkKey: named.EmberKeyData
    # The IEEE address of the destination device.
    destLongId: named.EmberEUI64
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
    destProfileIdList: basic.fixed_list(7, basic.uint8_t)
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
    sinkEUI: named.EmberEUI64
    # The short address of the target sink.
    sinkNodeId: named.EmberNodeId
