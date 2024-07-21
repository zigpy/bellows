from . import types as t

COMMANDS = {
    # 4. Configuration frames
    "version": (
        0x0000,
        (t.uint8_t,),
        (t.uint8_t, t.uint8_t, t.uint16_t),
    ),
    "getConfigurationValue": (
        0x0052,
        (t.EzspConfigId,),
        (t.EzspStatus, t.uint16_t),
    ),
    "setConfigurationValue": (
        0x0053,
        (t.EzspConfigId, t.uint16_t),
        (t.EzspStatus,),
    ),
    "addEndpoint": (
        0x0002,
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
        0x0055,
        (t.EzspPolicyId, t.uint16_t),
        (t.EzspStatus,),
    ),
    "getPolicy": (
        0x0056,
        (t.EzspPolicyId,),
        (t.EzspStatus, t.EzspDecisionId),
    ),
    "sendPanIdUpdate": (
        0x0057,
        (t.EmberPanId,),
        (t.Bool,),
    ),
    "getValue": (
        0x00AA,
        (t.EzspValueId,),
        (t.EzspStatus, t.LVBytes),
    ),
    "getExtendedValue": (
        0x0003,
        (t.EzspExtendedValueId, t.uint32_t),
        (t.EzspStatus, t.LVBytes),
    ),
    "setValue": (
        0x00AB,
        (t.EzspValueId, t.LVBytes),
        (t.EzspStatus,),
    ),
    "setGpioCurrentConfiguration": (
        0x00AC,
        (t.uint8_t, t.uint8_t, t.uint8_t),
        (t.EzspStatus,),
    ),
    "setGpioPowerUpDownConfiguration": (
        0x00AD,
        (t.uint8_t, t.uint8_t, t.uint8_t, t.uint8_t, t.uint8_t),
        (t.EzspStatus,),
    ),
    # 5. Utilities Frames
    "nop": (
        0x0005,
        (),
        (),
    ),
    "echo": (
        0x0081,
        (t.LVBytes,),
        (t.LVBytes,),
    ),
    "invalidCommand": (
        0x0058,
        (),
        (t.EzspStatus,),
    ),
    "callback": (
        0x0006,
        (),
        (),
    ),
    "noCallbacks": (
        0x0007,
        (),
        (),
    ),
    "setToken": (
        0x0009,
        (t.uint8_t, t.FixedList[t.uint8_t, 8]),
        (t.EmberStatus,),
    ),
    "getToken": (
        0x000A,
        (t.uint8_t,),
        (t.EmberStatus, t.FixedList[t.uint8_t, 8]),
    ),
    "getMfgToken": (
        0x000B,
        (t.EzspMfgTokenId,),
        (t.LVBytes,),
    ),
    "setMfgToken": (
        0x000C,
        (t.EzspMfgTokenId, t.LVBytes),
        (t.EmberStatus,),
    ),
    "stackTokenChangedHandler": (
        0x000D,
        (),
        (t.uint16_t,),
    ),
    "getRandomNumber": (
        0x0049,
        (),
        (t.EmberStatus, t.uint16_t),
    ),
    "setTimer": (
        0x000E,
        (t.uint8_t, t.uint16_t, t.EmberEventUnits, t.Bool),
        (t.EmberStatus,),
    ),
    "getTimer": (
        0x004E,
        (t.uint8_t,),
        (t.uint16_t, t.EmberEventUnits, t.Bool),
    ),
    "timerHandler": (
        0x000F,
        (),
        (t.uint8_t,),
    ),
    "debugWrite": (
        0x0012,
        (t.Bool, t.LVBytes),
        (t.EmberStatus,),
    ),
    "readAndClearCounters": (
        0x0065,
        (),
        (t.FixedList[t.uint16_t, len(t.EmberCounterType)],),
    ),
    "readCounters": (
        0x00F1,
        (),
        (t.FixedList[t.uint16_t, len(t.EmberCounterType)],),
    ),
    "counterRolloverHandler": (
        0x00F2,
        (),
        (t.EmberCounterType,),
    ),
    "delayTest": (
        0x009D,
        (t.uint16_t,),
        (),
    ),
    "getLibraryStatus": (
        0x0001,
        (t.EmberLibraryId,),
        (t.EmberLibraryStatus,),
    ),
    "getXncpInfo": (
        0x0013,
        (),
        (t.EmberStatus, t.uint16_t, t.uint16_t),
    ),
    "customFrame": (
        0x0047,
        (t.LVBytes,),
        (t.EmberStatus, t.LVBytes),
    ),
    "customFrameHandler": (
        0x0054,
        (),
        (t.LVBytes,),
    ),
    "getEui64": (
        0x0026,
        (),
        (t.EUI64,),
    ),
    "getNodeId": (
        0x0027,
        (),
        (t.EmberNodeId,),
    ),
    "getPhyInterfaceCount": (
        0x00FC,
        (),
        (t.uint8_t,),
    ),
    "getTrueRandomEntropySource": (
        0x004F,
        (),
        (t.EmberEntropySource,),
    ),
    "networkInit": (
        0x0017,
        (t.EmberNetworkInitBitmask,),
        (t.EmberStatus,),
    ),
    # 6. Networking Frames
    "setManufacturerCode": (
        0x0015,
        (t.uint16_t,),
        (),
    ),
    "setPowerDescriptor": (
        0x0016,
        (t.uint16_t,),
        (),
    ),
    "networkState": (
        0x0018,
        (),
        (t.EmberNetworkStatus,),
    ),
    "stackStatusHandler": (
        0x0019,
        (),
        (t.EmberStatus,),
    ),
    "startScan": (
        0x001A,
        (t.EzspNetworkScanType, t.uint32_t, t.uint8_t),
        (t.EmberStatus,),
    ),
    "energyScanResultHandler": (
        0x0048,
        (),
        (t.uint8_t, t.int8s),
    ),
    "networkFoundHandler": (
        0x001B,
        (),
        (t.EmberZigbeeNetwork, t.uint8_t, t.int8s),
    ),
    "scanCompleteHandler": (
        0x001C,
        (),
        (t.uint8_t, t.EmberStatus),
    ),
    "unusedPanIdFoundHandler": (
        0x00D2,
        (),
        (t.uint8_t, t.EmberStatus),
    ),
    "findUnusedPanId": (
        0x00D3,
        (t.Channels, t.uint8_t),
        (t.EmberStatus,),
    ),
    "stopScan": (
        0x001D,
        (),
        (t.EmberStatus,),
    ),
    "formNetwork": (
        0x001E,
        (t.EmberNetworkParameters,),
        (t.EmberStatus,),
    ),
    "joinNetwork": (
        0x001F,
        (t.EmberNodeType, t.EmberNetworkParameters),
        (t.EmberStatus,),
    ),
    "joinNetworkDirectly": (
        0x003B,
        (t.EmberNodeType, t.EmberBeaconData, t.int8s, t.Bool),
        (t.EmberStatus,),
    ),
    "leaveNetwork": (
        0x0020,
        (),
        (t.EmberStatus,),
    ),
    "findAndRejoinNetwork": (
        0x0021,
        (t.Bool, t.uint32_t),
        (t.EmberStatus,),
    ),
    "permitJoining": (
        0x0022,
        (t.uint8_t,),
        (t.EmberStatus,),
    ),
    "childJoinHandler": (
        0x0023,
        (),
        (t.uint8_t, t.Bool, t.EmberNodeId, t.EUI64, t.EmberNodeType),
    ),
    "energyScanRequest": (
        0x009C,
        (t.EmberNodeId, t.Channels, t.uint8_t, t.uint16_t),
        (t.EmberStatus,),
    ),
    "getNetworkParameters": (
        0x0028,
        (),
        (t.EmberStatus, t.EmberNodeType, t.EmberNetworkParameters),
    ),
    "getRadioParameters": (
        0x00FD,
        (t.uint8_t,),
        (t.EmberStatus, t.EmberNodeType, t.EmberNetworkParameters),
    ),
    "getParentChildParameters": (
        0x0029,
        (),
        (t.uint8_t, t.EUI64, t.EmberNodeId),
    ),
    "getChildData": (
        0x004A,
        (t.uint8_t,),
        (t.EmberStatus, t.EmberChildData),
    ),
    "getSourceRouteTableTotalSize": (
        0x00C3,
        (),
        (t.uint8_t,),
    ),
    "getSourceRouteTableFilledSize": (
        0x00C2,
        (),
        (t.uint8_t,),
    ),
    "getSourceRouteTableEntry": (
        0x00C1,
        (t.uint8_t,),
        (t.EmberStatus, t.EmberNodeId, t.uint8_t),
    ),
    "getNeighbor": (
        0x0079,
        (t.uint8_t,),
        (t.EmberStatus, t.EmberNeighborTableEntry),
    ),
    "getNeighborFrameCounter": (
        0x003E,
        (t.EUI64,),
        (t.EmberStatus, t.uint32_t),
    ),
    "setRoutingShortcutThreshold": (
        0x00D0,
        (t.uint8_t,),
        (t.EmberStatus,),
    ),
    "getRoutingShortcutThreshold": (
        0x00D1,
        (),
        (t.uint8_t,),
    ),
    "neighborCount": (
        0x007A,
        (),
        (t.uint8_t,),
    ),
    "getRouteTableEntry": (
        0x007B,
        (t.uint8_t,),
        (t.EmberStatus, t.EmberRouteTableEntry),
    ),
    "setRadioPower": (
        0x0099,
        (t.int8s,),
        (t.EmberStatus,),
    ),
    "setRadioChannel": (
        0x009A,
        (t.uint8_t,),
        (t.EmberStatus,),
    ),
    "setConcentrator": (
        0x0010,
        (t.Bool, t.uint16_t, t.uint16_t, t.uint16_t, t.uint8_t, t.uint8_t, t.uint8_t),
        (t.EmberStatus,),
    ),
    "setBrokenRouteErrorCode": (
        0x0011,
        (t.uint8_t,),
        (t.EmberStatus,),
    ),
    "multiPhyStart": (
        0x00F8,
        (t.uint8_t, t.uint8_t, t.uint8_t, t.int8s, t.EmberMultiPhyNwkConfig),
        (t.EmberStatus,),
    ),
    "multiPhyStop": (
        0x00F9,
        (t.uint8_t,),
        (t.EmberStatus,),
    ),
    "multiPhySetRadioPower": (
        0x00FA,
        (t.uint8_t, t.int8s),
        (t.EmberStatus,),
    ),
    "sendLinkPowerDeltaRequest": (
        0x00F7,
        (),
        (t.EmberStatus,),
    ),
    "multiPhySetRadioChannel": (
        0x00FB,
        (t.uint8_t, t.uint8_t, t.uint8_t),
        (t.EmberStatus,),
    ),
    "getDutyCycleState": (
        0x0035,
        (),
        (t.EmberStatus, t.EmberDutyCycleState),
    ),
    "setDutyCycleLimitsInStack": (
        0x0040,
        (t.EmberDutyCycleLimits,),
        (t.EmberStatus, t.EmberDutyCycleState),
    ),
    "getDutyCycleLimits": (
        0x004B,
        (),
        (t.EmberStatus, t.EmberDutyCycleLimits),
    ),
    "getCurrentDutyCycle": (
        0x004C,
        (t.uint8_t,),
        (t.EmberStatus, t.FixedList[t.uint8_t, 134]),
    ),
    "dutyCycleHandler": (
        0x004D,
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
        0x003D,
        (),
        (t.EmberStatus, t.EmberBeaconIterator),
    ),
    "getNextBeacon": (
        0x0004,
        (),
        (t.EmberStatus, t.EmberBeaconData),
    ),
    "getNumStoredBeacons": (
        0x0008,
        (),
        (t.uint8_t,),
    ),
    "clearStoredBeacons": (
        0x003C,
        (),
        (),
    ),
    "setLogicalAndRadioChannel": (
        0x00B9,
        (t.uint8_t,),
        (t.EmberStatus,),
    ),
    "getLogicalChannel": (
        0x00BA,
        (),
        (t.uint8_t,),
    ),
    # 7. Binding Frames
    "clearBindingTable": (
        0x002A,
        (),
        (t.EmberStatus,),
    ),
    "setBinding": (
        0x002B,
        (t.uint8_t, t.EmberBindingTableEntry),
        (t.EmberStatus,),
    ),
    "getBinding": (
        0x002C,
        (t.uint8_t,),
        (t.EmberStatus, t.EmberBindingTableEntry),
    ),
    "deleteBinding": (
        0x002D,
        (t.uint8_t,),
        (t.EmberStatus,),
    ),
    "bindingIsActive": (
        0x002E,
        (t.uint8_t,),
        (t.Bool,),
    ),
    "getBindingRemoteNodeId": (
        0x002F,
        (t.uint8_t,),
        (t.EmberNodeId,),
    ),
    "setBindingRemoteNodeId": (
        0x0030,
        (t.uint8_t, t.EmberNodeId),
        (),
    ),
    "remoteSetBindingHandler": (
        0x0031,
        (),
        (t.EmberBindingTableEntry, t.uint8_t, t.EmberStatus),
    ),
    "remoteDeleteBindingHandler": (
        0x0032,
        (),
        (t.uint8_t, t.EmberStatus),
    ),
    # 8. Messaging Frames
    "maximumPayloadLength": (
        0x0033,
        (),
        (t.uint8_t,),
    ),
    "sendUnicast": (
        0x0034,
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
        0x0036,
        (t.EmberNodeId, t.EmberApsFrame, t.uint8_t, t.uint8_t, t.LVBytes),
        (t.EmberStatus, t.uint8_t),
    ),
    "proxyBroadcast": (
        0x0037,
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
        0x0038,
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
        0x0039,
        (t.EmberNodeId, t.EmberApsFrame, t.LVBytes),
        (t.EmberStatus,),
    ),
    "messageSentHandler": (
        0x003F,
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
        0x0041,
        (t.uint16_t, t.uint8_t),
        (t.EmberStatus,),
    ),
    "pollForData": (
        0x0042,
        (t.uint16_t, t.EmberEventUnits, t.uint8_t),
        (t.EmberStatus,),
    ),
    "pollCompleteHandler": (
        0x0043,
        (),
        (t.EmberStatus,),
    ),
    "pollHandler": (
        0x0044,
        (),
        (t.EmberNodeId,),
    ),
    "incomingSenderEui64Handler": (
        0x0062,
        (),
        (t.EUI64,),
    ),
    "incomingMessageHandler": (
        0x0045,
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
        0x0059,
        (),
        (t.EmberNodeId, t.EUI64, t.uint8_t, t.int8s, t.LVList[t.EmberNodeId]),
    ),
    "incomingNetworkStatusHandler": (
        0x00C4,
        (),
        tuple(
            {"errorCode": t.EmberStackError, "target": t.EmberNodeId}.values(),
        ),
    ),
    "setSourceRoute": (
        0x00AE,
        (t.EmberNodeId, t.LVList[t.EmberNodeId]),
        (t.EmberStatus,),
    ),
    "setSourceRouteDiscoveryMode": (
        0x005A,
        (t.uint8_t,),
        (t.uint32_t,),
    ),
    "incomingManyToOneRouteRequestHandler": (
        0x007D,
        (),
        (t.EmberNodeId, t.EUI64, t.uint8_t),
    ),
    "incomingRouteErrorHandler": (
        0x0080,
        (),
        (t.EmberStatus, t.EmberNodeId),
    ),
    "unicastCurrentNetworkKey": (
        0x0050,
        (t.EmberNodeId, t.EUI64, t.EmberNodeId),
        (t.EmberStatus,),
    ),
    "addressTableEntryIsActive": (
        0x005B,
        (t.uint8_t,),
        (t.Bool,),
    ),
    "setAddressTableRemoteEui64": (
        0x005C,
        (t.uint8_t, t.EUI64),
        (t.EmberStatus,),
    ),
    "setAddressTableRemoteNodeId": (
        0x005D,
        (t.uint8_t, t.EmberNodeId),
        (),
    ),
    "getAddressTableRemoteEui64": (
        0x005E,
        (t.uint8_t,),
        (t.EUI64,),
    ),
    "getAddressTableRemoteNodeId": (
        0x005F,
        (t.uint8_t,),
        (t.EmberNodeId,),
    ),
    "setExtendedTimeout": (
        0x007E,
        (t.EUI64, t.Bool),
        (),
    ),
    "getExtendedTimeout": (
        0x007F,
        (t.EUI64,),
        (t.Bool,),
    ),
    "replaceAddressTableEntry": (
        0x0082,
        (t.uint8_t, t.EUI64, t.EmberNodeId, t.Bool),
        (t.EmberStatus, t.EUI64, t.EmberNodeId, t.Bool),
    ),
    "lookupNodeIdByEui64": (
        0x0060,
        (t.EUI64,),
        (t.EmberNodeId,),
    ),
    "lookupEui64ByNodeId": (
        0x0061,
        (t.EmberNodeId,),
        (t.EmberStatus, t.EUI64),
    ),
    "getMulticastTableEntry": (
        0x0063,
        (t.uint8_t,),
        (t.EmberStatus, t.EmberMulticastTableEntry),
    ),
    "setMulticastTableEntry": (
        0x0064,
        (t.uint8_t, t.EmberMulticastTableEntry),
        (t.EmberStatus,),
    ),
    "idConflictHandler": (
        0x007C,
        (),
        (t.EmberNodeId,),
    ),
    "writeNodeData": (
        0x00FE,
        (t.Bool,),
        (t.EmberStatus,),
    ),
    "sendRawMessage": (
        0x0096,
        (t.LVBytes,),
        (t.EmberStatus,),
    ),
    "sendRawMessageExtended": (
        0x0051,
        (t.LVBytes, t.uint8_t, t.Bool),
        (t.EmberStatus,),
    ),
    "macPassthroughMessageHandler": (
        0x0097,
        (),
        (t.EmberMacPassthroughType, t.uint8_t, t.int8s, t.LVBytes),
    ),
    "macFilterMatchMessageHandler": (
        0x0046,
        (),
        (t.uint8_t, t.EmberMacPassthroughType, t.uint8_t, t.int8s, t.LVBytes),
    ),
    "rawTransmitCompleteHandler": (
        0x0098,
        (),
        (t.EmberStatus,),
    ),
    "setMacPollFailureWaitTime": (
        0x00F4,
        (t.uint8_t,),
        (),
    ),
    "setBeaconClassificationParams": (
        0x00EF,
        (),
        (t.EmberStatus, t.EmberBeaconClassificationParams),
    ),
    "getBeaconClassificationParams": (
        0x00F3,
        (),
        (t.EmberStatus, t.EmberBeaconClassificationParams),
    ),
    # 9. Security Frames
    "setInitialSecurityState": (
        0x0068,
        (t.EmberInitialSecurityState,),
        (t.EmberStatus,),
    ),
    "getCurrentSecurityState": (
        0x0069,
        (),
        (t.EmberStatus, t.EmberCurrentSecurityState),
    ),
    "getKey": (
        0x006A,
        (t.EmberKeyType,),
        (t.EmberStatus, t.EmberKeyStruct),
    ),
    "switchNetworkKeyHandler": (
        0x006E,
        (),
        (t.uint8_t,),
    ),
    "getKeyTableEntry": (
        0x0071,
        (t.uint8_t,),
        (t.EmberStatus, t.EmberKeyStruct),
    ),
    "setKeyTableEntry": (
        0x0072,
        (t.uint8_t, t.EUI64, t.Bool, t.KeyData),
        (t.EmberStatus,),
    ),
    "findKeyTableEntry": (
        0x0075,
        (t.EUI64, t.Bool),
        (t.uint8_t,),
    ),
    "addOrUpdateKeyTableEntry": (
        0x0066,
        (t.EUI64, t.Bool, t.KeyData),
        (t.EmberStatus,),
    ),
    "sendTrustCenterLinkKey": (
        0x0067,
        (t.EmberNodeId, t.EUI64),
        (t.EmberStatus,),
    ),
    "eraseKeyTableEntry": (
        0x0076,
        (t.uint8_t,),
        (t.EmberStatus,),
    ),
    "clearKeyTable": (
        0x00B1,
        (),
        (t.EmberStatus,),
    ),
    "requestLinkKey": (
        0x0014,
        (t.EUI64,),
        (t.EmberStatus,),
    ),
    "updateTcLinkKey": (
        0x006C,
        (t.uint8_t,),
        (t.EmberStatus,),
    ),
    "zigbeeKeyEstablishmentHandler": (
        0x009B,
        (),
        (t.EUI64, t.EmberKeyStatus),
    ),
    "addTransientLinkKey": (
        0x00AF,
        (t.EUI64, t.KeyData),
        (t.EmberStatus,),
    ),
    "clearTransientLinkKeys": (
        0x006B,
        (),
        (),
    ),
    "getTransientLinkKey": (
        0x00CE,
        (t.EUI64,),
        (t.EmberStatus, t.EmberTransientKeyDataV8),
    ),
    "getTransientKeyTableEntry": (
        0x006D,
        (t.uint8_t,),
        (t.EmberStatus, t.EmberTransientKeyDataV8),
    ),
    # 10. Trust Center Frames
    "trustCenterJoinHandler": (
        0x0024,
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
        0x0073,
        (t.KeyData,),
        (t.EmberStatus,),
    ),
    "broadcastNetworkKeySwitch": (
        0x0074,
        (),
        (t.EmberStatus,),
    ),
    "becomeTrustCenter": (
        0x0077,
        (t.KeyData,),
        (t.EmberStatus,),
    ),
    "aesMmoHash": (
        0x006F,
        (t.EmberAesMmoHashContext, t.Bool, t.LVBytes),
        (t.EmberStatus, t.EmberAesMmoHashContext),
    ),
    "removeDevice": (
        0x00A8,
        (t.EmberNodeId, t.EUI64, t.EUI64),
        (t.EmberStatus,),
    ),
    "unicastNwkKeyUpdate": (
        0x00A9,
        (t.EmberNodeId, t.EUI64, t.KeyData),
        (t.EmberStatus,),
    ),
    # 11. Certificate Based Key Exchange (CBKE) Frames
    "generateCbkeKeys": (
        0x00A4,
        (),
        (t.EmberStatus,),
    ),
    "generateCbkeKeysHandler": (
        0x009E,
        (),
        (t.EmberStatus, t.EmberPublicKeyData),
    ),
    "calculateSmacs": (
        0x009F,
        (t.Bool, t.EmberCertificateData, t.EmberPublicKeyData),
        (t.EmberStatus,),
    ),
    "calculateSmacsHandler": (
        0x00A0,
        (),
        (t.EmberStatus, t.EmberSmacData, t.EmberSmacData),
    ),
    "generateCbkeKeys283k1": (
        0x00E8,
        (),
        (t.EmberStatus,),
    ),
    "generateCbkeKeysHandler283k1": (
        0x00E9,
        (),
        (t.EmberStatus, t.EmberPublicKey283k1Data),
    ),
    "calculateSmacs283k1": (
        0x00EA,
        (t.Bool, t.EmberCertificate283k1Data, t.EmberPublicKey283k1Data),
        (t.EmberStatus,),
    ),
    "calculateSmacsHandler283k1": (
        0x00EB,
        (),
        (t.EmberStatus, t.EmberSmacData, t.EmberSmacData),
    ),
    "clearTemporaryDataMaybeStoreLinkKey": (
        0x00A1,
        (t.Bool,),
        (t.EmberStatus,),
    ),
    "clearTemporaryDataMaybeStoreLinkKey283k1": (
        0x00EE,
        (t.Bool,),
        (t.EmberStatus,),
    ),
    "getCertificate": (
        0x00A5,
        (),
        (t.EmberStatus, t.EmberCertificateData),
    ),
    "getCertificate283k1": (
        0x00EC,
        (),
        (t.EmberStatus, t.EmberCertificate283k1Data),
    ),
    "dsaSign": (
        0x00A6,
        (t.LVBytes,),
        (t.EmberStatus,),
    ),  # Deprecated
    "dsaSignHandler": (
        0x00A7,
        (),
        (t.EmberStatus, t.LVBytes),
    ),  # Deprecated
    "dsaVerify": (
        0x00A3,
        (t.EmberMessageDigest, t.EmberCertificateData, t.EmberSignatureData),
        (t.EmberStatus,),
    ),
    "dsaVerifyHandler": (
        0x0078,
        (),
        (t.EmberStatus,),
    ),
    "dsaVerify283k1": (
        0x00B0,
        (t.EmberMessageDigest, t.EmberCertificate283k1Data, t.EmberSignature283k1Data),
        (t.EmberStatus,),
    ),
    "setPreinstalledCbkeData": (
        0x00A2,
        (t.EmberPublicKeyData, t.EmberCertificateData, t.EmberPrivateKeyData),
        (t.EmberStatus,),
    ),
    "setPreinstalledCbkeData283k1": (
        0x00ED,
        (
            t.EmberPublicKey283k1Data,
            t.EmberCertificate283k1Data,
            t.EmberPrivateKey283k1Data,
        ),
        (t.EmberStatus,),
    ),
    # 12. Mfglib Frames
    "mfglibStart": (
        0x0083,
        (t.Bool,),
        (t.EmberStatus,),
    ),
    "mfglibEnd": (
        0x0084,
        (),
        (t.EmberStatus,),
    ),
    "mfglibStartTone": (
        0x0085,
        (),
        (t.EmberStatus,),
    ),
    "mfglibStopTone": (
        0x0086,
        (),
        (t.EmberStatus,),
    ),
    "mfglibStartStream": (
        0x0087,
        (),
        (t.EmberStatus,),
    ),
    "mfglibStopStream": (
        0x0088,
        (),
        (t.EmberStatus,),
    ),
    "mfglibSendPacket": (
        0x0089,
        (t.LVBytes,),
        (t.EmberStatus,),
    ),
    "mfglibSetChannel": (
        0x008A,
        (t.uint8_t,),
        (t.EmberStatus,),
    ),
    "mfglibGetChannel": (
        0x008B,
        (),
        (t.uint8_t,),
    ),
    "mfglibSetPower": (
        0x008C,
        (t.uint16_t, t.int8s),
        (t.EmberStatus,),
    ),
    "mfglibGetPower": (
        0x008D,
        (),
        (t.int8s,),
    ),
    "mfglibRxHandler": (
        0x008E,
        (),
        (t.uint8_t, t.int8s, t.LVBytes),
    ),
    # 13. Bootloader Frames
    "launchStandaloneBootloader": (
        0x008F,
        (t.uint8_t,),
        (t.EmberStatus,),
    ),
    "sendBootloadMessage": (
        0x0090,
        (t.Bool, t.EUI64, t.LVBytes),
        (t.EmberStatus,),
    ),
    "getStandaloneBootloaderVersionPlatMicroPhy": (
        0x0091,
        (),
        (t.uint16_t, t.uint8_t, t.uint8_t, t.uint8_t),
    ),
    "incomingBootloadMessageHandler": (
        0x0092,
        (),
        (t.EUI64, t.uint8_t, t.int8s, t.LVBytes),
    ),
    "bootloadTransmitCompleteHandler": (
        0x0093,
        (),
        (t.EmberStatus, t.LVBytes),
    ),
    "aesEncrypt": (
        0x0094,
        (t.FixedList[t.uint8_t, 16], t.FixedList[t.uint8_t, 16]),
        (t.FixedList[t.uint8_t, 16],),
    ),
    "overrideCurrentChannel": (
        0x0095,
        (t.uint8_t,),
        (t.EmberStatus,),
    ),
    # 14. ZLL Frames
    "zllNetworkOps": (
        0x00B2,
        (t.EmberZllNetwork, t.EzspZllNetworkOperation, t.int8s),
        (t.EmberStatus,),
    ),
    "zllSetInitialSecurityState": (
        0x00B3,
        (t.KeyData, t.EmberZllInitialSecurityState),
        (t.EmberStatus,),
    ),
    "zllSetSecurityStateWithoutKey": (
        0x00CF,
        (t.EmberZllInitialSecurityState,),
        (t.EmberStatus,),
    ),
    "zllStartScan": (
        0x00B4,
        (t.Channels, t.int8s, t.EmberNodeType),
        (t.EmberStatus,),
    ),
    "zllSetRxOnWhenIdle": (
        0x00B5,
        (t.uint32_t,),
        (t.EmberStatus,),
    ),
    "zllNetworkFoundHandler": (
        0x00B6,
        (),
        (t.EmberZllNetwork, t.Bool, t.EmberZllDeviceInfoRecord, t.uint8_t, t.int8s),
    ),
    "zllScanCompleteHandler": (
        0x00B7,
        (),
        (t.EmberStatus,),
    ),
    "zllAddressAssignmentHandler": (
        0x00B8,
        (),
        (t.EmberZllAddressAssignment, t.uint8_t, t.int8s),
    ),
    "zllTouchLinkTargetHandler": (
        0x00BB,
        (),
        (t.EmberZllNetwork,),
    ),
    "zllGetTokens": (
        0x00BC,
        (),
        (t.EmberTokTypeStackZllData, t.EmberTokTypeStackZllSecurity),
    ),
    "zllSetDataToken": (
        0x00BD,
        (t.EmberTokTypeStackZllData,),
        (),
    ),
    "zllSetNonZllNetwork": (
        0x00BF,
        (),
        (),
    ),
    "isZllNetwork": (
        0x00BE,
        (),
        (t.Bool,),
    ),
    "zllSetRadioIdleMode": (
        0x00D4,
        (t.EmberRadioPowerMode,),
        (),
    ),
    "setZllNodeType": (
        0x00D5,
        (t.EmberNodeType,),
        (),
    ),
    "setZllAdditionalState": (
        0x00D6,
        (t.uint16_t,),
        (),
    ),
    "zllOperationInProgress": (
        0x00D7,
        (),
        (t.Bool,),
    ),
    "zllRxOnWhenIdleGetActive": (
        0x00D8,
        (),
        (t.Bool,),
    ),
    "getZllPrimaryChannelMask": (
        0x00D9,
        (),
        (t.Channels,),
    ),
    "getZllSecondaryChannelMask": (
        0x00DA,
        (),
        (t.Channels,),
    ),
    "setZllPrimaryChannelMask": (
        0x00DB,
        (t.Channels,),
        (),
    ),
    "setZllSecondaryChannelMask": (
        0x00DC,
        (t.Channels,),
        (),
    ),
    "zllClearTokens": (
        0x0025,
        (),
        (),
    ),
    # 15 WWAH Frames
    "setParentClassificationEnabled": (
        0x00E7,
        (t.Bool,),
        (),
    ),
    "getParentClassificationEnabled": (
        0x00F0,
        (),
        (t.Bool,),
    ),
    "setLongUpTime": (
        0x00E3,
        (t.Bool,),
        (),
    ),
    "setHubConnectivity": (
        0x00E4,
        (t.Bool,),
        (),
    ),
    "isUpTimeLong": (
        0x00E5,
        (),
        (t.Bool,),
    ),
    "isHubConnected": (
        0x00E6,
        (),
        (t.Bool,),
    ),
    # 16 Green Power Frames
    "gpProxyTableProcessGpPairing": (
        0x00C9,
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
        0x00C6,
        (t.Bool, t.Bool, t.EmberGpAddress, t.uint8_t, t.LVBytes, t.uint8_t, t.uint16_t),
        (t.EmberStatus,),
    ),
    "dGpSentHandler": (
        0x00C7,
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
        0x00C8,
        (t.uint8_t,),
        (t.EmberStatus, t.EmberGpProxyTableEntry),
    ),
    "gpProxyTableLookup": (
        0x00C0,
        (t.EmberGpAddress,),
        (t.uint8_t,),
    ),
    "gpSinkTableGetEntry": (
        0x00DD,
        (t.uint8_t,),
        (t.EmberStatus, t.EmberGpSinkTableEntry),
    ),
    "gpSinkTableLookup": (
        0x00DE,
        (t.EmberGpAddress,),
        (t.uint8_t,),
    ),
    "gpSinkTableSetEntry": (
        0x00DF,
        (t.uint8_t, t.EmberGpSinkTableEntry),
        (t.EmberStatus,),
    ),
    "gpSinkTableRemoveEntry": (
        0x00E0,
        (t.uint8_t,),
        (),
    ),
    "gpSinkTableFindOrAllocateEntry": (
        0x00E1,
        (t.EmberGpAddress,),
        (t.uint8_t,),
    ),
    "gpSinkTableClearAll": (
        0x00E2,
        (),
        (),
    ),
    "gpSinkTableInit": (
        0x0070,
        (),
        (),
    ),
    # 16 Secure EZSP Frames
    "setSecurityKey": (
        0x00CA,
        (t.KeyData, t.SecureEzspSecurityType),
        (t.EzspStatus,),
    ),
    "setSecurityParameters": (
        0x00CB,
        (t.SecureEzspSecurityLevel, t.uint128_t),
        (t.EzspStatus, t.uint128_t),
    ),
    "resetToFactoryDefaults": (
        0x00CC,
        (),
        (t.EzspStatus,),
    ),
    "getSecurityKeyStatus": (
        0x00CD,
        (),
        (t.EzspStatus, t.SecureEzspSecurityType),
    ),
}
