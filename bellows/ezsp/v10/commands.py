import bellows.types as t

from ..v9.commands import COMMANDS as COMMANDS_v9

COMMANDS = {
    **COMMANDS_v9,
    # Use the correct `EmberChildData` object with the extra field
    "getChildData": (
        0x004A,
        {
            "index": t.uint8_t,
        },
        {
            "status": t.EmberStatus,
            "child_data": t.EmberChildDataV10,
        },
    ),
    "setChildData": (
        0x00AC,
        {
            "index": t.uint8_t,
            "child_data": t.EmberChildDataV10,
        },
        {
            "status": t.EmberStatus,
        },
    ),
}
