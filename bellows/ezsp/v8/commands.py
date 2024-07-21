from bellows.ezsp.v7.commands import COMMANDS as COMMANDS_v7
import bellows.types as t

COMMANDS = {
    **COMMANDS_v7,
    "getNeighborFrameCounter": (
        0x003E,
        (t.EUI64,),
        (t.EmberStatus, t.uint32_t),
    ),
    "incomingNetworkStatusHandler": (
        0x00C4,
        (),
        tuple(
            {"errorCode": t.EmberStackError, "target": t.EmberNodeId}.values(),
        ),
    ),
    "sendRawMessageExtended": (
        0x0051,
        (t.LVBytes, t.uint8_t, t.Bool),
        (t.EmberStatus,),
    ),
    "setMacPollFailureWaitTime": (
        0x00F4,
        (t.uint8_t,),
        (),
    ),
    "setSourceRouteDiscoveryMode": (
        0x005A,
        (t.uint8_t,),
        (t.uint32_t,),
    ),
    # Changed
    "getTransientKeyTableEntry": (
        0x006D,
        (t.uint8_t,),
        (t.EmberStatus, t.EmberTransientKeyDataV8),
    ),
    "getTransientLinkKey": (
        0x00CE,
        (t.EUI64,),
        (t.EmberStatus, t.EmberTransientKeyDataV8),
    ),
    "setPolicy": (
        0x0055,
        (t.EzspPolicyId, t.uint16_t),
        (t.EzspStatus,),
    ),
    "setSourceRoute": (
        0x00AE,
        (t.EmberNodeId, t.LVList[t.EmberNodeId]),
        (t.EmberStatus,),
    ),
}

del COMMANDS["changeSourceRouteHandler"]
del COMMANDS["getCtune"]
del COMMANDS["setCtune"]
del COMMANDS["setGpioRadioPowerMask"]
del COMMANDS["setMacPollCcaWaitTime"]
