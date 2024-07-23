from bellows.ezsp.v6.commands import COMMANDS as COMMANDS_v6
import bellows.types as t

COMMANDS = {
    **COMMANDS_v6,
    "sendPanIdUpdate": (
        0x57,
        {
            "newPan": t.EmberPanId,
        },
        {
            "status": t.EmberStatus,
        },
    ),
    "getTrueRandomEntropySource": (
        0x4F,
        {},
        {
            "entropySource": t.EmberEntropySource,
        },
    ),
    "joinNetworkDirectly": (
        0x3B,
        {
            "localNodeType": t.EmberNodeType,
            "beacon": t.EmberBeaconData,
            "radioTxPower": t.int8s,
            "clearBeaconsAfterNetworkUp": t.Bool,
        },
        {
            "status": t.EmberStatus,
        },
    ),
    "getFirstBeacon": (
        0x3D,
        {},
        {
            "status": t.EmberStatus,
            "beaconIterator": t.EmberBeaconIterator,
        },
    ),
    "getNextBeacon": (
        0x04,
        {},
        {
            "status": t.EmberStatus,
            "beaconData": t.EmberBeaconData,
        },
    ),
    "getNumStoredBeacons": (
        0x08,
        {},
        {
            "numStoredBeacons": t.uint8_t,
        },
    ),
    "clearStoredBeacons": (
        0x3C,
        {},
        {},
    ),
    "unicastCurrentNetworkKey": (
        0x50,
        {
            "targetShort": t.EmberNodeId,
            "targetLong": t.EUI64,
            "parentShortId": t.EmberNodeId,
        },
        {
            "status": t.EmberStatus,
        },
    ),
    "setMacPollCcaWaitTime": (
        0xF4,
        {
            "waitBeforeRetryIntervalMs": t.uint8_t,
        },
        {},
    ),
    "setBeaconClassificationParams": (
        0xEF,
        {
            "param": t.EmberBeaconClassificationParams,
        },
        {
            "status": t.EmberStatus,
        },
    ),
    "getBeaconClassificationParams": (
        0xF3,
        {},
        {
            "status": t.EmberStatus,
            "param": t.EmberBeaconClassificationParams,
        },
    ),
    "updateTcLinkKey": (
        0x6C,
        {
            "maxAttempts": t.uint8_t,
        },
        {
            "status": t.EmberStatus,
        },
    ),
    "getTransientKeyTableEntry": (
        0x6D,
        {
            "index": t.uint8_t,
        },
        {
            "status": t.EmberStatus,
            "keyStruct": t.EmberTransientKeyDataV5,
        },
    ),
    "zllClearTokens": (
        0x25,
        {},
        {},
    ),
    "setParentClassificationEnabled": (
        0xE7,
        {
            "enabled": t.Bool,
        },
        {},
    ),
    "getParentClassificationEnabled": (
        0xF0,
        {},
        {
            "enabled": t.Bool,
        },
    ),
    "setLongUpTime": (
        0xE3,
        {
            "hasLongUpTime": t.Bool,
        },
        {},
    ),
    "setHubConnectivity": (
        0xE4,
        {
            "connected": t.Bool,
        },
        {},
    ),
    "isUpTimeLong": (
        0xE5,
        {},
        {
            "hasLongUpTime": t.Bool,
        },
    ),
    "isHubConnected": (
        0xE6,
        {},
        {
            "connected": t.Bool,
        },
    ),
    "gpSinkTableClearAll": (
        0xE2,
        {},
        {},
    ),
    "gpSinkTableInit": (
        0x70,
        {},
        {},
    ),
    # Changed commands
    "getChildData": (
        0x4A,
        {
            "index": t.uint8_t,
        },
        {
            "status": t.EmberStatus,
            "childData": t.EmberChildDataV7,
        },
    ),
}


del COMMANDS["gpClearSinkTable"]
