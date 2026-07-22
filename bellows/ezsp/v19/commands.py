import bellows.types as t

from ..v18.commands import COMMANDS as COMMANDS_v18

COMMANDS = {
    **COMMANDS_v18,
    # Added in Simplicity SDK 2026.6.0
    "clearBindingTableOnLeave": (
        0x006D,
        {
            "clear": t.Bool,
        },
        {},
    ),
}
