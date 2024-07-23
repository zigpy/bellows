import bellows.types as t

from ..v12.commands import COMMANDS as COMMANDS_v12

COMMANDS = {
    **COMMANDS_v12,
    "getNetworkKeyInfo": (
        0x0116,
        {},
        {
            "status": t.sl_Status,
            "network_key_info": t.SecurityManagerNetworkKeyInfo,
        },
    ),
    "gpSecurityTestVectors": (
        0x0117,
        {},
        {
            "status": t.EmberStatus,
        },
    ),
    "tokenFactoryReset": (
        0x0077,
        {
            "excludeOutgoingFC": t.Bool,
            "excludeBootCounter": t.Bool,
        },
        {},
    ),
    "gpSinkTableGetNumberOfActiveEntries": (
        0x0118,
        {},
        {
            "number_of_entries": t.uint8_t,
        },
    ),
    # The following commands are redefined because `SecurityManagerContext` changed
    "exportKey": (
        0x0114,
        {
            "context": t.SecurityManagerContextV13,
        },
        {
            "key": t.KeyData,
            "status": t.sl_Status,
        },
    ),
    "exportTransientKeyByEui": (
        0x0113,
        {
            "eui64": t.EUI64,
        },
        {
            "context": t.SecurityManagerContextV13,
            "plaintext_key": t.KeyData,
            "key_data": t.SecurityManagerAPSKeyMetadata,
            "status": t.sl_Status,
        },
    ),
    "exportTransientKeyByIndex": (
        0x0112,
        {
            "index": t.uint8_t,
        },
        {
            "context": t.SecurityManagerContextV13,
            "plaintext_key": t.KeyData,
            "key_data": t.SecurityManagerAPSKeyMetadata,
            "status": t.sl_Status,
        },
    ),
    "getApsKeyInfo": (
        0x010C,
        {
            "context_in": t.SecurityManagerContextV13,
        },
        {
            "eui": t.EUI64,
            "key_data": t.SecurityManagerAPSKeyMetadata,
            "status": t.sl_Status,
        },
    ),
    "importKey": (
        0x0115,
        {
            "context": t.SecurityManagerContextV13,
            "key": t.KeyData,
        },
        {
            "status": t.sl_Status,
        },
    ),
}

del COMMANDS["becomeTrustCenter"]  # this one was likely removed earlier
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
