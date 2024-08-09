import bellows.types as t

COMMANDS = {
    # 4. Configuration frames
    "version": (
        0x00,
        {
            "desiredProtocolVersion": t.uint8_t,
        },
        {
            "protocolVersion": t.uint8_t,
            "stackType": t.uint8_t,
            "stackVersion": t.uint16_t,
        },
    ),
    "getConfigurationValue": (
        0x52,
        {
            "configId": t.EzspConfigId,
        },
        {
            "status": t.EzspStatus,
            "value": t.uint16_t,
        },
    ),
    "setConfigurationValue": (
        0x53,
        {
            "configId": t.EzspConfigId,
            "value": t.uint16_t,
        },
        {
            "status": t.EzspStatus,
        },
    ),
    "addEndpoint": (
        0x02,
        {
            "endpoint": t.uint8_t,
            "profileId": t.uint16_t,
            "deviceId": t.uint16_t,
            "deviceVersion": t.uint8_t,
            "inputClusterCount": t.uint8_t,
            "outputClusterCount": t.uint8_t,
            "inputClusterList": t.List[t.uint16_t],
            "outputClusterList": t.List[t.uint16_t],
        },
        {
            "status": t.EzspStatus,
        },
    ),
    "setPolicy": (
        0x55,
        {
            "policyId": t.EzspPolicyId,
            "decisionId": t.EzspDecisionId,
        },
        {
            "status": t.EzspStatus,
        },
    ),
    "getPolicy": (
        0x56,
        {
            "policyId": t.EzspPolicyId,
        },
        {
            "status": t.EzspStatus,
            "decisionId": t.EzspDecisionId,
        },
    ),
    "getValue": (
        0xAA,
        {
            "valueId": t.EzspValueId,
        },
        {
            "status": t.EzspStatus,
            "value": t.LVBytes,
        },
    ),
    "getExtendedValue": (
        0x03,
        {
            "valueId": t.EzspExtendedValueId,
            "characteristics": t.uint32_t,
        },
        {
            "status": t.EzspStatus,
            "value": t.LVBytes,
        },
    ),
    "setValue": (
        0xAB,
        {
            "valueId": t.EzspValueId,
            "value": t.LVBytes,
        },
        {
            "status": t.EzspStatus,
        },
    ),
    "setGpioCurrentConfiguration": (
        0xAC,
        {
            "portPin": t.uint8_t,
            "cfg": t.uint8_t,
            "out": t.uint8_t,
        },
        {
            "status": t.EzspStatus,
        },
    ),
    "setGpioPowerUpDownConfiguration": (
        0xAD,
        {
            "portPin": t.uint8_t,
            "puCfg": t.uint8_t,
            "puOut": t.uint8_t,
            "pdCfg": t.uint8_t,
            "pdOut": t.uint8_t,
        },
        {
            "status": t.EzspStatus,
        },
    ),
    "setGpioRadioPowerMask": (
        0xAE,
        {
            "mask": t.uint32_t,
        },
        {},
    ),
    "setCtune": (
        0xF5,
        {
            "ctune": t.uint16_t,
        },
        {},
    ),
    "getCtune": (
        0xF6,
        {},
        {
            "ctune": t.uint16_t,
        },
    ),
    # 5. Utilities Frames
    "nop": (
        0x05,
        {},
        {},
    ),
    "echo": (
        0x81,
        {
            "data": t.LVBytes,
        },
        {
            "echo": t.LVBytes,
        },
    ),
    "invalidCommand": (
        0x58,
        {},
        {
            "status": t.EzspStatus,
        },
    ),
    "callback": (
        0x06,
        {},
        {},
    ),
    "noCallbacks": (
        0x07,
        {},
        {},
    ),
    "setToken": (
        0x09,
        {
            "tokenId": t.uint8_t,
            "tokenData": t.FixedList[t.uint8_t, 8],
        },
        {
            "status": t.EmberStatus,
        },
    ),
    "getToken": (
        0x0A,
        {
            "tokenId": t.uint8_t,
        },
        {
            "status": t.EmberStatus,
            "tokenData": t.FixedList[t.uint8_t, 8],
        },
    ),
    "getMfgToken": (
        0x0B,
        {
            "tokenId": t.EzspMfgTokenId,
        },
        {
            "tokenData": t.LVBytes,
        },
    ),
    "setMfgToken": (
        0x0C,
        {
            "tokenId": t.EzspMfgTokenId,
            "tokenData": t.LVBytes,
        },
        {
            "status": t.EmberStatus,
        },
    ),
    "stackTokenChangedHandler": (
        0x0D,
        {},
        {
            "tokenAddress": t.uint16_t,
        },
    ),
    "getRandomNumber": (
        0x49,
        {},
        {
            "status": t.EmberStatus,
            "value": t.uint16_t,
        },
    ),
    "setTimer": (
        0x0E,
        {
            "timerId": t.uint8_t,
            "time": t.uint16_t,
            "units": t.EmberEventUnits,
            "repeat": t.Bool,
        },
        {
            "status": t.EmberStatus,
        },
    ),
    "getTimer": (
        0x4E,
        {
            "timerId": t.uint8_t,
        },
        {
            "time": t.uint16_t,
            "units": t.EmberEventUnits,
            "repeat": t.Bool,
        },
    ),
    "timerHandler": (
        0x0F,
        {},
        {
            "timerId": t.uint8_t,
        },
    ),
    "debugWrite": (
        0x12,
        {
            "binaryMessage": t.Bool,
            "messageContents": t.LVBytes,
        },
        {
            "status": t.EmberStatus,
        },
    ),
    "readAndClearCounters": (
        0x65,
        {},
        {
            "values": t.List[t.uint16_t],
        },
    ),
    "readCounters": (
        0xF1,
        {},
        {
            "values": t.List[t.uint16_t],
        },
    ),
    "counterRolloverHandler": (
        0xF2,
        {},
        {
            "type": t.EmberCounterType,
        },
    ),
    "delayTest": (
        0x9D,
        {
            "delay": t.uint16_t,
        },
        {},
    ),
    "getLibraryStatus": (
        0x01,
        {
            "libraryId": t.uint8_t,
        },
        {
            "status": t.uint8_t,
        },
    ),
    "getXncpInfo": (
        0x13,
        {},
        {
            "status": t.EmberStatus,
            "manufacturerId": t.uint16_t,
            "versionNumber": t.uint16_t,
        },
    ),
    "customFrame": (
        0x47,
        {
            "payload": t.LVBytes,
        },
        {
            "status": t.EmberStatus,
            "reply": t.LVBytes,
        },
    ),
    "customFrameHandler": (
        0x54,
        {},
        {
            "payload": t.LVBytes,
        },
    ),
    "getEui64": (
        0x26,
        {},
        {
            "eui64": t.EUI64,
        },
    ),
    "getNodeId": (
        0x27,
        {},
        {
            "nodeId": t.EmberNodeId,
        },
    ),
    "networkInit": (
        0x17,
        {},
        {
            "status": t.EmberStatus,
        },
    ),
    # 6. Networking Frames
    "setManufacturerCode": (
        0x15,
        {
            "code": t.uint16_t,
        },
        {},
    ),
    "setPowerDescriptor": (
        0x16,
        {
            "descriptor": t.uint16_t,
        },
        {},
    ),
    "networkInitExtended": (
        0x70,
        {
            "networkInitStruct": t.EmberNetworkInitBitmask,
        },
        {
            "status": t.EmberStatus,
        },
    ),
    "networkState": (
        0x18,
        {},
        {
            "status": t.EmberNetworkStatus,
        },
    ),
    "stackStatusHandler": (
        0x19,
        {},
        {
            "status": t.EmberStatus,
        },
    ),
    "startScan": (
        0x1A,
        {
            "scanType": t.EzspNetworkScanType,
            "channelMask": t.Channels,
            "duration": t.uint8_t,
        },
        {
            "status": t.EmberStatus,
        },
    ),
    "energyScanResultHandler": (
        0x48,
        {},
        {
            "channel": t.uint8_t,
            "maxRssiValue": t.int8s,
        },
    ),
    "networkFoundHandler": (
        0x1B,
        {},
        {
            "networkFound": t.EmberZigbeeNetwork,
            "lastHopLqi": t.uint8_t,
            "lastHopRssi": t.int8s,
        },
    ),
    "scanCompleteHandler": (
        0x1C,
        {},
        {
            "channel": t.uint8_t,
            "status": t.EmberStatus,
        },
    ),
    "stopScan": (
        0x1D,
        {},
        {
            "status": t.EmberStatus,
        },
    ),
    "formNetwork": (
        0x1E,
        {
            "parameters": t.EmberNetworkParameters,
        },
        {
            "status": t.EmberStatus,
        },
    ),
    "joinNetwork": (
        0x1F,
        {
            "nodeType": t.EmberNodeType,
            "parameters": t.EmberNetworkParameters,
        },
        {
            "status": t.EmberStatus,
        },
    ),
    "leaveNetwork": (
        0x20,
        {},
        {
            "status": t.EmberStatus,
        },
    ),
    "findAndRejoinNetwork": (
        0x21,
        {
            "haveCurrentNetworkKey": t.Bool,
            "channelMask": t.uint32_t,
        },
        {
            "status": t.EmberStatus,
        },
    ),
    "permitJoining": (
        0x22,
        {
            "duration": t.uint8_t,
        },
        {
            "status": t.EmberStatus,
        },
    ),
    "childJoinHandler": (
        0x23,
        {},
        {
            "index": t.uint8_t,
            "joining": t.Bool,
            "childId": t.EmberNodeId,
            "childEui64": t.EUI64,
            "childType": t.EmberNodeType,
        },
    ),
    "energyScanRequest": (
        0x9C,
        {
            "target": t.EmberNodeId,
            "scanChannels": t.Channels,
            "scanDuration": t.uint8_t,
            "scanCount": t.uint16_t,
        },
        {
            "status": t.EmberStatus,
        },
    ),
    "getNetworkParameters": (
        0x28,
        {},
        {
            "status": t.EmberStatus,
            "nodeType": t.EmberNodeType,
            "parameters": t.EmberNetworkParameters,
        },
    ),
    "getParentChildParameters": (
        0x29,
        {},
        {
            "childCount": t.uint8_t,
            "parentEui64": t.EUI64,
            "parentNodeId": t.EmberNodeId,
        },
    ),
    "getChildData": (
        0x4A,
        {
            "index": t.uint8_t,
        },
        {
            "status": t.EmberStatus,
            "childId": t.EmberNodeId,
            "childEui64": t.EUI64,
            "childType": t.EmberNodeType,
        },
    ),
    "getNeighbor": (
        0x79,
        {
            "index": t.uint8_t,
        },
        {
            "status": t.EmberStatus,
            "value": t.EmberNeighborTableEntry,
        },
    ),
    "neighborCount": (
        0x7A,
        {},
        {
            "value": t.uint8_t,
        },
    ),
    "getRouteTableEntry": (
        0x7B,
        {
            "index": t.uint8_t,
        },
        {
            "status": t.EmberStatus,
            "value": t.EmberRouteTableEntry,
        },
    ),
    "setRadioPower": (
        0x99,
        {
            "power": t.int8s,
        },
        {
            "status": t.EmberStatus,
        },
    ),
    "setRadioChannel": (
        0x9A,
        {
            "channel": t.uint8_t,
        },
        {
            "status": t.EmberStatus,
        },
    ),
    "setConcentrator": (
        0x10,
        {
            "on": t.Bool,
            "concentratorType": t.uint16_t,
            "minTime": t.uint16_t,
            "maxTime": t.uint16_t,
            "routeErrorThreshold": t.uint8_t,
            "deliveryFailureThreshold": t.uint8_t,
            "maxHops": t.uint8_t,
        },
        {
            "status": t.EmberStatus,
        },
    ),
    # 7. Binding Frames
    "clearBindingTable": (
        0x2A,
        {},
        {
            "status": t.EmberStatus,
        },
    ),
    "setBinding": (
        0x2B,
        {
            "index": t.uint8_t,
            "value": t.EmberBindingTableEntry,
        },
        {
            "status": t.EmberStatus,
        },
    ),
    "getBinding": (
        0x2C,
        {
            "index": t.uint8_t,
        },
        {
            "status": t.EmberStatus,
            "value": t.EmberBindingTableEntry,
        },
    ),
    "deleteBinding": (
        0x2D,
        {
            "index": t.uint8_t,
        },
        {
            "status": t.EmberStatus,
        },
    ),
    "bindingIsActive": (
        0x2E,
        {
            "index": t.uint8_t,
        },
        {
            "active": t.Bool,
        },
    ),
    "getBindingRemoteNodeId": (
        0x2F,
        {
            "index": t.uint8_t,
        },
        {
            "nodeId": t.EmberNodeId,
        },
    ),
    "setBindingRemoteNodeId": (
        0x30,
        {
            "index": t.uint8_t,
            "nodeId": t.EmberNodeId,
        },
        {},
    ),
    "remoteSetBindingHandler": (
        0x31,
        {},
        {
            "entry": t.EmberBindingTableEntry,
            "index": t.uint8_t,
            "policyDecision": t.EmberStatus,
        },
    ),
    "remoteDeleteBindingHandler": (
        0x32,
        {},
        {
            "index": t.uint8_t,
            "policyDecision": t.EmberStatus,
        },
    ),
    # 8. Messaging Frames
    "maximumPayloadLength": (
        0x33,
        {},
        {
            "apsLength": t.uint8_t,
        },
    ),
    "sendUnicast": (
        0x34,
        {
            "type": t.EmberOutgoingMessageType,
            "indexOrDestination": t.EmberNodeId,
            "apsFrame": t.EmberApsFrame,
            "messageTag": t.uint8_t,
            "messageContents": t.LVBytes,
        },
        {
            "status": t.EmberStatus,
            "sequence": t.uint8_t,
        },
    ),
    "sendBroadcast": (
        0x36,
        {
            "destination": t.EmberNodeId,
            "apsFrame": t.EmberApsFrame,
            "radius": t.uint8_t,
            "messageTag": t.uint8_t,
            "messageContents": t.LVBytes,
        },
        {
            "status": t.EmberStatus,
            "sequence": t.uint8_t,
        },
    ),
    "proxyBroadcast": (
        0x37,
        {
            "source": t.EmberNodeId,
            "destination": t.EmberNodeId,
            "nwkSequence": t.uint8_t,
            "apsFrame": t.EmberApsFrame,
            "radius": t.uint8_t,
            "messageTag": t.uint8_t,
            "messageContents": t.LVBytes,
        },
        {
            "status": t.EmberStatus,
            "apsSequence": t.uint8_t,
        },
    ),
    "sendMulticast": (
        0x38,
        {
            "apsFrame": t.EmberApsFrame,
            "hops": t.uint8_t,
            "nonmemberRadius": t.uint8_t,
            "messageTag": t.uint8_t,
            "messageContents": t.LVBytes,
        },
        {
            "status": t.EmberStatus,
            "sequence": t.uint8_t,
        },
    ),
    "sendReply": (
        0x39,
        {
            "sender": t.EmberNodeId,
            "apsFrame": t.EmberApsFrame,
            "messageContents": t.LVBytes,
        },
        {
            "status": t.EmberStatus,
        },
    ),
    "messageSentHandler": (
        0x3F,
        {},
        {
            "type": t.EmberOutgoingMessageType,
            "indexOrDestination": t.uint16_t,
            "apsFrame": t.EmberApsFrame,
            "messageTag": t.uint8_t,
            "status": t.EmberStatus,
            "messageContents": t.LVBytes,
        },
    ),
    "sendManyToOneRouteRequest": (
        0x41,
        {
            "concentratorType": t.uint16_t,
            "radius": t.uint8_t,
        },
        {
            "status": t.EmberStatus,
        },
    ),
    "pollForData": (
        0x42,
        {
            "interval": t.uint16_t,
            "units": t.EmberEventUnits,
            "failureLimit": t.uint8_t,
        },
        {
            "status": t.EmberStatus,
        },
    ),
    "pollCompleteHandler": (
        0x43,
        {},
        {
            "status": t.EmberStatus,
        },
    ),
    "pollHandler": (
        0x44,
        {},
        {
            "childId": t.EmberNodeId,
        },
    ),
    "incomingSenderEui64Handler": (
        0x62,
        {},
        {
            "senderEui64": t.EUI64,
        },
    ),
    "incomingMessageHandler": (
        0x45,
        {},
        {
            "type": t.EmberIncomingMessageType,
            "apsFrame": t.EmberApsFrame,
            "lastHopLqi": t.uint8_t,
            "lastHopRssi": t.int8s,
            "sender": t.EmberNodeId,
            "bindingIndex": t.uint8_t,
            "addressIndex": t.uint8_t,
            "messageContents": t.LVBytes,
        },
    ),
    "incomingRouteRecordHandler": (
        0x59,
        {},
        {
            "source": t.EmberNodeId,
            "sourceEui": t.EUI64,
            "lastHopLqi": t.uint8_t,
            "lastHopRssi": t.int8s,
            "relayList": t.LVList[t.EmberNodeId],
        },
    ),
    "setSourceRoute": (
        0x5A,
        {
            "destination": t.EmberNodeId,
            "relayList": t.LVList[t.EmberNodeId],
        },
        {
            "status": t.EmberStatus,
        },
    ),
    "incomingManyToOneRouteRequestHandler": (
        0x7D,
        {},
        {
            "source": t.EmberNodeId,
            "longId": t.EUI64,
            "cost": t.uint8_t,
        },
    ),
    "incomingRouteErrorHandler": (
        0x80,
        {},
        {
            "status": t.EmberStatus,
            "target": t.EmberNodeId,
        },
    ),
    "addressTableEntryIsActive": (
        0x5B,
        {
            "addressTableIndex": t.uint8_t,
        },
        {
            "active": t.Bool,
        },
    ),
    "setAddressTableRemoteEui64": (
        0x5C,
        {
            "addressTableIndex": t.uint8_t,
            "eui64": t.EUI64,
        },
        {
            "status": t.EmberStatus,
        },
    ),
    "setAddressTableRemoteNodeId": (
        0x5D,
        {
            "addressTableIndex": t.uint8_t,
            "id": t.EmberNodeId,
        },
        {},
    ),
    "getAddressTableRemoteEui64": (
        0x5E,
        {
            "addressTableIndex": t.uint8_t,
        },
        {
            "eui64": t.EUI64,
        },
    ),
    "getAddressTableRemoteNodeId": (
        0x5F,
        {
            "addressTableIndex": t.uint8_t,
        },
        {
            "nodeId": t.EmberNodeId,
        },
    ),
    "setExtendedTimeout": (
        0x7E,
        {
            "remoteEui64": t.EUI64,
            "extendedTimeout": t.Bool,
        },
        {},
    ),
    "getExtendedTimeout": (
        0x7F,
        {
            "remoteEui64": t.EUI64,
        },
        {
            "extendedTimeout": t.Bool,
        },
    ),
    "replaceAddressTableEntry": (
        0x82,
        {
            "addressTableIndex": t.uint8_t,
            "newEui64": t.EUI64,
            "newId": t.EmberNodeId,
            "newExtendedTimeout": t.Bool,
        },
        {
            "status": t.EmberStatus,
            "oldEui64": t.EUI64,
            "oldId": t.EmberNodeId,
            "oldExtendedTimeout": t.Bool,
        },
    ),
    "lookupNodeIdByEui64": (
        0x60,
        {
            "eui64": t.EUI64,
        },
        {
            "nodeId": t.EmberNodeId,
        },
    ),
    "lookupEui64ByNodeId": (
        0x61,
        {
            "nodeId": t.EmberNodeId,
        },
        {
            "status": t.EmberStatus,
            "eui64": t.EUI64,
        },
    ),
    "getMulticastTableEntry": (
        0x63,
        {
            "index": t.uint8_t,
        },
        {
            "status": t.EmberStatus,
            "value": t.EmberMulticastTableEntry,
        },
    ),
    "setMulticastTableEntry": (
        0x64,
        {
            "index": t.uint8_t,
            "value": t.EmberMulticastTableEntry,
        },
        {
            "status": t.EmberStatus,
        },
    ),
    "idConflictHandler": (
        0x7C,
        {},
        {
            "nodeId": t.EmberNodeId,
        },
    ),
    "sendRawMessage": (
        0x96,
        {
            "messageContents": t.LVBytes,
        },
        {
            "status": t.EmberStatus,
        },
    ),
    "macPassthroughMessageHandler": (
        0x97,
        {},
        {
            "messageType": t.EmberMacPassthroughType,
            "lastHopLqi": t.uint8_t,
            "lastHopRssi": t.int8s,
            "messageContents": t.LVBytes,
        },
    ),
    "macFilterMatchMessageHandler": (
        0x46,
        {},
        {
            "filterIndexMatch": t.uint8_t,
            "legacyPassthroughType": t.EmberMacPassthroughType,
            "lastHopLqi": t.uint8_t,
            "lastHopRssi": t.int8s,
            "messageContents": t.LVBytes,
        },
    ),
    "rawTransmitCompleteHandler": (
        0x98,
        {},
        {
            "status": t.EmberStatus,
        },
    ),
    # 9. Security Frames
    "setInitialSecurityState": (
        0x68,
        {
            "state": t.EmberInitialSecurityState,
        },
        {
            "status": t.EmberStatus,
        },
    ),
    "getCurrentSecurityState": (
        0x69,
        {},
        {
            "status": t.EmberStatus,
            "state": t.EmberCurrentSecurityState,
        },
    ),
    "getKey": (
        0x6A,
        {
            "keyType": t.EmberKeyType,
        },
        {
            "status": t.EmberStatus,
            "keyStruct": t.EmberKeyStruct,
        },
    ),
    "switchNetworkKeyHandler": (
        0x6E,
        {},
        {
            "sequenceNumber": t.uint8_t,
        },
    ),
    "getKeyTableEntry": (
        0x71,
        {
            "index": t.uint8_t,
        },
        {
            "status": t.EmberStatus,
            "keyStruct": t.EmberKeyStruct,
        },
    ),
    "setKeyTableEntry": (
        0x72,
        {
            "index": t.uint8_t,
            "address": t.EUI64,
            "linkKey": t.Bool,
            "keyData": t.KeyData,
        },
        {
            "status": t.EmberStatus,
        },
    ),
    "findKeyTableEntry": (
        0x75,
        {
            "address": t.EUI64,
            "linkKey": t.Bool,
        },
        {
            "index": t.uint8_t,
        },
    ),
    "addOrUpdateKeyTableEntry": (
        0x66,
        {
            "address": t.EUI64,
            "linkKey": t.Bool,
            "keyData": t.KeyData,
        },
        {
            "status": t.EmberStatus,
        },
    ),
    "eraseKeyTableEntry": (
        0x76,
        {
            "index": t.uint8_t,
        },
        {
            "status": t.EmberStatus,
        },
    ),
    "clearKeyTable": (
        0xB1,
        {},
        {
            "status": t.EmberStatus,
        },
    ),
    "requestLinkKey": (
        0x14,
        {
            "partner": t.EUI64,
        },
        {
            "status": t.EmberStatus,
        },
    ),
    "zigbeeKeyEstablishmentHandler": (
        0x9B,
        {},
        {
            "partner": t.EUI64,
            "status": t.EmberKeyStatus,
        },
    ),
    "addTransientLinkKey": (
        0xAF,
        {
            "partner": t.EUI64,
            "transientKey": t.KeyData,
        },
        {
            "status": t.EmberStatus,
        },
    ),
    "clearTransientLinkKeys": (
        0x6B,
        {},
        {},
    ),
    # 10. Trust Center Frames
    "trustCenterJoinHandler": (
        0x24,
        {},
        {
            "newNodeId": t.EmberNodeId,
            "newNodeEui64": t.EUI64,
            "status": t.EmberDeviceUpdate,
            "policyDecision": t.EmberJoinDecision,
            "parentOfNewNodeId": t.EmberNodeId,
        },
    ),
    "broadcastNextNetworkKey": (
        0x73,
        {
            "key": t.KeyData,
        },
        {
            "status": t.EmberStatus,
        },
    ),
    "broadcastNetworkKeySwitch": (
        0x74,
        {},
        {
            "status": t.EmberStatus,
        },
    ),
    "becomeTrustCenter": (
        0x77,
        {
            "key": t.KeyData,
        },
        {
            "status": t.EmberStatus,
        },
    ),
    "aesMmoHash": (
        0x6F,
        {
            "context": t.EmberAesMmoHashContext,
            "finalize": t.Bool,
            "data": t.LVBytes,
        },
        {
            "status": t.EmberStatus,
            "returnContext": t.EmberAesMmoHashContext,
        },
    ),
    "removeDevice": (
        0xA8,
        {
            "destShort": t.EmberNodeId,
            "destLong": t.EUI64,
            "targetLong": t.EUI64,
        },
        {
            "status": t.EmberStatus,
        },
    ),
    "unicastNwkKeyUpdate": (
        0xA9,
        {
            "destShort": t.EmberNodeId,
            "destLong": t.EUI64,
            "key": t.KeyData,
        },
        {
            "status": t.EmberStatus,
        },
    ),
    # 11. Certificate Based Key Exchange (CBKE) Frames
    "generateCbkeKeys": (
        0xA4,
        {},
        {
            "status": t.EmberStatus,
        },
    ),
    "generateCbkeKeysHandler": (
        0x9E,
        {},
        {
            "status": t.EmberStatus,
            "ephemeralPublicKey": t.EmberPublicKeyData,
        },
    ),
    "calculateSmacs": (
        0x9F,
        {
            "amInitiator": t.Bool,
            "partnerCertificate": t.EmberCertificateData,
            "partnerEphemeralPublicKey": t.EmberPublicKeyData,
        },
        {
            "status": t.EmberStatus,
        },
    ),
    "calculateSmacsHandler": (
        0xA0,
        {},
        {
            "status": t.EmberStatus,
            "initiatorSmac": t.EmberSmacData,
            "responderSmac": t.EmberSmacData,
        },
    ),
    "generateCbkeKeys283k1": (
        0xE8,
        {},
        {
            "status": t.EmberStatus,
        },
    ),
    "generateCbkeKeysHandler283k1": (
        0xE9,
        {},
        {
            "status": t.EmberStatus,
            "ephemeralPublicKey": t.EmberPublicKey283k1Data,
        },
    ),
    "calculateSmacs283k1": (
        0xEA,
        {
            "amInitiator": t.Bool,
            "partnerCertificate": t.EmberCertificate283k1Data,
            "partnerEphemeralPublicKey": t.EmberPublicKey283k1Data,
        },
        {
            "status": t.EmberStatus,
        },
    ),
    "calculateSmacsHandler283k1": (
        0xEB,
        {},
        {
            "status": t.EmberStatus,
            "initiatorSmac": t.EmberSmacData,
            "responderSmac": t.EmberSmacData,
        },
    ),
    "clearTemporaryDataMaybeStoreLinkKey": (
        0xA1,
        {
            "storeLinkKey": t.Bool,
        },
        {
            "status": t.EmberStatus,
        },
    ),
    "clearTemporaryDataMaybeStoreLinkKey283k1": (
        0xEE,
        {
            "storeLinkKey": t.Bool,
        },
        {
            "status": t.EmberStatus,
        },
    ),
    "getCertificate": (
        0xA5,
        {},
        {
            "status": t.EmberStatus,
            "localCert": t.EmberCertificateData,
        },
    ),
    "getCertificate283k1": (
        0xEC,
        {},
        {
            "status": t.EmberStatus,
            "localCert": t.EmberCertificate283k1Data,
        },
    ),
    "dsaSign": (
        0xA6,
        {
            "messageContents": t.LVBytes,
        },
        {
            "status": t.EmberStatus,
        },
    ),  # Deprecated
    "dsaSignHandler": (
        0xA7,
        {},
        {
            "status": t.EmberStatus,
            "messageContents": t.LVBytes,
        },
    ),  # Deprecated
    "dsaVerify": (
        0xA3,
        {
            "digest": t.EmberMessageDigest,
            "signerCertificate": t.EmberCertificateData,
            "receivedSig": t.EmberSignatureData,
        },
        {
            "status": t.EmberStatus,
        },
    ),
    "dsaVerifyHandler": (
        0x78,
        {},
        {
            "status": t.EmberStatus,
        },
    ),
    "dsaVerify283k1": (
        0xB0,
        {
            "digest": t.EmberMessageDigest,
            "signerCertificate": t.EmberCertificate283k1Data,
            "receivedSig": t.EmberSignature283k1Data,
        },
        {
            "status": t.EmberStatus,
        },
    ),
    "setPreinstalledCbkeData": (
        0xA2,
        {
            "caPublic": t.EmberPublicKeyData,
            "myCert": t.EmberCertificateData,
            "myKey": t.EmberPrivateKeyData,
        },
        {
            "status": t.EmberStatus,
        },
    ),
    "savePreinstalledCbkeData283k1": (
        0xED,
        {},
        {
            "status": t.EmberStatus,
        },
    ),
    # 12. Mfglib Frames
    "mfglibStart": (
        0x83,
        {
            "rxCallback": t.Bool,
        },
        {
            "status": t.EmberStatus,
        },
    ),
    "mfglibEnd": (
        0x84,
        {},
        {
            "status": t.EmberStatus,
        },
    ),
    "mfglibStartTone": (
        0x85,
        {},
        {
            "status": t.EmberStatus,
        },
    ),
    "mfglibStopTone": (
        0x86,
        {},
        {
            "status": t.EmberStatus,
        },
    ),
    "mfglibStartStream": (
        0x87,
        {},
        {
            "status": t.EmberStatus,
        },
    ),
    "mfglibStopStream": (
        0x88,
        {},
        {
            "status": t.EmberStatus,
        },
    ),
    "mfglibSendPacket": (
        0x89,
        {
            "packetContents": t.LVBytes,
        },
        {
            "status": t.EmberStatus,
        },
    ),
    "mfglibSetChannel": (
        0x8A,
        {
            "channel": t.uint8_t,
        },
        {
            "status": t.EmberStatus,
        },
    ),
    "mfglibGetChannel": (
        0x8B,
        {},
        {
            "channel": t.uint8_t,
        },
    ),
    "mfglibSetPower": (
        0x8C,
        {
            "txPowerMode": t.uint16_t,
            "power": t.int8s,
        },
        {
            "status": t.EmberStatus,
        },
    ),
    "mfglibGetPower": (
        0x8D,
        {},
        {
            "power": t.int8s,
        },
    ),
    "mfglibRxHandler": (
        0x8E,
        {},
        {
            "linkQuality": t.uint8_t,
            "rssi": t.int8s,
            "packetContents": t.LVBytes,
        },
    ),
    # 13. Bootloader Frames
    "launchStandaloneBootloader": (
        0x8F,
        {
            "mode": t.uint8_t,
        },
        {
            "status": t.EmberStatus,
        },
    ),
    "sendBootloadMessage": (
        0x90,
        {
            "broadcast": t.Bool,
            "destEui64": t.EUI64,
            "messageContents": t.LVBytes,
        },
        {
            "status": t.EmberStatus,
        },
    ),
    "getStandaloneBootloaderVersionPlatMicroPhy": (
        0x91,
        {},
        {
            "bootloader_version": t.uint16_t,
            "nodePlat": t.uint8_t,
            "nodeMicro": t.uint8_t,
            "nodePhy": t.uint8_t,
        },
    ),
    "incomingBootloadMessageHandler": (
        0x92,
        {},
        {
            "longId": t.EUI64,
            "lastHopLqi": t.uint8_t,
            "lastHopRssi": t.int8s,
            "messageContents": t.LVBytes,
        },
    ),
    "bootloadTransmitCompleteHandler": (
        0x93,
        {},
        {
            "status": t.EmberStatus,
            "messageContents": t.LVBytes,
        },
    ),
    "aesEncrypt": (
        0x94,
        {
            "plaintext": t.FixedList[t.uint8_t, 16],
            "key": t.FixedList[t.uint8_t, 16],
        },
        {
            "ciphertext": t.FixedList[t.uint8_t, 16],
        },
    ),
    "overrideCurrentChannel": (
        0x95,
        {
            "channel": t.uint8_t,
        },
        {
            "status": t.EmberStatus,
        },
    ),
    # 14. ZLL Frames
    "zllNetworkOps": (
        0xB2,
        {
            "networkInfo": t.EmberZllNetwork,
            "op": t.EzspZllNetworkOperation,
            "radioTxPower": t.int8s,
        },
        {
            "status": t.EmberStatus,
        },
    ),
    "zllSetInitialSecurityState": (
        0xB3,
        {
            "networkKey": t.KeyData,
            "securityState": t.EmberZllInitialSecurityState,
        },
        {
            "status": t.EmberStatus,
        },
    ),
    "zllStartScan": (
        0xB4,
        {
            "channelMask": t.Channels,
            "radioPowerForScan": t.int8s,
            "nodeType": t.EmberNodeType,
        },
        {
            "status": t.EmberStatus,
        },
    ),
    "zllSetRxOnWhenIdle": (
        0xB5,
        {
            "durationMs": t.uint32_t,
        },
        {
            "status": t.EmberStatus,
        },
    ),
    "zllNetworkFoundHandler": (
        0xB6,
        {},
        {
            "networkInfo": t.EmberZllNetwork,
            "isDeviceInfoNull": t.Bool,
            "deviceInfo": t.EmberZllDeviceInfoRecord,
            "lastHopLqi": t.uint8_t,
            "lastHopRssi": t.int8s,
        },
    ),
    "zllScanCompleteHandler": (
        0xB7,
        {},
        {
            "status": t.EmberStatus,
        },
    ),
    "zllAddressAssignmentHandler": (
        0xB8,
        {},
        {
            "addressInfo": t.EmberZllAddressAssignment,
            "lastHopLqi": t.uint8_t,
            "lastHopRssi": t.int8s,
        },
    ),
    "setLogicalAndRadioChannel": (
        0xB9,
        {
            "": t.uint8_t,
        },
        {
            "status": t.EmberStatus,
        },
    ),
    "getLogicalChannel": (
        0xBA,
        {},
        {
            "radioChannel": t.uint8_t,
        },
    ),
    "zllTouchLinkTargetHandler": (
        0xBB,
        {},
        {
            "networkInfo": t.EmberZllNetwork,
        },
    ),
    "zllGetTokens": (
        0xBC,
        {},
        {
            "data": t.EmberTokTypeStackZllData,
            "security": t.EmberTokTypeStackZllSecurity,
        },
    ),
    "zllSetDataToken": (
        0xBD,
        {
            "data": t.EmberTokTypeStackZllData,
        },
        {},
    ),
    "zllSetNonZllNetwork": (
        0xBF,
        {},
        {},
    ),
    "isZllNetwork": (
        0xBE,
        {},
        {
            "isZllNetwork": t.Bool,
        },
    ),
    # 15 RF4CE Frames
    "rf4ceSetPairingTableEntry": (
        0xD0,
        {
            "pairingIndex": t.uint8_t,
            "entry": t.EmberRf4cePairingTableEntry,
        },
        {
            "status": t.EmberStatus,
        },
    ),
    "rf4ceGetPairingTableEntry": (
        0xD1,
        {
            "pairingIndex": t.uint8_t,
        },
        {
            "status": t.EmberStatus,
            "entry": t.EmberRf4cePairingTableEntry,
        },
    ),
    "rf4ceDeletePairingTableEntry": (
        0xD2,
        {
            "pairingIndex": t.uint8_t,
        },
        {
            "status": t.EmberStatus,
        },
    ),
    "rf4ceKeyUpdate": (
        0xD3,
        {
            "pairingIndex": t.uint8_t,
            "key": t.KeyData,
        },
        {
            "status": t.EmberStatus,
        },
    ),
    "rf4ceSend": (
        0xD4,
        {
            "pairingIndex": t.uint8_t,
            "profileId": t.uint8_t,
            "vendorId": t.uint16_t,
            "txOptions": t.EmberRf4ceTxOption,
            "messageTag": t.uint8_t,
            "message": t.LVBytes,
        },
        {
            "status": t.EmberStatus,
        },
    ),
    "rf4ceIncomingMessageHandler": (
        0xD5,
        {},
        {
            "pairingIndex": t.uint8_t,
            "profileId": t.uint8_t,
            "vendorId": t.uint16_t,
            "txOptions": t.EmberRf4ceTxOption,
            "message": t.LVBytes,
        },
    ),
    "rf4ceMessageSentHandler": (
        0xD6,
        {},
        {
            "status": t.EmberStatus,
            "pairingIndex": t.uint8_t,
            "profileId": t.uint8_t,
            "vendorId": t.uint16_t,
            "txOptions": t.uint8_t,
            "message": t.LVBytes,
        },
    ),
    "rf4ceStart": (
        0xD7,
        {
            "capabilities": t.EmberRf4ceNodeCapabilities,
            "vendorInfo": t.EmberRf4ceVendorInfo,
            "power": t.int8s,
        },
        {
            "status": t.EmberStatus,
        },
    ),
    "rf4ceStop": (
        0xD8,
        {},
        {
            "status": t.EmberStatus,
        },
    ),
    "rf4ceDiscovery": (
        0xD9,
        {
            "panId": t.EmberPanId,
            "nodeId": t.EmberNodeId,
            "searchDevType": t.uint8_t,
            "discDuration": t.uint16_t,
            "maxDiscRepetitions": t.uint8_t,
            "discProfileIdList": t.LVList[t.uint8_t],
        },
        {
            "status": t.EmberStatus,
        },
    ),
    "rf4ceDiscoveryCompleteHandler": (
        0xDA,
        {},
        {
            "status": t.EmberStatus,
        },
    ),
    "rf4ceDiscoveryRequestHandler": (
        0xDB,
        {},
        {
            "ieeeAddr": t.EUI64,
            "nodeCapabilities": t.uint8_t,
            "vendorInfo": t.EmberRf4ceVendorInfo,
            "appInfo": t.EmberRf4ceApplicationInfo,
            "searchDevType": t.uint8_t,
            "rxLinkQuality": t.uint8_t,
        },
    ),
    "rf4ceDiscoveryResponseHandler": (
        0xDC,
        {},
        {
            "atCapacity": t.Bool,
            "channel": t.uint8_t,
            "panId": t.EmberPanId,
            "ieeeAddr": t.EUI64,
            "nodeCapabilities": t.uint8_t,
            "vendorInfo": t.EmberRf4ceVendorInfo,
            "appInfo": t.EmberRf4ceApplicationInfo,
            "rxLinkQuality": t.uint8_t,
            "discRequestLqi": t.uint8_t,
        },
    ),
    "rf4ceEnableAutoDiscoveryResponse": (
        0xDD,
        {
            "duration": t.uint16_t,
        },
        {
            "status": t.EmberStatus,
        },
    ),
    "rf4ceAutoDiscoveryResponseCompleteHandler": (
        0xDE,
        {},
        {
            "status": t.EmberStatus,
            "srcIeeeAddr": t.EUI64,
            "nodeCapabilities": t.uint8_t,
            "vendorInfo": t.EmberRf4ceVendorInfo,
            "appInfo": t.EmberRf4ceApplicationInfo,
            "searchDevType": t.uint8_t,
        },
    ),
    "rf4cePair": (
        0xDF,
        {
            "channel": t.uint8_t,
            "panId": t.EmberPanId,
            "ieeeAddr": t.EUI64,
            "keyExchangeTransferCount": t.uint8_t,
        },
        {
            "status": t.EmberStatus,
        },
    ),
    "rf4cePairCompleteHandler": (
        0xE0,
        {},
        {
            "status": t.EmberStatus,
            "pairingIndex": t.uint8_t,
            "vendorInfo": t.EmberRf4ceVendorInfo,
            "appInfo": t.EmberRf4ceApplicationInfo,
        },
    ),
    "rf4cePairRequestHandler": (
        0xE1,
        {},
        {
            "status": t.EmberStatus,
            "pairingIndex": t.uint8_t,
            "srcIeeeAddr": t.EUI64,
            "nodeCapabilities": t.uint8_t,
            "vendorInfo": t.EmberRf4ceVendorInfo,
            "appInfo": t.EmberRf4ceApplicationInfo,
            "keyExchangeTransferCount": t.uint8_t,
        },
    ),
    "rf4ceUnpair": (
        0xE2,
        {
            "pairingIndex": t.uint8_t,
        },
        {
            "status": t.EmberStatus,
        },
    ),
    "rf4ceUnpairHandler": (
        0xE3,
        {},
        {
            "pairingIndex": t.uint8_t,
        },
    ),
    "rf4ceUnpairCompleteHandler": (
        0xE4,
        {},
        {
            "pairingIndex": t.uint8_t,
        },
    ),
    "rf4ceSetPowerSavingParameters": (
        0xE5,
        {
            "dutyCycle": t.uint32_t,
            "activePeriod": t.uint32_t,
        },
        {
            "status": t.EmberStatus,
        },
    ),
    "rf4ceSetFrequencyAgilityParameters": (
        0xE6,
        {
            "rssiWindowSize": t.uint8_t,
            "channelChangeReads": t.uint8_t,
            "rssiThreshold": t.int8s,
            "readInterval": t.uint16_t,
            "readDuration": t.uint8_t,
        },
        {
            "status": t.EmberStatus,
        },
    ),
    "rf4ceSetApplicationInfo": (
        0xE7,
        {
            "appInfo": t.EmberRf4ceApplicationInfo,
        },
        {
            "status": t.EmberStatus,
        },
    ),
    "rf4ceGetApplicationInfo": (
        0xEF,
        {},
        {
            "status": t.EmberStatus,
            "appInfo": t.EmberRf4ceApplicationInfo,
        },
    ),
    "rf4ceGetMaxPayload": (
        0xF3,
        {
            "pairingIndex": t.uint8_t,
            "txOptions": t.EmberRf4ceTxOption,
        },
        {
            "maxLength": t.uint8_t,
        },
    ),
    "rf4ceGetNetworkParameters": (
        0xF4,
        {},
        {
            "status": t.EmberStatus,
            "nodeType": t.EmberNodeType,
            "parameters": t.EmberNetworkParameters,
        },
    ),
    # 16 Green Power Frames
    "gpProxyTableProcessGpPairing": (
        0xC9,
        {
            "options": t.uint32_t,
            "addr": t.EmberGpAddress,
            "commMode": t.uint8_t,
            "sinkNetworkAddress": t.uint16_t,
            "sinkGroupId": t.uint16_t,
            "assignedAlias": t.uint16_t,
            "sinkIeeeAddress": t.EUI64,
            "gpdKey": t.KeyData,
        },
        {
            "gpPairingAdded": t.Bool,
        },
    ),
    "dGpSend": (
        0xC6,
        {
            "action": t.Bool,
            "useCca": t.Bool,
            "addr": t.EmberGpAddress,
            "gpdCommandId": t.uint8_t,
            "gpdAsdu": t.LVBytes,
            "gpepHandle": t.uint8_t,
            "gpTxQueueEntryLifetimeMs": t.uint16_t,
        },
        {
            "status": t.EmberStatus,
        },
    ),
    "dGpSentHandler": (
        0xC7,
        {},
        {
            "status": t.EmberStatus,
            "gpepHandle": t.uint8_t,
        },
    ),
    "gpepIncomingMessageHandler": (
        0x00C5,
        {},
        {
            "status": t.EmberStatus,
            "gpdLink": t.uint8_t,
            "sequenceNumber": t.uint8_t,
            "addrType": t.uint8_t,
            "addr": t.uint32_t,
            "applicationId": t.uint8_t,
            "address": t.EUI64,  # TODO: `sourceId` if appId == 0 else `gpdIeeeAddress`
            "endpoint": t.uint8_t,
            "gpdfSecurityLevel": t.EmberGpSecurityLevel,
            "gpdfSecurityKeyType": t.EmberGpKeyType,
            "autoCommissioning": t.Bool,
            "bidirectionalInfo": t.Bool,
            "gpdSecurityFrameCounter": t.uint32_t,
            "gpdCommandId": t.uint8_t,
            "mic": t.uint32_t,
            "proxyTableIndex": t.uint8_t,
            "gpdCommandPayload": t.LVBytes,
        },
    ),
}
