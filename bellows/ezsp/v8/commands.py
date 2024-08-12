from bellows.ezsp.v7.commands import COMMANDS as COMMANDS_v7
import bellows.types as t

COMMANDS = {
    **COMMANDS_v7,
    "getNeighborFrameCounter": (
        0x003E,
        {
            "eui64": t.EUI64,
        },
        {
            "status": t.EmberStatus,
            "frameCounter": t.uint32_t,
        },
    ),
    "incomingNetworkStatusHandler": (
        0x00C4,
        {},
        {
            "errorCode": t.EmberStackError,
            "target": t.EmberNodeId,
        },
    ),
    "sendRawMessageExtended": (
        0x0051,
        {
            "message": t.LVBytes,
            "priority": t.uint8_t,
            "useCca": t.Bool,
        },
        {
            "status": t.EmberStatus,
        },
    ),
    "setMacPollFailureWaitTime": (
        0x00F4,
        {
            "waitBeforeRetryIntervalMs": t.uint32_t,
        },
        {},
    ),
    "setSourceRouteDiscoveryMode": (
        0x005A,
        {
            "mode": t.uint8_t,
        },
        {
            "remainingTime": t.uint32_t,
        },
    ),
    # Changed
    "getTransientKeyTableEntry": (
        0x006D,
        {
            "index": t.uint8_t,
        },
        {
            "status": t.EmberStatus,
            "transient_key_data": t.EmberTransientKeyDataV8,
        },
    ),
    "getTransientLinkKey": (
        0x00CE,
        {
            "eui64": t.EUI64,
        },
        {
            "status": t.EmberStatus,
            "transient_key_data": t.EmberTransientKeyDataV8,
        },
    ),
    "setSourceRoute": (
        0x00AE,
        {
            "destination": t.EmberNodeId,
            "relayList": t.LVList[t.EmberNodeId],
        },
        {
            "status": t.EmberStatus,
        },
    ),
}

del COMMANDS["changeSourceRouteHandler"]
del COMMANDS["getCtune"]
del COMMANDS["setCtune"]
del COMMANDS["setGpioRadioPowerMask"]
del COMMANDS["setMacPollCcaWaitTime"]
