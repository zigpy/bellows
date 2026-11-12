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
    # The token info `size` field is a `uint32_t` since Simplicity SDK 2025.12
    "getTokenInfo": (
        0x0101,
        {
            "index": t.uint8_t,
        },
        {
            "status": t.sl_Status,
            "token_info": t.SlZigbeeTokenInfo,
        },
    ),
}
