from bellows.ezsp.v4.commands import COMMANDS as COMMANDS_v4
import bellows.types as t

COMMANDS = {
    **COMMANDS_v4,
    "changeSourceRouteHandler": (
        0xC4,
        {},
        {
            "newChildId": t.EmberNodeId,
            "newParentId": t.EmberNodeId,
            "ourChild": t.Bool,
        },
    ),
    "setSecurityKey": (
        0xCA,
        {
            "securityKey": t.KeyData,
            "securityType": t.SecureEzspSecurityType,
        },
        {
            "status": t.EzspStatus,
        },
    ),
    "setSecurityParameters": (
        0xCB,
        {
            "securityLevel": t.SecureEzspSecurityLevel,
        },
        {
            "status": t.EzspStatus,
            "randomNumber": t.uint128_t,
        },
    ),
    "resetToFactoryDefaults": (
        0xCC,
        {},
        {
            "status": t.EzspStatus,
        },
    ),
    "getSecurityKeyStatus": (
        0xCD,
        {},
        {
            "status": t.EzspStatus,
            "securityType": t.SecureEzspSecurityType,
        },
    ),
    "getTransientLinkKey": (
        0xCE,
        {
            "eui": t.EUI64,
        },
        {
            "status": t.EmberStatus,
            "transientKeyData": t.EmberTransientKeyDataV5,
        },
    ),
    "setChannelMap": (
        0xF7,
        {
            "page": t.uint8_t,
            "channel": t.uint8_t,
        },
        {},
    ),
}
