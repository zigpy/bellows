import bellows.types as t

from ..v16.commands import COMMANDS as COMMANDS_v16

COMMANDS = {
    **COMMANDS_v16,
    "gpProxyTableRemoveEntry": (
        0x005D,
        {
            "proxyIndex": t.uint8_t,
        },
        {},
    ),
    "gpClearProxyTable": (
        0x005F,
        {},
        {},
    ),
    "muxInvalidRxHandler": (
        0x0062,
        {},
        {
            "newRxChannel": t.uint8_t,
            "oldRxChannel": t.uint8_t,
        },
    ),
}
