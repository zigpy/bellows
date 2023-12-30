from . import types as t
from ..v12.commands import COMMANDS as COMMANDS_v12

COMMANDS = {
    **COMMANDS_v12,
    "getNetworkKeyInfo": (
        0x0116,
        (),
        tuple(
            {
                "status": t.sl_Status,
                "bogus": t.uint16_t,
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
    # The following commands are redefined because `sl_zb_sec_man_context_t` changed
    "exportKey": (
        0x0114,
        tuple(
            {
                "context": t.sl_zb_sec_man_context_t,
            }.values()
        ),
        tuple(
            {
                "key": t.KeyData,
                "status": t.sl_Status,
            }.values()
        ),
    ),
    "exportTransientKeyByEui": (
        0x0113,
        tuple(
            {
                "eui64": t.EUI64,
            }.values()
        ),
        tuple(
            {
                "context": t.sl_zb_sec_man_context_t,
                "plaintext_key": t.KeyData,
                "key_data": t.sl_zb_sec_man_aps_key_metadata_t,
                "status": t.sl_Status,
            }.values()
        ),
    ),
    "exportTransientKeyByIndex": (
        0x0112,
        tuple(
            {
                "index": t.uint8_t,
            }.values()
        ),
        tuple(
            {
                "context": t.sl_zb_sec_man_context_t,
                "plaintext_key": t.KeyData,
                "key_data": t.sl_zb_sec_man_aps_key_metadata_t,
                "status": t.sl_Status,
            }.values()
        ),
    ),
    "getApsKeyInfo": (
        0x010C,
        tuple(
            {
                "context_in": t.sl_zb_sec_man_context_t,
            }.values()
        ),
        tuple(
            {
                "eui": t.EUI64,
                "key_data": t.sl_zb_sec_man_aps_key_metadata_t,
                "status": t.sl_Status,
            }.values()
        ),
    ),
    "importKey": (
        0x0115,
        tuple(
            {
                "context": t.sl_zb_sec_man_context_t,
                "key": t.KeyData,
            }.values()
        ),
        tuple(
            {
                "status": t.sl_Status,
            }.values()
        ),
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
