from bellows.ezsp.v6.commands import COMMANDS as COMMANDS_v6
import bellows.types as t

COMMANDS = {
    **COMMANDS_v6,
    "sendPanIdUpdate": (
        0x57,
        (t.EmberPanId,),
        (t.Bool,),
    ),
    "getTrueRandomEntropySource": (
        0x4F,
        (),
        (t.EmberEntropySource,),
    ),
    "joinNetworkDirectly": (
        0x3B,
        (t.EmberNodeType, t.EmberBeaconData, t.int8s, t.Bool),
        (t.EmberStatus,),
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
    "unicastCurrentNetworkKey": (
        0x50,
        (t.EmberNodeId, t.EUI64, t.EmberNodeId),
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
    "updateTcLinkKey": (
        0x6C,
        (t.uint8_t,),
        (t.EmberStatus,),
    ),
    "getTransientKeyTableEntry": (
        0x6D,
        (t.uint8_t,),
        (t.EmberStatus, t.EmberTransientKeyDataV5),
    ),
    "zllClearTokens": (
        0x25,
        (),
        (),
    ),
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
    # Changed commands
    "getChildData": (
        0x4A,
        (t.uint8_t,),
        (t.EmberStatus, t.EmberChildDataV7),
    ),
}


del COMMANDS["gpClearSinkTable"]
