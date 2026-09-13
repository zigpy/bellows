from zigpy.types import EUI64, NWK, BroadcastAddress, Struct, StructField

import bellows.types as t

from ..v13.commands import COMMANDS as COMMANDS_v13


class GetTokenDataRsp(Struct):
    status: t.sl_Status
    value: t.LVBytes32 = StructField(requires=lambda rsp: rsp.status == t.sl_Status.OK)


# EmberStatus and EzspStatus have been replaced with sl_Status globally.
# The `status` field is also moved to be the first parameter in most responses.
_REPLACEMENTS = {
    t.EmberStatus: t.sl_Status,
    t.EzspStatus: t.sl_Status,
}

COMMANDS = {
    "radioSetSchedulerPriorities": (
        0x012B,
        {
            "priorities": t.SlZigbeeMultiprotocolPriorities,
        },
        {},
    ),
    "setExtendedTimeout": (
        0x007E,
        {
            "remoteEui64": t.EUI64,
            "extendedTimeout": t.Bool,
        },
        {
            "status": t.sl_Status,
        },
    ),
    "getTokenData": (
        0x0102,
        {
            "token": t.uint32_t,
            "index": t.uint32_t,
        },
        GetTokenDataRsp,
    ),
    "exportLinkKeyByIndex": (
        0x010F,
        {
            "index": t.uint8_t,
        },
        {
            "status": t.sl_Status,
            "context": t.SecurityManagerContextV13,
            "plaintext_key": t.KeyData,
            "key_data": t.SecurityManagerAPSKeyMetadata,
        },
    ),
    "exportKey": (
        0x0114,
        {
            "context": t.SecurityManagerContextV13,
        },
        {
            "status": t.sl_Status,
            "key": t.KeyData,
            "context": t.SecurityManagerContextV13,
        },
    ),
    "exportLinkKeyByEui": (
        0x010D,
        {
            "eui64": t.EUI64,
        },
        {
            "status": t.sl_Status,
            "context": t.SecurityManagerContextV13,
            "plaintext_key": t.KeyData,
            "key_data": t.SecurityManagerAPSKeyMetadata,
        },
    ),
    "exportTransientKeyByIndex": (
        0x0112,
        {
            "index": t.uint8_t,
        },
        {
            "status": t.sl_Status,
            "context": t.SecurityManagerContextV13,
            "plaintext_key": t.KeyData,
            "key_data": t.SecurityManagerAPSKeyMetadata,
        },
    ),
    "exportTransientKeyByEui": (
        0x0113,
        {
            "eui64": t.EUI64,
        },
        {
            "status": t.sl_Status,
            "context": t.SecurityManagerContextV13,
            "plaintext_key": t.KeyData,
            "key_data": t.SecurityManagerAPSKeyMetadata,
        },
    ),
    "getApsKeyInfo": (
        0x010C,
        {
            "context_in": t.SecurityManagerContextV13,
        },
        {
            "status": t.sl_Status,
            "key_data": t.SecurityManagerAPSKeyMetadata,
            "context": t.SecurityManagerContextV13,
        },
    ),
    "importKey": (
        0x0115,
        {
            "context": t.SecurityManagerContextV13,
            "key": t.KeyData,
        },
        {
            "status": t.sl_Status,
            "context": t.SecurityManagerContextV13,
        },
    ),
    "findAndRejoinNetwork": (
        0x0021,
        {
            "haveCurrentNetworkKey": t.Bool,
            "channelMask": t.uint32_t,
            "reason": t.uint8_t,
            "nodeType": t.EmberNodeType,
        },
        {
            "status": t.sl_Status,
        },
    ),
    # Replaces `setAddressTableRemoteEui64` and `setAddressTableRemoteNodeId`
    "setAddressTableInfo": (
        0x005C,
        {
            "index": t.uint8_t,
            "eui64": EUI64,
            "nwk": NWK,
        },
        {
            "status": t.sl_Status,
        },
    ),
    "setPowerDescriptor": (
        0x0016,
        {
            "descriptor": t.uint16_t,
        },
        {
            "status": t.sl_Status,
        },
    ),
    "clearStoredBeacons": (
        0x003C,
        {},
        {
            "status": t.sl_Status,
        },
    ),
    # These three still respond with a single byte, not an `sl_Status`
    "sendPanIdUpdate": (
        0x0057,
        {
            "newPan": t.EmberPanId,
        },
        {
            "status": t.Bool,
        },
    ),
    "readAttribute": (
        0x0108,
        {
            "endpoint": t.uint8_t,
            "cluster": t.uint16_t,
            "attributeId": t.uint16_t,
            "mask": t.uint8_t,
            "manufacturerCode": t.uint16_t,
        },
        {
            "status": t.EmberStatus,
            "dataType": t.uint8_t,
            "data": t.LVBytes,
        },
    ),
    "writeAttribute": (
        0x0109,
        {
            "endpoint": t.uint8_t,
            "cluster": t.uint16_t,
            "attributeId": t.uint16_t,
            "mask": t.uint8_t,
            "manufacturerCode": t.uint16_t,
            "overrideReadOnlyAndDataType": t.Bool,
            "justTest": t.Bool,
            "dataType": t.uint8_t,
            "data": t.LVBytes,
        },
        {
            "status": t.EmberStatus,
        },
    ),
    # `lastHopLqi` and `lastHopRssi` were replaced with `packetInfo`
    "macPassthroughMessageHandler": (
        0x0097,
        {},
        {
            "messageType": t.EmberMacPassthroughType,
            "packetInfo": t.SlRxPacketInfo,
            "messageContents": t.LVBytes,
        },
    ),
    "macFilterMatchMessageHandler": (
        0x0046,
        {},
        {
            "filterIndexMatch": t.uint8_t,
            "legacyPassthroughType": t.EmberMacPassthroughType,
            "packetInfo": t.SlRxPacketInfo,
            "messageContents": t.LVBytes,
        },
    ),
    "incomingBootloadMessageHandler": (
        0x0092,
        {},
        {
            "longId": t.EUI64,
            "packetInfo": t.SlRxPacketInfo,
            "messageContents": t.LVBytes,
        },
    ),
    "zllNetworkFoundHandler": (
        0x00B6,
        {},
        {
            "networkInfo": t.EmberZllNetwork,
            "isDeviceInfoNull": t.Bool,
            "deviceInfo": t.EmberZllDeviceInfoRecord,
            "packetInfo": t.SlRxPacketInfo,
        },
    ),
    "zllAddressAssignmentHandler": (
        0x00B8,
        {},
        {
            "addressInfo": t.EmberZllAddressAssignment,
            "packetInfo": t.SlRxPacketInfo,
        },
    ),
    "rawTransmitCompleteHandler": (
        0x0098,
        {},
        {
            "messageContents": t.LVBytes,
            "status": t.sl_Status,
        },
    ),
    "getAddressTableInfo": (
        0x005E,
        {
            "index": t.uint8_t,
        },
        {
            "status": t.sl_Status,
            "nwk": NWK,
            "eui64": EUI64,
        },
    ),
    "incomingMessageHandler": (
        0x0045,
        {},
        {
            "message_type": t.EmberIncomingMessageType,
            "aps_frame": t.EmberApsFrame,
            "nwk": NWK,
            "eui64": EUI64,
            "binding_index": t.uint8_t,
            "address_index": t.uint8_t,
            "lqi": t.uint8_t,
            "rssi": t.int8s,
            "timestamp": t.uint32_t,
            "message": t.LVBytes,
        },
    ),
    "messageSentHandler": (
        0x003F,
        {},
        {
            "status": t.sl_Status,
            "message_type": t.EmberOutgoingMessageType,
            "nwk": NWK,
            "aps_frame": t.EmberApsFrame,
            "message_tag": t.uint16_t,
            "message": t.LVBytes,
        },
    ),
    "sendUnicast": (
        0x0034,
        {
            "message_type": t.EmberOutgoingMessageType,
            "nwk": NWK,
            "aps_frame": t.EmberApsFrame,
            "message_tag": t.uint16_t,
            "message": t.LVBytes,
        },
        {
            "status": t.sl_Status,
            "sequence": t.uint8_t,
        },
    ),
    "sendBroadcast": (
        0x0036,
        {
            "alias": t.uint16_t,
            "destination": BroadcastAddress,
            "sequence": t.uint8_t,
            "aps_frame": t.EmberApsFrame,
            "radius": t.uint8_t,
            "message_tag": t.uint16_t,
            "message": t.LVBytes,
        },
        {
            "status": t.sl_Status,
            "sequence": t.uint8_t,
        },
    ),
    "sendMulticast": (
        0x0038,
        {
            "aps_frame": t.EmberApsFrame,
            "hops": t.uint8_t,
            "broadcast_addr": t.BroadcastAddress,
            "alias": t.uint16_t,
            "sequence": t.uint8_t,
            "message_tag": t.uint16_t,
            "message": t.LVBytes,
        },
        {
            "status": t.sl_Status,
            "sequence": t.uint8_t,
        },
    ),
    "launchStandaloneBootloader": (
        0x008F,
        {
            "mode": t.uint8_t,
        },
        {
            # XXX: One of the few commands that does *not* migrate to `sl_Status`!
            "status": t.EmberStatus,
        },
    ),
}


for name, (command_id, tx_schema, rx_schema) in COMMANDS_v13.items():
    if name in COMMANDS:
        continue

    if isinstance(tx_schema, dict):
        tx_schema = {k: _REPLACEMENTS.get(v, v) for k, v in tx_schema.items()}

    if isinstance(rx_schema, dict):
        rx_schema = {k: _REPLACEMENTS.get(v, v) for k, v in rx_schema.items()}

    COMMANDS[name] = (command_id, tx_schema, rx_schema)

del COMMANDS["getAddressTableRemoteEui64"]
del COMMANDS["setAddressTableRemoteEui64"]

# Removed in v14. Their frame IDs were reused, either right away or in later versions
del COMMANDS["getNextBeacon"]  # 0x0004 is now `getStoredBeacon`
del COMMANDS["proxyBroadcast"]  # 0x0037 is now `setNumBeaconsToStore`
del COMMANDS["sendMulticastWithAlias"]  # 0x003A is now `setupDelayedJoin`
del COMMANDS["getFirstBeacon"]  # 0x003D
del COMMANDS["setAddressTableRemoteNodeId"]  # 0x005D
del COMMANDS["getAddressTableRemoteNodeId"]  # 0x005F
del COMMANDS["incomingSenderEui64Handler"]  # 0x0062

# Removed in v14
del COMMANDS["sendRawMessage"]  # Now the name of 0x0051, `sendRawMessageExtended`
del COMMANDS["setLongUpTime"]
del COMMANDS["setHubConnectivity"]
del COMMANDS["isUpTimeLong"]
del COMMANDS["isHubConnected"]
del COMMANDS["setParentClassificationEnabled"]
del COMMANDS["getParentClassificationEnabled"]
