from . import types as t
from ..v12.commands import COMMANDS as COMMANDS_v12

COMMANDS = {
    **COMMANDS_v12,
    "getNetworkKeyInfo": (
        0x0116,
        (),
        tuple(
            {
                "status": t.EmberStatus,
                "network_key_info": t.sl_zb_sec_man_network_key_info_t,
            }.values()
        ),
    ),
    "gpSecurityTestVectors": (
        0x0117,
        (),
        tuple(
            {
                "status": t.EmberStatus,
            }.values()
        ),
    ),
    "tokenFactoryReset": (
        0x0077,
        tuple({"excludeOutgoingFC": t.Bool, "excludeBootCounter": t.Bool}.values()),
        (),
    ),
    "gpSinkTableGetNumberOfActiveEntries": (
        0x0118,
        (),
        tuple(
            {
                "number_of_entries": t.uint8_t,
            }.values()
        ),
    ),
}

del COMMANDS["getKey"]
del COMMANDS["getKeyTableEntry"]
del COMMANDS["setKeyTableEntry"]
del COMMANDS["addOrUpdateKeyTableEntry"]
del COMMANDS["addTransientLinkKey"]
del COMMANDS["getTransientLinkKey"]
del COMMANDS["getTransientKeyTableEntry"]
del COMMANDS["setSecurityKey"]
del COMMANDS["setSecurityParameters"]
del COMMANDS["resetToFactoryDefaults"]
del COMMANDS["getSecurityKeyStatus"]
