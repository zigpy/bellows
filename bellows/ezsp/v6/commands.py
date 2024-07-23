from bellows.ezsp.v5.commands import COMMANDS as COMMANDS_v5
import bellows.types as t

COMMANDS = {
    **COMMANDS_v5,
    "getPhyInterfaceCount": (
        0xFC,
        {},
        {
            "interfaceCount": t.uint8_t,
        },
    ),
    "unusedPanIdFoundHandler": (
        0xD2,
        {},
        {
            "panId": t.uint16_t,
            "channel": t.uint8_t,
        },
    ),
    "findUnusedPanId": (
        0xD3,
        {
            "channelMask": t.Channels,
            "duration": t.uint8_t,
        },
        {
            "status": t.EmberStatus,
        },
    ),
    "getRadioParameters": (
        0xFD,
        {
            "phyIndex": t.uint8_t,
        },
        {
            "status": t.EmberStatus,
            "parameters": t.EmberMultiPhyRadioParameters,
        },
    ),
    "getSourceRouteTableTotalSize": (
        0xC3,
        {},
        {
            "sourceRouteTableTotalSize": t.uint8_t,
        },
    ),
    "getSourceRouteTableFilledSize": (
        0xC2,
        {},
        {
            "sourceRouteTableFilledSize": t.uint8_t,
        },
    ),
    "getSourceRouteTableEntry": (
        0xC1,
        {
            "index": t.uint8_t,
        },
        {
            "status": t.EmberStatus,
            "destination": t.EmberNodeId,
            "closerIndex": t.uint8_t,
        },
    ),
    "setRoutingShortcutThreshold": (
        0xD0,
        {
            "index": t.uint8_t,
        },
        {
            "status": t.EmberStatus,
        },
    ),
    "getRoutingShortcutThreshold": (
        0xD1,
        {},
        {
            "routingShortcutThresh": t.uint8_t,
        },
    ),
    "setBrokenRouteErrorCode": (
        0x11,
        {
            "errorCode": t.uint8_t,
        },
        {
            "status": t.EmberStatus,
        },
    ),
    "multiPhyStart": (
        0xF8,
        {
            "phyIndex": t.uint8_t,
            "page": t.uint8_t,
            "channel": t.uint8_t,
            "power": t.int8s,
            "bitmask": t.EmberMultiPhyNwkConfig,
        },
        {
            "status": t.EmberStatus,
        },
    ),
    "multiPhyStop": (
        0xF9,
        {
            "phyIndex": t.uint8_t,
        },
        {
            "status": t.EmberStatus,
        },
    ),
    "multiPhySetRadioPower": (
        0xFA,
        {
            "phyIndex": t.uint8_t,
            "power": t.int8s,
        },
        {
            "status": t.EmberStatus,
        },
    ),
    "sendLinkPowerDeltaRequest": (
        0xF7,
        {},
        {
            "status": t.EmberStatus,
        },
    ),
    "multiPhySetRadioChannel": (
        0xFB,
        {
            "phyIndex": t.uint8_t,
            "page": t.uint8_t,
            "channel": t.uint8_t,
        },
        {
            "status": t.EmberStatus,
        },
    ),
    "getDutyCycleState": (
        0x35,
        {},
        {
            "status": t.EmberStatus,
            "returnedState": t.EmberDutyCycleState,
        },
    ),
    "setDutyCycleLimitsInStack": (
        0x40,
        {
            "limits": t.EmberDutyCycleLimits,
        },
        {
            "status": t.EmberStatus,
        },
    ),
    "getDutyCycleLimits": (
        0x4B,
        {},
        {
            "status": t.EmberStatus,
            "limits": t.EmberDutyCycleLimits,
        },
    ),
    "getCurrentDutyCycle": (
        0x4C,
        {
            "maxDevices": t.uint8_t,
        },
        {
            "status": t.EmberStatus,
            "arrayOfDeviceDutyCycles": t.FixedList[t.uint8_t, 134],
        },
    ),
    "dutyCycleHandler": (
        0x4D,
        {},
        {
            "channelPage": t.uint8_t,
            "channel": t.uint8_t,
            "state": t.EmberDutyCycleState,
            "arrayOfDeviceDutyCycles": t.LVList[t.EmberPerDeviceDutyCycle],
        },
    ),
    "sendMulticastWithAlias": (
        0x3A,
        {
            "hops": t.EmberApsFrame,
            "nonmemberRadius": t.uint8_t,
            "alias": t.uint8_t,
            "nwkSequence": t.uint16_t,
            "messageTag": t.uint8_t,
            "messageLength": t.uint8_t,
            "messageContents": t.LVBytes,
        },
        {
            "status": t.EmberStatus,
            "sequence": t.uint8_t,
        },
    ),
    "writeNodeData": (
        0xFE,
        {
            "erase": t.Bool,
        },
        {
            "status": t.EmberStatus,
        },
    ),
    "sendTrustCenterLinkKey": (
        0x67,
        {
            "destinationNodeId": t.EmberNodeId,
            "destinationEui64": t.EUI64,
        },
        {
            "status": t.EmberStatus,
        },
    ),
    "zllSetSecurityStateWithoutKey": (
        0xCF,
        {
            "securityState": t.EmberZllInitialSecurityState,
        },
        {
            "status": t.EmberStatus,
        },
    ),
    "zllSetRadioIdleMode": (
        0xD4,
        {
            "mode": t.EmberRadioPowerMode,
        },
        {},
    ),
    "setZllNodeType": (
        0xD5,
        {
            "nodeType": t.EmberNodeType,
        },
        {},
    ),
    "setZllAdditionalState": (
        0xD6,
        {
            "state": t.uint16_t,
        },
        {},
    ),
    "zllOperationInProgress": (
        0xD7,
        {},
        {
            "zllOperationInProgress": t.Bool,
        },
    ),
    "zllRxOnWhenIdleGetActive": (
        0xD8,
        {},
        {
            "zllRxOnWhenIdleGetActive": t.Bool,
        },
    ),
    "getZllPrimaryChannelMask": (
        0xD9,
        {},
        {
            "zllPrimaryChannelMask": t.Channels,
        },
    ),
    "getZllSecondaryChannelMask": (
        0xDA,
        {},
        {
            "zllSecondaryChannelMask": t.Channels,
        },
    ),
    "setZllPrimaryChannelMask": (
        0xDB,
        {
            "zllPrimaryChannelMask": t.Channels,
        },
        {},
    ),
    "setZllSecondaryChannelMask": (
        0xDC,
        {
            "zllSecondaryChannelMask": t.Channels,
        },
        {},
    ),
    # TODO: are these green power frames in the correct protocol version?
    "gpProxyTableGetEntry": (
        0xC8,
        {
            "proxyIndex": t.uint8_t,
        },
        {
            "status": t.EmberStatus,
            "entry": t.EmberGpProxyTableEntry,
        },
    ),
    "gpProxyTableLookup": (
        0xC0,
        {
            "addr": t.EmberGpAddress,
        },
        {
            "index": t.uint8_t,
        },
    ),
    "gpSinkTableGetEntry": (
        0xDD,
        {
            "index": t.uint8_t,
        },
        {
            "status": t.EmberStatus,
            "entry": t.EmberGpSinkTableEntry,
        },
    ),
    "gpSinkTableLookup": (
        0xDE,
        {
            "addr": t.EmberGpAddress,
        },
        {
            "index": t.uint8_t,
        },
    ),
    "gpSinkTableSetEntry": (
        0xDF,
        {
            "sinkIndex": t.uint8_t,
            "entry": t.EmberGpSinkTableEntry,
        },
        {
            "status": t.EmberStatus,
        },
    ),
    "gpSinkTableRemoveEntry": (
        0xE0,
        {
            "sinkIndex": t.uint8_t,
        },
        {},
    ),
    "gpSinkTableFindOrAllocateEntry": (
        0xE1,
        {
            "addr": t.EmberGpAddress,
        },
        {
            "index": t.uint8_t,
        },
    ),
    "gpClearSinkTable": (
        0xE2,
        {},
        {},
    ),
    # Changed commands
    "zllSetRxOnWhenIdle": (
        0xB5,
        {
            "durationMs": t.uint32_t,
        },
        {
            "status": t.EmberStatus,
        },
    ),
    "networkInit": (
        0x17,
        {
            "networkInitBitmask": t.EmberNetworkInitBitmask,  # XXX: We deviate here, since the struct has a single member
        },
        {
            "status": t.EmberStatus,
        },
    ),
}


del COMMANDS["rf4ceSetPowerSavingParameters"]
del COMMANDS["rf4ceMessageSentHandler"]
del COMMANDS["rf4ceUnpair"]
del COMMANDS["rf4ceGetNetworkParameters"]
del COMMANDS["rf4ceDiscovery"]
del COMMANDS["rf4ceDiscoveryCompleteHandler"]
del COMMANDS["networkInitExtended"]
del COMMANDS["rf4ceEnableAutoDiscoveryResponse"]
del COMMANDS["rf4ceUnpairHandler"]
del COMMANDS["rf4ceGetPairingTableEntry"]
del COMMANDS["rf4ceUnpairCompleteHandler"]
del COMMANDS["rf4ceIncomingMessageHandler"]
del COMMANDS["rf4cePair"]
del COMMANDS["rf4ceSend"]
del COMMANDS["rf4cePairCompleteHandler"]
del COMMANDS["rf4cePairRequestHandler"]
del COMMANDS["rf4ceSetFrequencyAgilityParameters"]
del COMMANDS["rf4ceStop"]
del COMMANDS["rf4ceSetPairingTableEntry"]
del COMMANDS["setChannelMap"]
del COMMANDS["rf4ceDeletePairingTableEntry"]
del COMMANDS["rf4ceKeyUpdate"]
del COMMANDS["rf4ceGetApplicationInfo"]
del COMMANDS["rf4ceAutoDiscoveryResponseCompleteHandler"]
del COMMANDS["rf4ceDiscoveryRequestHandler"]
del COMMANDS["rf4ceDiscoveryResponseHandler"]
del COMMANDS["rf4ceStart"]
del COMMANDS["rf4ceSetApplicationInfo"]
del COMMANDS["rf4ceGetMaxPayload"]
