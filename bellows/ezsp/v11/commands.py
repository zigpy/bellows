import bellows.types as t

from ..v10.commands import COMMANDS as COMMANDS_v10

COMMANDS = {
    **COMMANDS_v10,
    "pollHandler": (
        0x0044,
        {},
        {
            "childId": t.EmberNodeId,
            "transmitExpected": t.Bool,
        },
    ),
}
