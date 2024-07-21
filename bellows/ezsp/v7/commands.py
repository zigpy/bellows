from . import types as t

COMMANDS = {
    # 4. Configuration frames
    "version": (
        0x00,
        (t.uint8_t,),
        (t.uint8_t, t.uint8_t, t.uint16_t),
    ),
    "getConfigurationValue": (
        0x52,
        (t.EzspConfigId,),
        (t.EzspStatus, t.uint16_t),
    ),
    "setConfigurationValue": (
        0x53,
        (t.EzspConfigId, t.uint16_t),
        (t.EzspStatus,),
    ),
    "addEndpoint": (
        0x02,
        (
            t.uint8_t,
            t.uint16_t,
            t.uint16_t,
            t.uint8_t,
            t.uint8_t,
            t.uint8_t,
            t.List[t.uint16_t],
            t.List[t.uint16_t],
        ),
        (t.EzspStatus,),
    ),
    "setPolicy": (
        0x55,
        (t.EzspPolicyId, t.EzspDecisionId),
        (t.EzspStatus,),
    ),
    "getPolicy": (
        0x56,
        (t.EzspPolicyId,),
        (t.EzspStatus, t.EzspDecisionId),
    ),
    "sendPanIdUpdate": (
        0x57,
        (t.EmberPanId,),
        (t.Bool,),
    ),
    "getValue": (
        0xAA,
        (t.EzspValueId,),
        (t.EzspStatus, t.LVBytes),
    ),
    "getExtendedValue": (
        0x03,
        (t.EzspExtendedValueId, t.uint32_t),
        (t.EzspStatus, t.LVBytes),
    ),
    "setValue": (
        0xAB,
        (t.EzspValueId, t.LVBytes),
        (t.EzspStatus,),
    ),
    "setGpioCurrentConfiguration": (
        0xAC,
        (t.uint8_t, t.uint8_t, t.uint8_t),
        (t.EzspStatus,),
    ),
    "setGpioPowerUpDownConfiguration": (
        0xAD,
        (t.uint8_t, t.uint8_t, t.uint8_t, t.uint8_t, t.uint8_t),
        (t.EzspStatus,),
    ),
    "setGpioRadioPowerMask": (
        0xAE,
        (t.uint32_t,),
        (),
    ),
    "setCtune": (
        0xF5,
        (t.uint16_t,),
        (),
    ),
    "getCtune": (
        0xF6,
        (),
        (t.uint16_t,),
    ),
    # 5. Utilities Frames
    "nop": (
        0x05,
        (),
        (),
    ),
    "echo": (
        0x81,
        (t.LVBytes,),
        (t.LVBytes,),
    ),
    "invalidCommand": (
        0x58,
        (),
        (t.EzspStatus,),
    ),
    "callback": (
        0x06,
        (),
        (),
    ),
    "noCallbacks": (
        0x07,
        (),
        (),
    ),
    "setToken": (
        0x09,
        (t.uint8_t, t.FixedList[t.uint8_t, 8]),
        (t.EmberStatus,),
    ),
    "getToken": (
        0x0A,
        (t.uint8_t,),
        (t.EmberStatus, t.FixedList[t.uint8_t, 8]),
    ),
    "getMfgToken": (
        0x0B,
        (t.EzspMfgTokenId,),
        (t.LVBytes,),
    ),
    "setMfgToken": (
        0x0C,
        (t.EzspMfgTokenId, t.LVBytes),
        (t.EmberStatus,),
    ),
    "stackTokenChangedHandler": (
        0x0D,
        (),
        (t.uint16_t,),
    ),
    "getRandomNumber": (
        0x49,
        (),
        (t.EmberStatus, t.uint16_t),
    ),
    "setTimer": (
        0x0E,
        (t.uint8_t, t.uint16_t, t.EmberEventUnits, t.Bool),
        (t.EmberStatus,),
    ),
    "getTimer": (
        0x4E,
        (t.uint8_t,),
        (t.uint16_t, t.EmberEventUnits, t.Bool),
    ),
    "timerHandler": (
        0x0F,
        (),
        (t.uint8_t,),
    ),
    "debugWrite": (
        0x12,
        (t.Bool, t.LVBytes),
        (t.EmberStatus,),
    ),
    "readAndClearCounters": (
        0x65,
        (),
        (t.FixedList[t.uint16_t, len(t.EmberCounterType)],),
    ),
    "readCounters": (
        0xF1,
        (),
        (t.FixedList[t.uint16_t, len(t.EmberCounterType)],),
    ),
    "counterRolloverHandler": (
        0xF2,
        (),
        (t.EmberCounterType,),
    ),
    "delayTest": (
        0x9D,
        (t.uint16_t,),
        (),
    ),
    "getLibraryStatus": (
        0x01,
        (t.uint8_t,),
        (t.EmberLibraryStatus,),
    ),
    "getXncpInfo": (
        0x13,
        (),
        (t.EmberStatus, t.uint16_t, t.uint16_t),
    ),
    "customFrame": (
        0x47,
        (t.LVBytes,),
        (t.EmberStatus, t.LVBytes),
    ),
    "customFrameHandler": (
        0x54,
        (),
        (t.LVBytes,),
    ),
    "getEui64": (
        0x26,
        (),
        (t.EUI64,),
    ),
    "getNodeId": (
        0x27,
        (),
        (t.EmberNodeId,),
    ),
    "getPhyInterfaceCount": (
        0xFC,
        (),
        (t.uint8_t,),
    ),
    "getTrueRandomEntropySource": (
        0x4F,
        (),
        (t.EmberEntropySource,),
    ),
    "networkInit": (
        0x17,
        (t.EmberNetworkInitBitmask,),
        (t.EmberStatus,),
    ),
    # 6. Networking Frames
    "setManufacturerCode": (
        0x15,
        (t.uint16_t,),
        (),
    ),
    "setPowerDescriptor": (
        0x16,
        (t.uint16_t,),
        (),
    ),
    "networkState": (
        0x18,
        (),
        (t.EmberNetworkStatus,),
    ),
    "stackStatusHandler": (
        0x19,
        (),
        (t.EmberStatus,),
    ),
    "startScan": (
        0x1A,
        (t.EzspNetworkScanType, t.uint32_t, t.uint8_t),
        (t.EmberStatus,),
    ),
    "energyScanResultHandler": (
        0x48,
        (),
        (t.uint8_t, t.int8s),
    ),
    "networkFoundHandler": (
        0x1B,
        (),
        (t.EmberZigbeeNetwork, t.uint8_t, t.int8s),
    ),
    "scanCompleteHandler": (
        0x1C,
        (),
        (t.uint8_t, t.EmberStatus),
    ),
    "unusedPanIdFoundHandler": (
        0xD2,
        (),
        (t.uint8_t, t.EmberStatus),
    ),
    "findUnusedPanId": (
        0xD3,
        (t.Channels, t.uint8_t),
        (t.EmberStatus,),
    ),
    "stopScan": (
        0x1D,
        (),
        (t.EmberStatus,),
    ),
    "formNetwork": (
        0x1E,
        (t.EmberNetworkParameters,),
        (t.EmberStatus,),
    ),
    "joinNetwork": (
        0x1F,
        (t.EmberNodeType, t.EmberNetworkParameters),
        (t.EmberStatus,),
    ),
    "joinNetworkDirectly": (
        0x3B,
        (t.EmberNodeType, t.EmberBeaconData, t.int8s, t.Bool),
        (t.EmberStatus,),
    ),
    "leaveNetwork": (
        0x20,
        (),
        (t.EmberStatus,),
    ),
    "findAndRejoinNetwork": (
        0x21,
        (t.Bool, t.uint32_t),
        (t.EmberStatus,),
    ),
    "permitJoining": (
        0x22,
        (t.uint8_t,),
        (t.EmberStatus,),
    ),
    "childJoinHandler": (
        0x23,
        (),
        (t.uint8_t, t.Bool, t.EmberNodeId, t.EUI64, t.EmberNodeType),
    ),
    "energyScanRequest": (
        0x9C,
        (t.EmberNodeId, t.Channels, t.uint8_t, t.uint16_t),
        (t.EmberStatus,),
    ),
    "getNetworkParameters": (
        0x28,
        (),
        (t.EmberStatus, t.EmberNodeType, t.EmberNetworkParameters),
    ),
    "getRadioParameters": (
        0xFD,
        (t.uint8_t,),
        (t.EmberStatus, t.EmberNodeType, t.EmberNetworkParameters),
    ),
    "getParentChildParameters": (
        0x29,
        (),
        (t.uint8_t, t.EUI64, t.EmberNodeId),
    ),
    "getChildData": (
        0x4A,
        (t.uint8_t,),
        (t.EmberStatus, t.EmberChildData),
    ),
    "getSourceRouteTableTotalSize": (
        0xC3,
        (),
        (t.uint8_t,),
    ),
    "getSourceRouteTableFilledSize": (
        0xC2,
        (),
        (t.uint8_t,),
    ),
    "getSourceRouteTableEntry": (
        0xC1,
        (t.uint8_t,),
        (t.EmberStatus, t.EmberNodeId, t.uint8_t),
    ),
    "getNeighbor": (
        0x79,
        (t.uint8_t,),
        (t.EmberStatus, t.EmberNeighborTableEntry),
    ),
    "setRoutingShortcutThreshold": (
        0xD0,
        (t.uint8_t,),
        (t.EmberStatus,),
    ),
    "getRoutingShortcutThreshold": (
        0xD1,
        (),
        (t.uint8_t,),
    ),
    "neighborCount": (
        0x7A,
        (),
        (t.uint8_t,),
    ),
    "getRouteTableEntry": (
        0x7B,
        (t.uint8_t,),
        (t.EmberStatus, t.EmberRouteTableEntry),
    ),
    "setRadioPower": (
        0x99,
        (t.int8s,),
        (t.EmberStatus,),
    ),
    "setRadioChannel": (
        0x9A,
        (t.uint8_t,),
        (t.EmberStatus,),
    ),
    "setConcentrator": (
        0x10,
        (t.Bool, t.uint16_t, t.uint16_t, t.uint16_t, t.uint8_t, t.uint8_t, t.uint8_t),
        (t.EmberStatus,),
    ),
    "setBrokenRouteErrorCode": (
        0x11,
        (t.uint8_t,),
        (t.EmberStatus,),
    ),
    "multiPhyStart": (
        0xF8,
        (t.uint8_t, t.uint8_t, t.uint8_t, t.int8s, t.EmberMultiPhyNwkConfig),
        (t.EmberStatus,),
    ),
    "multiPhyStop": (
        0xF9,
        (t.uint8_t,),
        (t.EmberStatus,),
    ),
    "multiPhySetRadioPower": (
        0xFA,
        (t.uint8_t, t.int8s),
        (t.EmberStatus,),
    ),
    "sendLinkPowerDeltaRequest": (
        0xF7,
        (),
        (t.EmberStatus,),
    ),
    "multiPhySetRadioChannel": (
        0xFB,
        (t.uint8_t, t.uint8_t, t.uint8_t),
        (t.EmberStatus,),
    ),
    "getDutyCycleState": (
        0x35,
        (),
        (t.EmberStatus, t.EmberDutyCycleState),
    ),
    "setDutyCycleLimitsInStack": (
        0x40,
        (t.EmberDutyCycleLimits,),
        (t.EmberStatus, t.EmberDutyCycleState),
    ),
    "getDutyCycleLimits": (
        0x4B,
        (),
        (t.EmberStatus, t.EmberDutyCycleLimits),
    ),
    "getCurrentDutyCycle": (
        0x4C,
        (t.uint8_t,),
        (t.EmberStatus, t.FixedList[t.uint8_t, 134]),
    ),
    "dutyCycleHandler": (
        0x4D,
        (),
        (
            t.uint8_t,
            t.uint8_t,
            t.EmberDutyCycleState,
            t.uint8_t,
            t.EmberPerDeviceDutyCycle,
        ),
    ),
    "getFirstBeacon": (
        0x3D,
        (),
        (t.EmberStatus, t.EmberBeaconIterator),
    ),
    "getNextBeacon": (
        0x04,
        (),
        (t.EmberStatus, t.EmberBeaconData),
    ),
    "getNumStoredBeacons": (
        0x08,
        (),
        (t.uint8_t,),
    ),
    "clearStoredBeacons": (
        0x3C,
        (),
        (),
    ),
    # 7. Binding Frames
    "clearBindingTable": (
        0x2A,
        (),
        (t.EmberStatus,),
    ),
    "setBinding": (
        0x2B,
        (t.uint8_t, t.EmberBindingTableEntry),
        (t.EmberStatus,),
    ),
    "getBinding": (
        0x2C,
        (t.uint8_t,),
        (t.EmberStatus, t.EmberBindingTableEntry),
    ),
    "deleteBinding": (
        0x2D,
        (t.uint8_t,),
        (t.EmberStatus,),
    ),
    "bindingIsActive": (
        0x2E,
        (t.uint8_t,),
        (t.Bool,),
    ),
    "getBindingRemoteNodeId": (
        0x2F,
        (t.uint8_t,),
        (t.EmberNodeId,),
    ),
    "setBindingRemoteNodeId": (
        0x30,
        (t.uint8_t, t.EmberNodeId),
        (),
    ),
    "remoteSetBindingHandler": (
        0x31,
        (),
        (t.EmberBindingTableEntry, t.uint8_t, t.EmberStatus),
    ),
    "remoteDeleteBindingHandler": (
        0x32,
        (),
        (t.uint8_t, t.EmberStatus),
    ),
    # 8. Messaging Frames
    "maximumPayloadLength": (
        0x33,
        (),
        (t.uint8_t,),
    ),
    "sendUnicast": (
        0x34,
        (
            t.EmberOutgoingMessageType,
            t.EmberNodeId,
            t.EmberApsFrame,
            t.uint8_t,
            t.LVBytes,
        ),
        (t.EmberStatus, t.uint8_t),
    ),
    "sendBroadcast": (
        0x36,
        (t.EmberNodeId, t.EmberApsFrame, t.uint8_t, t.uint8_t, t.LVBytes),
        (t.EmberStatus, t.uint8_t),
    ),
    "proxyBroadcast": (
        0x37,
        (
            t.EmberNodeId,
            t.EmberNodeId,
            t.uint8_t,
            t.EmberApsFrame,
            t.uint8_t,
            t.uint8_t,
            t.LVBytes,
        ),
        (t.EmberStatus, t.uint8_t),
    ),
    "sendMulticast": (
        0x38,
        (t.EmberApsFrame, t.uint8_t, t.uint8_t, t.uint8_t, t.LVBytes),
        (t.EmberStatus, t.uint8_t),
    ),
    "sendMulticastWithAlias": (
        0x3A,
        (
            t.EmberApsFrame,
            t.uint8_t,
            t.uint8_t,
            t.uint16_t,
            t.uint8_t,
            t.uint8_t,
            t.LVBytes,
        ),
        (t.EmberStatus, t.uint8_t),
    ),
    "sendReply": (
        0x39,
        (t.EmberNodeId, t.EmberApsFrame, t.LVBytes),
        (t.EmberStatus,),
    ),
    "messageSentHandler": (
        0x3F,
        (),
        (
            t.EmberOutgoingMessageType,
            t.uint16_t,
            t.EmberApsFrame,
            t.uint8_t,
            t.EmberStatus,
            t.LVBytes,
        ),
    ),
    "sendManyToOneRouteRequest": (
        0x41,
        (t.uint16_t, t.uint8_t),
        (t.EmberStatus,),
    ),
    "pollForData": (
        0x42,
        (t.uint16_t, t.EmberEventUnits, t.uint8_t),
        (t.EmberStatus,),
    ),
    "pollCompleteHandler": (
        0x43,
        (),
        (t.EmberStatus,),
    ),
    "pollHandler": (
        0x44,
        (),
        (t.EmberNodeId,),
    ),
    "incomingSenderEui64Handler": (
        0x62,
        (),
        (t.EUI64,),
    ),
    "incomingMessageHandler": (
        0x45,
        (),
        (
            t.EmberIncomingMessageType,
            t.EmberApsFrame,
            t.uint8_t,
            t.int8s,
            t.EmberNodeId,
            t.uint8_t,
            t.uint8_t,
            t.LVBytes,
        ),
    ),
    "incomingRouteRecordHandler": (
        0x59,
        (),
        (t.EmberNodeId, t.EUI64, t.uint8_t, t.int8s, t.LVList[t.EmberNodeId]),
    ),
    "changeSourceRouteHandler": (
        0xC4,
        (),
        (t.EmberNodeId, t.EmberNodeId, t.Bool),
    ),
    "setSourceRoute": (
        0x5A,
        (t.EmberNodeId, t.LVList[t.EmberNodeId]),
        (t.EmberStatus,),
    ),
    "incomingManyToOneRouteRequestHandler": (
        0x7D,
        (),
        (t.EmberNodeId, t.EUI64, t.uint8_t),
    ),
    "incomingRouteErrorHandler": (
        0x80,
        (),
        (t.EmberStatus, t.EmberNodeId),
    ),
    "unicastCurrentNetworkKey": (
        0x50,
        (t.EmberNodeId, t.EUI64, t.EmberNodeId),
        (t.EmberStatus,),
    ),
    "addressTableEntryIsActive": (
        0x5B,
        (t.uint8_t,),
        (t.Bool,),
    ),
    "setAddressTableRemoteEui64": (
        0x5C,
        (t.uint8_t, t.EUI64),
        (t.EmberStatus,),
    ),
    "setAddressTableRemoteNodeId": (
        0x5D,
        (t.uint8_t, t.EmberNodeId),
        (),
    ),
    "getAddressTableRemoteEui64": (
        0x5E,
        (t.uint8_t,),
        (t.EUI64,),
    ),
    "getAddressTableRemoteNodeId": (
        0x5F,
        (t.uint8_t,),
        (t.EmberNodeId,),
    ),
    "setExtendedTimeout": (
        0x7E,
        (t.EUI64, t.Bool),
        (),
    ),
    "getExtendedTimeout": (
        0x7F,
        (t.EUI64,),
        (t.Bool,),
    ),
    "replaceAddressTableEntry": (
        0x82,
        (t.uint8_t, t.EUI64, t.EmberNodeId, t.Bool),
        (t.EmberStatus, t.EUI64, t.EmberNodeId, t.Bool),
    ),
    "lookupNodeIdByEui64": (
        0x60,
        (t.EUI64,),
        (t.EmberNodeId,),
    ),
    "lookupEui64ByNodeId": (
        0x61,
        (t.EmberNodeId,),
        (t.EmberStatus, t.EUI64),
    ),
    "getMulticastTableEntry": (
        0x63,
        (t.uint8_t,),
        (t.EmberStatus, t.EmberMulticastTableEntry),
    ),
    "setMulticastTableEntry": (
        0x64,
        (t.uint8_t, t.EmberMulticastTableEntry),
        (t.EmberStatus,),
    ),
    "idConflictHandler": (
        0x7C,
        (),
        (t.EmberNodeId,),
    ),
    "writeNodeData": (
        0xFE,
        (t.Bool,),
        (t.EmberStatus,),
    ),
    "sendRawMessage": (
        0x96,
        (t.LVBytes,),
        (t.EmberStatus,),
    ),
    "macPassthroughMessageHandler": (
        0x97,
        (),
        (t.EmberMacPassthroughType, t.uint8_t, t.int8s, t.LVBytes),
    ),
    "macFilterMatchMessageHandler": (
        0x46,
        (),
        (t.uint8_t, t.EmberMacPassthroughType, t.uint8_t, t.int8s, t.LVBytes),
    ),
    "rawTransmitCompleteHandler": (
        0x98,
        (),
        (t.EmberStatus,),
    ),
    "setMacPollCcaWaitTime": (
        0xF4,
        (t.uint8_t,),
        (),
    ),
    "setBeaconClassificationParams": (
        0xEF,
        (),
        (t.EmberStatus, t.EmberBeaconClassificationParams),
    ),
    "getBeaconClassificationParams": (
        0xF3,
        (),
        (t.EmberStatus, t.EmberBeaconClassificationParams),
    ),
    # 9. Security Frames
    "setInitialSecurityState": (
        0x68,
        (t.EmberInitialSecurityState,),
        (t.EmberStatus,),
    ),
    "getCurrentSecurityState": (
        0x69,
        (),
        (t.EmberStatus, t.EmberCurrentSecurityState),
    ),
    "getKey": (
        0x6A,
        (t.EmberKeyType,),
        (t.EmberStatus, t.EmberKeyStruct),
    ),
    "switchNetworkKeyHandler": (
        0x6E,
        (),
        (t.uint8_t,),
    ),
    "getKeyTableEntry": (
        0x71,
        (t.uint8_t,),
        (t.EmberStatus, t.EmberKeyStruct),
    ),
    "setKeyTableEntry": (
        0x72,
        (t.uint8_t, t.EUI64, t.Bool, t.KeyData),
        (t.EmberStatus,),
    ),
    "findKeyTableEntry": (
        0x75,
        (t.EUI64, t.Bool),
        (t.uint8_t,),
    ),
    "addOrUpdateKeyTableEntry": (
        0x66,
        (t.EUI64, t.Bool, t.KeyData),
        (t.EmberStatus,),
    ),
    "sendTrustCenterLinkKey": (
        0x67,
        (t.EmberNodeId, t.EUI64),
        (t.EmberStatus,),
    ),
    "eraseKeyTableEntry": (
        0x76,
        (t.uint8_t,),
        (t.EmberStatus,),
    ),
    "clearKeyTable": (
        0xB1,
        (),
        (t.EmberStatus,),
    ),
    "requestLinkKey": (
        0x14,
        (t.EUI64,),
        (t.EmberStatus,),
    ),
    "updateTcLinkKey": (
        0x6C,
        (t.uint8_t,),
        (t.EmberStatus,),
    ),
    "zigbeeKeyEstablishmentHandler": (
        0x9B,
        (),
        (t.EUI64, t.EmberKeyStatus),
    ),
    "addTransientLinkKey": (
        0xAF,
        (t.EUI64, t.KeyData),
        (t.EmberStatus,),
    ),
    "clearTransientLinkKeys": (
        0x6B,
        (),
        (),
    ),
    "getTransientLinkKey": (
        0xCE,
        (t.EUI64,),
        (t.EmberStatus, t.EmberTransientKeyDataV5),
    ),
    "getTransientKeyTableEntry": (
        0x6D,
        (t.uint8_t,),
        (t.EmberStatus, t.EmberTransientKeyDataV5),
    ),
    # 10. Trust Center Frames
    "trustCenterJoinHandler": (
        0x24,
        (),
        (
            t.EmberNodeId,
            t.EUI64,
            t.EmberDeviceUpdate,
            t.EmberJoinDecision,
            t.EmberNodeId,
        ),
    ),
    "broadcastNextNetworkKey": (
        0x73,
        (t.KeyData,),
        (t.EmberStatus,),
    ),
    "broadcastNetworkKeySwitch": (
        0x74,
        (),
        (t.EmberStatus,),
    ),
    "becomeTrustCenter": (
        0x77,
        (t.KeyData,),
        (t.EmberStatus,),
    ),
    "aesMmoHash": (
        0x6F,
        (t.EmberAesMmoHashContext, t.Bool, t.LVBytes),
        (t.EmberStatus, t.EmberAesMmoHashContext),
    ),
    "removeDevice": (
        0xA8,
        (t.EmberNodeId, t.EUI64, t.EUI64),
        (t.EmberStatus,),
    ),
    "unicastNwkKeyUpdate": (
        0xA9,
        (t.EmberNodeId, t.EUI64, t.KeyData),
        (t.EmberStatus,),
    ),
    # 11. Certificate Based Key Exchange (CBKE) Frames
    "generateCbkeKeys": (
        0xA4,
        (),
        (t.EmberStatus,),
    ),
    "generateCbkeKeysHandler": (
        0x9E,
        (),
        (t.EmberStatus, t.EmberPublicKeyData),
    ),
    "calculateSmacs": (
        0x9F,
        (t.Bool, t.EmberCertificateData, t.EmberPublicKeyData),
        (t.EmberStatus,),
    ),
    "calculateSmacsHandler": (
        0xA0,
        (),
        (t.EmberStatus, t.EmberSmacData, t.EmberSmacData),
    ),
    "generateCbkeKeys283k1": (
        0xE8,
        (),
        (t.EmberStatus,),
    ),
    "generateCbkeKeysHandler283k1": (
        0xE9,
        (),
        (t.EmberStatus, t.EmberPublicKey283k1Data),
    ),
    "calculateSmacs283k1": (
        0xEA,
        (t.Bool, t.EmberCertificate283k1Data, t.EmberPublicKey283k1Data),
        (t.EmberStatus,),
    ),
    "calculateSmacsHandler283k1": (
        0xEB,
        (),
        (t.EmberStatus, t.EmberSmacData, t.EmberSmacData),
    ),
    "clearTemporaryDataMaybeStoreLinkKey": (
        0xA1,
        (t.Bool,),
        (t.EmberStatus,),
    ),
    "clearTemporaryDataMaybeStoreLinkKey283k1": (
        0xEE,
        (t.Bool,),
        (t.EmberStatus,),
    ),
    "getCertificate": (
        0xA5,
        (),
        (t.EmberStatus, t.EmberCertificateData),
    ),
    "getCertificate283k1": (
        0xEC,
        (),
        (t.EmberStatus, t.EmberCertificate283k1Data),
    ),
    "dsaSign": (
        0xA6,
        (t.LVBytes,),
        (t.EmberStatus,),
    ),  # Deprecated
    "dsaSignHandler": (
        0xA7,
        (),
        (t.EmberStatus, t.LVBytes),
    ),  # Deprecated
    "dsaVerify": (
        0xA3,
        (t.EmberMessageDigest, t.EmberCertificateData, t.EmberSignatureData),
        (t.EmberStatus,),
    ),
    "dsaVerifyHandler": (
        0x78,
        (),
        (t.EmberStatus,),
    ),
    "dsaVerify283k1": (
        0xB0,
        (t.EmberMessageDigest, t.EmberCertificate283k1Data, t.EmberSignature283k1Data),
        (t.EmberStatus,),
    ),
    "setPreinstalledCbkeData": (
        0xA2,
        (t.EmberPublicKeyData, t.EmberCertificateData, t.EmberPrivateKeyData),
        (t.EmberStatus,),
    ),
    "setPreinstalledCbkeData283k1": (
        0xED,
        (
            t.EmberPublicKey283k1Data,
            t.EmberCertificate283k1Data,
            t.EmberPrivateKey283k1Data,
        ),
        (t.EmberStatus,),
    ),
    # 12. Mfglib Frames
    "mfglibStart": (
        0x83,
        (t.Bool,),
        (t.EmberStatus,),
    ),
    "mfglibEnd": (
        0x84,
        (),
        (t.EmberStatus,),
    ),
    "mfglibStartTone": (
        0x85,
        (),
        (t.EmberStatus,),
    ),
    "mfglibStopTone": (
        0x86,
        (),
        (t.EmberStatus,),
    ),
    "mfglibStartStream": (
        0x87,
        (),
        (t.EmberStatus,),
    ),
    "mfglibStopStream": (
        0x88,
        (),
        (t.EmberStatus,),
    ),
    "mfglibSendPacket": (
        0x89,
        (t.LVBytes,),
        (t.EmberStatus,),
    ),
    "mfglibSetChannel": (
        0x8A,
        (t.uint8_t,),
        (t.EmberStatus,),
    ),
    "mfglibGetChannel": (
        0x8B,
        (),
        (t.uint8_t,),
    ),
    "mfglibSetPower": (
        0x8C,
        (t.uint16_t, t.int8s),
        (t.EmberStatus,),
    ),
    "mfglibGetPower": (
        0x8D,
        (),
        (t.int8s,),
    ),
    "mfglibRxHandler": (
        0x8E,
        (),
        (t.uint8_t, t.int8s, t.LVBytes),
    ),
    # 13. Bootloader Frames
    "launchStandaloneBootloader": (
        0x8F,
        (t.uint8_t,),
        (t.EmberStatus,),
    ),
    "sendBootloadMessage": (
        0x90,
        (t.Bool, t.EUI64, t.LVBytes),
        (t.EmberStatus,),
    ),
    "getStandaloneBootloaderVersionPlatMicroPhy": (
        0x91,
        (),
        (t.uint16_t, t.uint8_t, t.uint8_t, t.uint8_t),
    ),
    "incomingBootloadMessageHandler": (
        0x92,
        (),
        (t.EUI64, t.uint8_t, t.int8s, t.LVBytes),
    ),
    "bootloadTransmitCompleteHandler": (
        0x93,
        (),
        (t.EmberStatus, t.LVBytes),
    ),
    "aesEncrypt": (
        0x94,
        (t.FixedList[t.uint8_t, 16], t.FixedList[t.uint8_t, 16]),
        (t.FixedList[t.uint8_t, 16],),
    ),
    "overrideCurrentChannel": (
        0x95,
        (t.uint8_t,),
        (t.EmberStatus,),
    ),
    # 14. ZLL Frames
    "zllNetworkOps": (
        0xB2,
        (t.EmberZllNetwork, t.EzspZllNetworkOperation, t.int8s),
        (t.EmberStatus,),
    ),
    "zllSetInitialSecurityState": (
        0xB3,
        (t.KeyData, t.EmberZllInitialSecurityState),
        (t.EmberStatus,),
    ),
    "zllSetSecurityStateWithoutKey": (
        0xCF,
        (t.EmberZllInitialSecurityState,),
        (t.EmberStatus,),
    ),
    "zllStartScan": (
        0xB4,
        (t.Channels, t.int8s, t.EmberNodeType),
        (t.EmberStatus,),
    ),
    "zllSetRxOnWhenIdle": (
        0xB5,
        (t.uint32_t,),
        (t.EmberStatus,),
    ),
    "zllNetworkFoundHandler": (
        0xB6,
        (),
        (t.EmberZllNetwork, t.Bool, t.EmberZllDeviceInfoRecord, t.uint8_t, t.int8s),
    ),
    "zllScanCompleteHandler": (
        0xB7,
        (),
        (t.EmberStatus,),
    ),
    "zllAddressAssignmentHandler": (
        0xB8,
        (),
        (t.EmberZllAddressAssignment, t.uint8_t, t.int8s),
    ),
    "setLogicalAndRadioChannel": (
        0xB9,
        (t.uint8_t,),
        (t.EmberStatus,),
    ),
    "getLogicalChannel": (
        0xBA,
        (),
        (t.uint8_t,),
    ),
    "zllTouchLinkTargetHandler": (
        0xBB,
        (),
        (t.EmberZllNetwork,),
    ),
    "zllGetTokens": (
        0xBC,
        (),
        (t.EmberTokTypeStackZllData, t.EmberTokTypeStackZllSecurity),
    ),
    "zllSetDataToken": (
        0xBD,
        (t.EmberTokTypeStackZllData,),
        (),
    ),
    "zllSetNonZllNetwork": (
        0xBF,
        (),
        (),
    ),
    "isZllNetwork": (
        0xBE,
        (),
        (t.Bool,),
    ),
    "zllSetRadioIdleMode": (
        0xD4,
        (t.EmberRadioPowerMode,),
        (),
    ),
    "setZllNodeType": (
        0xD5,
        (t.EmberNodeType,),
        (),
    ),
    "setZllAdditionalState": (
        0xD6,
        (t.uint16_t,),
        (),
    ),
    "zllOperationInProgress": (
        0xD7,
        (),
        (t.Bool,),
    ),
    "zllRxOnWhenIdleGetActive": (
        0xD8,
        (),
        (t.Bool,),
    ),
    "getZllPrimaryChannelMask": (
        0xD9,
        (),
        (t.Channels,),
    ),
    "getZllSecondaryChannelMask": (
        0xDA,
        (),
        (t.Channels,),
    ),
    "setZllPrimaryChannelMask": (
        0xDB,
        (t.Channels,),
        (),
    ),
    "setZllSecondaryChannelMask": (
        0xDC,
        (t.Channels,),
        (),
    ),
    "zllClearTokens": (
        0x25,
        (),
        (),
    ),
    # 15 WWAH Frames
    "setParentClassificationEnabled": (
        0xE7,
        (t.Bool,),
        (),
    ),
    "getParentClassificationEnabled": (
        0xF0,
        (),
        (t.Bool,),
    ),
    "setLongUpTime": (
        0xE3,
        (t.Bool,),
        (),
    ),
    "setHubConnectivity": (
        0xE4,
        (t.Bool,),
        (),
    ),
    "isUpTimeLong": (
        0xE5,
        (),
        (t.Bool,),
    ),
    "isHubConnected": (
        0xE6,
        (),
        (t.Bool,),
    ),
    # 16 Green Power Frames
    "gpProxyTableProcessGpPairing": (
        0xC9,
        (
            t.uint32_t,
            t.EmberGpAddress,
            t.uint8_t,
            t.uint16_t,
            t.uint16_t,
            t.uint16_t,
            t.EUI64,
            t.KeyData,
        ),
        (),
    ),
    "dGpSend": (
        0xC6,
        (t.Bool, t.Bool, t.EmberGpAddress, t.uint8_t, t.LVBytes, t.uint8_t, t.uint16_t),
        (t.EmberStatus,),
    ),
    "dGpSentHandler": (
        0xC7,
        (),
        (t.EmberStatus, t.uint8_t),
    ),
    "gpepIncomingMessageHandler": (
        0x00C5,
        (),
        (
            t.EmberStatus,  # status
            t.uint8_t,  # gpd link
            t.uint8_t,  # sequence number
            t.uint8_t,  # addrType
            t.uint32_t,  # address
            t.uint32_t,  # src ID
            t.uint8_t,  # endpoint
            t.EmberGpSecurityLevel,
            t.EmberGpKeyType,
            t.Bool,  # auto commissioning
            t.Bool,  # rx capable?
            t.uint32_t,  # security frame counter
            t.uint8_t,  # gpd command id
            t.uint32_t,  # MIC
            t.uint8_t,  # proxy table index
            t.LVBytes,  # optional payload
        ),
    ),
    "gpProxyTableGetEntry": (
        0xC8,
        (t.uint8_t,),
        (t.EmberStatus, t.EmberGpProxyTableEntry),
    ),
    "gpProxyTableLookup": (
        0xC0,
        (t.EmberGpAddress,),
        (t.uint8_t,),
    ),
    "gpSinkTableGetEntry": (
        0xDD,
        (t.uint8_t,),
        (t.EmberStatus, t.EmberGpSinkTableEntry),
    ),
    "gpSinkTableLookup": (
        0xDE,
        (t.EmberGpAddress,),
        (t.uint8_t,),
    ),
    "gpSinkTableSetEntry": (
        0xDF,
        (t.uint8_t, t.EmberGpSinkTableEntry),
        (t.EmberStatus,),
    ),
    "gpSinkTableRemoveEntry": (
        0xE0,
        (t.uint8_t,),
        (),
    ),
    "gpSinkTableFindOrAllocateEntry": (
        0xE1,
        (t.EmberGpAddress,),
        (t.uint8_t,),
    ),
    "gpSinkTableClearAll": (
        0xE2,
        (),
        (),
    ),
    "gpSinkTableInit": (
        0x70,
        (),
        (),
    ),
    # 16 Secure EZSP Frames
    "setSecurityKey": (
        0xCA,
        (t.KeyData, t.SecureEzspSecurityType),
        (t.EzspStatus,),
    ),
    "setSecurityParameters": (
        0xCB,
        (t.SecureEzspSecurityLevel, t.uint128_t),
        (t.EzspStatus, t.uint128_t),
    ),
    "resetToFactoryDefaults": (
        0xCC,
        (),
        (t.EzspStatus,),
    ),
    "getSecurityKeyStatus": (
        0xCD,
        (),
        (t.EzspStatus, t.SecureEzspSecurityType),
    ),
}
