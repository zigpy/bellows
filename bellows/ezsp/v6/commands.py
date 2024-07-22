from bellows.ezsp.v5.commands import COMMANDS as COMMANDS_v5
import bellows.types as t

COMMANDS = {
    **COMMANDS_v5,
    "getPhyInterfaceCount": (
        0xFC,
        tuple({}.values()),
        tuple(
            {
                "interfaceCount": t.uint8_t,
            }.values()
        ),
    ),
    "unusedPanIdFoundHandler": (
        0xD2,
        tuple({}.values()),
        tuple(
            {
                "panId": t.uint16_t,
                "channel": t.uint8_t,
            }.values()
        ),
    ),
    "findUnusedPanId": (
        0xD3,
        tuple(
            {
                "channelMask": t.Channels,
                "duration": t.uint8_t,
            }.values()
        ),
        tuple(
            {
                "status": t.EmberStatus,
            }.values()
        ),
    ),
    "getRadioParameters": (
        0xFD,
        tuple(
            {
                "phyIndex": t.uint8_t,
            }.values()
        ),
        tuple(
            {
                "status": t.EmberStatus,
                "parameters": t.EmberMultiPhyRadioParameters,
            }.values()
        ),
    ),
    "getSourceRouteTableTotalSize": (
        0xC3,
        tuple({}.values()),
        tuple(
            {
                "sourceRouteTableTotalSize": t.uint8_t,
            }.values()
        ),
    ),
    "getSourceRouteTableFilledSize": (
        0xC2,
        tuple({}.values()),
        tuple(
            {
                "sourceRouteTableFilledSize": t.uint8_t,
            }.values()
        ),
    ),
    "getSourceRouteTableEntry": (
        0xC1,
        tuple(
            {
                "index": t.uint8_t,
            }.values()
        ),
        tuple(
            {
                "status": t.EmberStatus,
                "destination": t.EmberNodeId,
                "closerIndex": t.uint8_t,
            }.values()
        ),
    ),
    "setRoutingShortcutThreshold": (
        0xD0,
        tuple(
            {
                "index": t.uint8_t,
            }.values()
        ),
        tuple(
            {
                "status": t.EmberStatus,
            }.values()
        ),
    ),
    "getRoutingShortcutThreshold": (
        0xD1,
        tuple({}.values()),
        tuple(
            {
                "routingShortcutThresh": t.uint8_t,
            }.values()
        ),
    ),
    "setBrokenRouteErrorCode": (
        0x11,
        tuple(
            {
                "errorCode": t.uint8_t,
            }.values()
        ),
        tuple(
            {
                "status": t.EmberStatus,
            }.values()
        ),
    ),
    "multiPhyStart": (
        0xF8,
        tuple(
            {
                "phyIndex": t.uint8_t,
                "page": t.uint8_t,
                "channel": t.uint8_t,
                "power": t.int8s,
                "bitmask": t.EmberMultiPhyNwkConfig,
            }.values()
        ),
        tuple(
            {
                "status": t.EmberStatus,
            }.values()
        ),
    ),
    "multiPhyStop": (
        0xF9,
        tuple(
            {
                "phyIndex": t.uint8_t,
            }.values()
        ),
        tuple(
            {
                "status": t.EmberStatus,
            }.values()
        ),
    ),
    "multiPhySetRadioPower": (
        0xFA,
        tuple(
            {
                "phyIndex": t.uint8_t,
                "power": t.int8s,
            }.values()
        ),
        tuple(
            {
                "status": t.EmberStatus,
            }.values()
        ),
    ),
    "sendLinkPowerDeltaRequest": (
        0xF7,
        tuple({}.values()),
        tuple(
            {
                "status": t.EmberStatus,
            }.values()
        ),
    ),
    "multiPhySetRadioChannel": (
        0xFB,
        tuple(
            {
                "phyIndex": t.uint8_t,
                "page": t.uint8_t,
                "channel": t.uint8_t,
            }.values()
        ),
        tuple(
            {
                "status": t.EmberStatus,
            }.values()
        ),
    ),
    "getDutyCycleState": (
        0x35,
        tuple({}.values()),
        tuple(
            {
                "status": t.EmberStatus,
                "returnedState": t.EmberDutyCycleState,
            }.values()
        ),
    ),
    "setDutyCycleLimitsInStack": (
        0x40,
        tuple(
            {
                "limits": t.EmberDutyCycleLimits,
            }.values()
        ),
        tuple(
            {
                "status": t.EmberStatus,
            }.values()
        ),
    ),
    "getDutyCycleLimits": (
        0x4B,
        tuple({}.values()),
        tuple(
            {
                "status": t.EmberStatus,
                "limits": t.EmberDutyCycleLimits,
            }.values()
        ),
    ),
    "getCurrentDutyCycle": (
        0x4C,
        tuple(
            {
                "maxDevices": t.uint8_t,
            }.values()
        ),
        tuple(
            {
                "status": t.EmberStatus,
                "arrayOfDeviceDutyCycles": t.FixedList[t.uint8_t, 134],
            }.values()
        ),
    ),
    "dutyCycleHandler": (
        0x4D,
        tuple({}.values()),
        tuple(
            {
                "channelPage": t.uint8_t,
                "channel": t.uint8_t,
                "state": t.EmberDutyCycleState,
                "arrayOfDeviceDutyCycles": t.LVList[t.EmberPerDeviceDutyCycle],
            }.values()
        ),
    ),
    "sendMulticastWithAlias": (
        0x3A,
        tuple(
            {
                "hops": t.EmberApsFrame,
                "nonmemberRadius": t.uint8_t,
                "alias": t.uint8_t,
                "nwkSequence": t.uint16_t,
                "messageTag": t.uint8_t,
                "messageLength": t.uint8_t,
                "messageContents": t.LVBytes,
            }.values()
        ),
        tuple(
            {
                "status": t.EmberStatus,
                "sequence": t.uint8_t,
            }.values()
        ),
    ),
    "writeNodeData": (
        0xFE,
        tuple(
            {
                "erase": t.Bool,
            }.values()
        ),
        tuple(
            {
                "status": t.EmberStatus,
            }.values()
        ),
    ),
    "sendTrustCenterLinkKey": (
        0x67,
        tuple(
            {
                "destinationNodeId": t.EmberNodeId,
                "destinationEui64": t.EUI64,
            }.values()
        ),
        tuple(
            {
                "status": t.EmberStatus,
            }.values()
        ),
    ),
    "zllSetSecurityStateWithoutKey": (
        0xCF,
        tuple(
            {
                "securityState": t.EmberZllInitialSecurityState,
            }.values()
        ),
        tuple(
            {
                "status": t.EmberStatus,
            }.values()
        ),
    ),
    "zllSetRadioIdleMode": (
        0xD4,
        tuple(
            {
                "mode": t.EmberRadioPowerMode,
            }.values()
        ),
        tuple({}.values()),
    ),
    "setZllNodeType": (
        0xD5,
        tuple(
            {
                "nodeType": t.EmberNodeType,
            }.values()
        ),
        tuple({}.values()),
    ),
    "setZllAdditionalState": (
        0xD6,
        tuple(
            {
                "state": t.uint16_t,
            }.values()
        ),
        tuple({}.values()),
    ),
    "zllOperationInProgress": (
        0xD7,
        tuple({}.values()),
        tuple(
            {
                "zllOperationInProgress": t.Bool,
            }.values()
        ),
    ),
    "zllRxOnWhenIdleGetActive": (
        0xD8,
        tuple({}.values()),
        tuple(
            {
                "zllRxOnWhenIdleGetActive": t.Bool,
            }.values()
        ),
    ),
    "getZllPrimaryChannelMask": (
        0xD9,
        tuple({}.values()),
        tuple(
            {
                "zllPrimaryChannelMask": t.Channels,
            }.values()
        ),
    ),
    "getZllSecondaryChannelMask": (
        0xDA,
        tuple({}.values()),
        tuple(
            {
                "zllSecondaryChannelMask": t.Channels,
            }.values()
        ),
    ),
    "setZllPrimaryChannelMask": (
        0xDB,
        tuple(
            {
                "zllPrimaryChannelMask": t.Channels,
            }.values()
        ),
        tuple({}.values()),
    ),
    "setZllSecondaryChannelMask": (
        0xDC,
        tuple(
            {
                "zllSecondaryChannelMask": t.Channels,
            }.values()
        ),
        tuple({}.values()),
    ),
    # TODO: are these green power frames in the correct protocol version?
    "gpProxyTableGetEntry": (
        0xC8,
        tuple(
            {
                "proxyIndex": t.uint8_t,
            }.values()
        ),
        tuple(
            {
                "status": t.EmberStatus,
                "entry": t.EmberGpProxyTableEntry,
            }.values()
        ),
    ),
    "gpProxyTableLookup": (
        0xC0,
        tuple(
            {
                "addr": t.EmberGpAddress,
            }.values()
        ),
        tuple(
            {
                "index": t.uint8_t,
            }.values()
        ),
    ),
    "gpSinkTableGetEntry": (
        0xDD,
        tuple(
            {
                "index": t.uint8_t,
            }.values()
        ),
        tuple(
            {
                "status": t.EmberStatus,
                "entry": t.EmberGpSinkTableEntry,
            }.values()
        ),
    ),
    "gpSinkTableLookup": (
        0xDE,
        tuple(
            {
                "addr": t.EmberGpAddress,
            }.values()
        ),
        tuple(
            {
                "index": t.uint8_t,
            }.values()
        ),
    ),
    "gpSinkTableSetEntry": (
        0xDF,
        tuple(
            {
                "sinkIndex": t.uint8_t,
                "entry": t.EmberGpSinkTableEntry,
            }.values()
        ),
        tuple(
            {
                "status": t.EmberStatus,
            }.values()
        ),
    ),
    "gpSinkTableRemoveEntry": (
        0xE0,
        tuple(
            {
                "sinkIndex": t.uint8_t,
            }.values()
        ),
        tuple({}.values()),
    ),
    "gpSinkTableFindOrAllocateEntry": (
        0xE1,
        tuple(
            {
                "addr": t.EmberGpAddress,
            }.values()
        ),
        tuple(
            {
                "index": t.uint8_t,
            }.values()
        ),
    ),
    "gpClearSinkTable": (
        0xE2,
        tuple({}.values()),
        tuple({}.values()),
    ),
    # Changed commands
    "zllSetRxOnWhenIdle": (
        0xB5,
        tuple(
            {
                "durationMs": t.uint32_t,
            }.values()
        ),
        tuple(
            {
                "status": t.EmberStatus,
            }.values()
        ),
    ),
    "networkInit": (
        0x17,
        tuple(
            {"networkInitBitmask": t.EmberNetworkInitBitmask}.values()
        ),  # XXX: We deviate here, since the struct has a single membe.values())r
        tuple(
            {
                "status": t.EmberStatus,
            }.values()
        ),
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
