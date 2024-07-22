from bellows.ezsp.v7.commands import COMMANDS as COMMANDS_v7
import bellows.types as t

COMMANDS = {
    **COMMANDS_v7,
    "getNeighborFrameCounter": (
        0x003E,
        tuple(
            {
                "eui64": t.EUI64,
            }.values()
        ),
        tuple(
            {
                "status": t.EmberStatus,
                "frameCounter": t.uint32_t,
            }.values()
        ),
    ),
    "incomingNetworkStatusHandler": (
        0x00C4,
        tuple({}.values()),
        tuple(
            {
                "errorCode": t.EmberStackError,
                "target": t.EmberNodeId,
            }.values()
        ),
    ),
    "sendRawMessageExtended": (
        0x0051,
        tuple(
            {
                "message": t.LVBytes,
                "priority": t.uint8_t,
                "useCca": t.Bool,
            }.values()
        ),
        tuple(
            {
                "status": t.EmberStatus,
            }.values()
        ),
    ),
    "setMacPollFailureWaitTime": (
        0x00F4,
        tuple(
            {
                "waitBeforeRetryIntervalMs": t.uint32_t,
            }.values()
        ),
        tuple({}.values()),
    ),
    "setSourceRouteDiscoveryMode": (
        0x005A,
        tuple(
            {
                "mode": t.uint8_t,
            }.values()
        ),
        tuple(
            {
                "remainingTime": t.uint32_t,
            }.values()
        ),
    ),
    # Changed
    "getTransientKeyTableEntry": (
        0x006D,
        tuple(
            {
                "index": t.uint8_t,
            }.values()
        ),
        tuple(
            {
                "status": t.EmberStatus,
                "transient_key_data": t.EmberTransientKeyDataV8,
            }.values()
        ),
    ),
    "getTransientLinkKey": (
        0x00CE,
        tuple(
            {
                "eui64": t.EUI64,
            }.values()
        ),
        tuple(
            {
                "status": t.EmberStatus,
                "transient_key_data": t.EmberTransientKeyDataV8,
            }.values()
        ),
    ),
    "setSourceRoute": (
        0x00AE,
        tuple(
            {
                "destination": t.EmberNodeId,
                "relays": t.LVList[t.EmberNodeId],
            }.values()
        ),
        tuple(
            {
                "status": t.EmberStatus,
            }.values()
        ),
    ),
}

del COMMANDS["changeSourceRouteHandler"]
del COMMANDS["getCtune"]
del COMMANDS["setCtune"]
del COMMANDS["setGpioRadioPowerMask"]
del COMMANDS["setMacPollCcaWaitTime"]
