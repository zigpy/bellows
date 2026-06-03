import bellows.types as t

from ..v14.commands import COMMANDS as COMMANDS_v14

COMMANDS = {
    **COMMANDS_v14,
    # The priorities struct grew from three to five fields
    "radioSetSchedulerPriorities": (
        0x012B,
        {
            "priorities": t.Sl802154RadioPriorities,
        },
        {},
    ),
}
