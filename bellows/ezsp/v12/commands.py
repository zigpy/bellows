import bellows.types as t
from bellows.types import KeyData

from ..v11.commands import COMMANDS as COMMANDS_v11

COMMANDS = {
    **COMMANDS_v11,
    "readAttribute": (
        0x0108,
        {
            "endpoint": t.uint8_t,
            "cluster": t.uint16_t,
            "attributeId": t.uint16_t,
            "mask": t.uint8_t,
            "manufacturerCode": t.uint16_t,
        },
        {
            "status": t.EmberStatus,
            "dataType": t.uint8_t,
            "data": t.LVBytes,
        },
    ),
    "writeAttribute": (
        0x0109,
        {
            "endpoint": t.uint8_t,
            "cluster": t.uint16_t,
            "attributeId": t.uint16_t,
            "mask": t.uint8_t,
            "manufacturerCode": t.uint16_t,
            "overrideReadOnlyAndDataType": t.Bool,
            "justTest": t.Bool,
            "dataType": t.uint8_t,
            "data": t.LVBytes,
        },
        {
            "status": t.EmberStatus,
        },
    ),
    "setPassiveAckConfig": (
        0x0105,
        {
            "config": t.uint8_t,
            "minAcksNeeded": t.uint8_t,
        },
        {
            "status": t.EmberStatus,
        },
    ),
    "checkKeyContext": (
        0x0110,
        {
            "config": t.uint8_t,
            "minAcksNeeded": t.uint8_t,
        },
        {
            "status": t.EmberStatus,
        },
    ),
    "childId": (
        0x0106,
        {
            "childIndex": t.uint8_t,
        },
        {
            "childId": t.EmberNodeId,
        },
    ),
    "exportKey": (
        0x0114,
        {
            "context": t.SecurityManagerContextV12,
        },
        {
            "key": KeyData,
            "status": t.sl_Status,
        },
    ),
    "exportLinkKeyByEui": (
        0x010D,
        {
            "eui64": t.EUI64,
        },
        {
            "plaintext_key": KeyData,
            "index": t.uint8_t,
            "key_data": t.SecurityManagerAPSKeyMetadata,
            "status": t.sl_Status,
        },
    ),
    "exportLinkKeyByIndex": (
        0x010F,
        {
            "index": t.uint8_t,
        },
        {
            "eui64": t.EUI64,
            "plaintext_key": KeyData,
            "key_data": t.SecurityManagerAPSKeyMetadata,
            "status": t.sl_Status,
        },
    ),
    "exportTransientKeyByEui": (
        0x0113,
        {
            "eui64": t.EUI64,
        },
        {
            "context": t.SecurityManagerContextV12,
            "plaintext_key": KeyData,
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
            "context": t.SecurityManagerContextV12,
            "plaintext_key": KeyData,
            "key_data": t.SecurityManagerAPSKeyMetadata,
            "status": t.sl_Status,
        },
    ),
    "getApsKeyInfo": (
        0x010C,
        {
            "context_in": t.SecurityManagerContextV12,
        },
        {
            "eui": t.EUI64,
            "key_data": t.SecurityManagerAPSKeyMetadata,
            "status": t.sl_Status,
        },
    ),
    "gpSinkCommission": (
        0x010A,
        {
            "options": t.uint8_t,
            "gpmAddrForSecurity": t.uint16_t,
            "gpmAddrForPairing": t.uint16_t,
            "sinkEndpoint": t.uint8_t,
        },
        {
            "status": t.EmberStatus,
        },
    ),
    "gpTranslationTableClear": (
        0x010B,
        (),
        (),
    ),
    "importKey": (
        0x0115,
        {
            "context": t.SecurityManagerContextV12,
            "key": KeyData,
        },
        {
            "status": t.sl_Status,
        },
    ),
    "importLinkKey": (
        0x010E,
        {
            "index": t.uint8_t,
            "address": t.EUI64,
            "key": KeyData,
        },
        {
            "status": t.sl_Status,
        },
    ),
    "importTransientKey": (
        0x0111,
        {
            "eui64": t.EUI64,
            "plaintext_key": KeyData,
            "flags": t.SecurityManagerContextFlags,
        },
        {
            "status": t.sl_Status,
        },
    ),
}
