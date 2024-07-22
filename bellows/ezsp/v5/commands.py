from bellows.ezsp.v4.commands import COMMANDS as COMMANDS_v4
import bellows.types as t

COMMANDS = {
    **COMMANDS_v4,
    "changeSourceRouteHandler": (
        0xC4,
        tuple({}.values()),
        tuple(
            {
                "newChildId": t.EmberNodeId,
                "newParentId": t.EmberNodeId,
                "ourChild": t.Bool,
            }.values()
        ),
    ),
    "setSecurityKey": (
        0xCA,
        tuple(
            {
                "securityKey": t.KeyData,
                "securityType": t.SecureEzspSecurityType,
            }.values()
        ),
        tuple(
            {
                "status": t.EzspStatus,
            }.values()
        ),
    ),
    "setSecurityParameters": (
        0xCB,
        tuple(
            {
                "securityLevel": t.SecureEzspSecurityLevel,
            }.values()
        ),
        tuple(
            {
                "status": t.EzspStatus,
                "randomNumber": t.uint128_t,
            }.values()
        ),
    ),
    "resetToFactoryDefaults": (
        0xCC,
        tuple({}.values()),
        tuple(
            {
                "status": t.EzspStatus,
            }.values()
        ),
    ),
    "getSecurityKeyStatus": (
        0xCD,
        tuple({}.values()),
        tuple(
            {
                "status": t.EzspStatus,
                "securityType": t.SecureEzspSecurityType,
            }.values()
        ),
    ),
    "getTransientLinkKey": (
        0xCE,
        tuple(
            {
                "eui": t.EUI64,
            }.values()
        ),
        tuple(
            {
                "status": t.EmberStatus,
                "transientKeyData": t.EmberTransientKeyDataV5,
            }.values()
        ),
    ),
    "setChannelMap": (
        0xF7,
        tuple(
            {
                "page": t.uint8_t,
                "channel": t.uint8_t,
            }.values()
        ),
        tuple({}.values()),
    ),
}
