import bellows.types as t

from ..v17.commands import COMMANDS as COMMANDS_v17

COMMANDS = {
    **COMMANDS_v17,
    "macFilterMatchMessageHandler": (
        0x46,
        {},
        {
            "filterValueMatch": t.uint16_t,  # Was `filterIndexMatch: uint8_t`
            "legacyPassthroughType": t.EmberMacPassthroughType,
            "lastHopLqi": t.uint8_t,
            "lastHopRssi": t.int8s,
            "messageContents": t.LVBytes,
        },
    ),
}
