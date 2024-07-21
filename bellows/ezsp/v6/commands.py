from bellows.ezsp.v5.commands import COMMANDS as COMMANDS_v5
import bellows.types as t

COMMANDS = {
    **COMMANDS_v5,
    "getPhyInterfaceCount": (
        0xFC,
        (),
        (t.uint8_t,),
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
    "getRadioParameters": (
        0xFD,
        (t.uint8_t,),
        (t.EmberStatus, t.EmberNodeType, t.EmberNetworkParameters),
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
        (
            t.EmberStatus,
            t.uint8_t,
        ),
    ),
    "writeNodeData": (
        0xFE,
        (t.Bool,),
        (t.EmberStatus,),
    ),
    "sendTrustCenterLinkKey": (
        0x67,
        (t.EmberNodeId, t.EUI64),
        (t.EmberStatus,),
    ),
    "zllSetSecurityStateWithoutKey": (
        0xCF,
        (t.EmberZllInitialSecurityState,),
        (t.EmberStatus,),
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
    "gpClearSinkTable": (
        0xE2,
        (),
        (),
    ),
    # Changed commands
    "zllSetRxOnWhenIdle": (
        0xB5,
        (t.uint32_t,),
        (t.EmberStatus,),
    ),
    "networkInit": (
        0x17,
        (t.EmberNetworkInitBitmask,),
        (t.EmberStatus,),
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
