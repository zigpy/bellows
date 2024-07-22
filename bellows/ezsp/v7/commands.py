from bellows.ezsp.v6.commands import COMMANDS as COMMANDS_v6
import bellows.types as t

COMMANDS = {
    **COMMANDS_v6,
    "sendPanIdUpdate": (
        0x57,
        tuple(
            {
                "newPan": t.EmberPanId,
            }.values()
        ),
        tuple(
            {
                "status": t.EmberStatus,
            }.values()
        ),
    ),
    "getTrueRandomEntropySource": (
        0x4F,
        tuple({}.values()),
        tuple(
            {
                "entropySource": t.EmberEntropySource,
            }.values()
        ),
    ),
    "joinNetworkDirectly": (
        0x3B,
        tuple(
            {
                "localNodeType": t.EmberNodeType,
                "beacon": t.EmberBeaconData,
                "radioTxPower": t.int8s,
                "clearBeaconsAfterNetworkUp": t.Bool,
            }.values()
        ),
        tuple(
            {
                "status": t.EmberStatus,
            }.values()
        ),
    ),
    "getFirstBeacon": (
        0x3D,
        tuple({}.values()),
        tuple(
            {
                "status": t.EmberStatus,
                "beaconIterator": t.EmberBeaconIterator,
            }.values()
        ),
    ),
    "getNextBeacon": (
        0x04,
        tuple({}.values()),
        tuple(
            {
                "status": t.EmberStatus,
                "beaconData": t.EmberBeaconData,
            }.values()
        ),
    ),
    "getNumStoredBeacons": (
        0x08,
        tuple({}.values()),
        tuple(
            {
                "numStoredBeacons": t.uint8_t,
            }.values()
        ),
    ),
    "clearStoredBeacons": (
        0x3C,
        tuple({}.values()),
        tuple({}.values()),
    ),
    "unicastCurrentNetworkKey": (
        0x50,
        tuple(
            {
                "targetShort": t.EmberNodeId,
                "targetLong": t.EUI64,
                "parentShortId": t.EmberNodeId,
            }.values()
        ),
        tuple(
            {
                "status": t.EmberStatus,
            }.values()
        ),
    ),
    "setMacPollCcaWaitTime": (
        0xF4,
        tuple(
            {
                "waitBeforeRetryIntervalMs": t.uint8_t,
            }.values()
        ),
        tuple({}.values()),
    ),
    "setBeaconClassificationParams": (
        0xEF,
        tuple(
            {
                "param": t.EmberBeaconClassificationParams,
            }.values()
        ),
        tuple(
            {
                "status": t.EmberStatus,
            }.values()
        ),
    ),
    "getBeaconClassificationParams": (
        0xF3,
        tuple({}.values()),
        tuple(
            {
                "status": t.EmberStatus,
                "param": t.EmberBeaconClassificationParams,
            }.values()
        ),
    ),
    "updateTcLinkKey": (
        0x6C,
        tuple(
            {
                "maxAttempts": t.uint8_t,
            }.values()
        ),
        tuple(
            {
                "status": t.EmberStatus,
            }.values()
        ),
    ),
    "getTransientKeyTableEntry": (
        0x6D,
        tuple(
            {
                "index": t.uint8_t,
            }.values()
        ),
        tuple(
            {
                "status": t.EmberStatus,
                "keyStruct": t.EmberTransientKeyDataV5,
            }.values()
        ),
    ),
    "zllClearTokens": (
        0x25,
        tuple({}.values()),
        tuple({}.values()),
    ),
    "setParentClassificationEnabled": (
        0xE7,
        tuple(
            {
                "enabled": t.Bool,
            }.values()
        ),
        tuple({}.values()),
    ),
    "getParentClassificationEnabled": (
        0xF0,
        tuple({}.values()),
        tuple(
            {
                "enabled": t.Bool,
            }.values()
        ),
    ),
    "setLongUpTime": (
        0xE3,
        tuple(
            {
                "hasLongUpTime": t.Bool,
            }.values()
        ),
        tuple({}.values()),
    ),
    "setHubConnectivity": (
        0xE4,
        tuple(
            {
                "connected": t.Bool,
            }.values()
        ),
        tuple({}.values()),
    ),
    "isUpTimeLong": (
        0xE5,
        tuple({}.values()),
        tuple(
            {
                "hasLongUpTime": t.Bool,
            }.values()
        ),
    ),
    "isHubConnected": (
        0xE6,
        tuple({}.values()),
        tuple(
            {
                "connected": t.Bool,
            }.values()
        ),
    ),
    "gpSinkTableClearAll": (
        0xE2,
        tuple({}.values()),
        tuple({}.values()),
    ),
    "gpSinkTableInit": (
        0x70,
        tuple({}.values()),
        tuple({}.values()),
    ),
    # Changed commands
    "getChildData": (
        0x4A,
        tuple(
            {
                "index": t.uint8_t,
            }.values()
        ),
        tuple(
            {
                "status": t.EmberStatus,
                "childData": t.EmberChildDataV7,
            }.values()
        ),
    ),
}


del COMMANDS["gpClearSinkTable"]
