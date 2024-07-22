from bellows.ezsp.v4.commands import COMMANDS as COMMANDS_v4
import bellows.types as t

COMMANDS = {
    **COMMANDS_v4,
    "changeSourceRouteHandler": (
        0xC4,
        (),
        (t.EmberNodeId, t.EmberNodeId, t.Bool),
    ),
    "setSecurityKey": (
        0xCA,
        (t.KeyData, t.SecureEzspSecurityType),
        (t.EzspStatus,),
    ),
    "setSecurityParameters": (
        0xCB,
        (t.SecureEzspSecurityLevel, t.uint128_t),
        (t.EzspStatus, t.uint128_t),
    ),
    "resetToFactoryDefaults": (
        0xCC,
        (),
        (t.EzspStatus,),
    ),
    "getSecurityKeyStatus": (
        0xCD,
        (),
        (t.EzspStatus, t.SecureEzspSecurityType),
    ),
    "getTransientLinkKey": (
        0xCE,
        (t.EUI64,),
        (t.EmberStatus, t.EmberTransientKeyDataV5),
    ),
    "setChannelMap": (
        0xF7,
        (t.uint8_t, t.uint8_t),
        (),
    ),
}
