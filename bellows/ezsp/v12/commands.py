from bellows.types import EmberKeyData

from . import types as t
from ..v11.commands import COMMANDS as COMMANDS_v11

COMMANDS = {
    **COMMANDS_v11,
    "readAttribute": (
        0x0108,
        tuple(
            {
                "endpoint": t.uint8_t,
                "cluster": t.uint16_t,
                "attributeId": t.uint16_t,
                "mask": t.uint8_t,
                "manufacturerCode": t.uint16_t,
            }.values()
        ),
        tuple(
            {
                "status": t.EmberStatus,
                "dataType": t.uint8_t,
                "data": t.LVBytes,
            }.values()
        ),
    ),
    "writeAttribute": (
        0x0109,
        tuple(
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
            }.values()
        ),
        tuple(
            {
                "status": t.EmberStatus,
            }.values()
        ),
    ),
    "setPassiveAckConfig": (
        0x0105,
        tuple(
            {
                "config": t.uint8_t,
                "minAcksNeeded": t.uint8_t,
            }.values()
        ),
        tuple(
            {
                "status": t.EmberStatus,
            }.values()
        ),
    ),
    "checkKeyContext": (
        0x0110,
        tuple(
            {
                "config": t.uint8_t,
                "minAcksNeeded": t.uint8_t,
            }.values()
        ),
        tuple(
            {
                "status": t.EmberStatus,
            }.values()
        ),
    ),
    "childId": (
        0x0106,
        tuple(
            {
                "childIndex": t.uint8_t,
            }.values()
        ),
        tuple(
            {
                "childId": t.EmberNodeId,
            }.values()
        ),
    ),
    "exportKey": (
        0x0114,
        tuple(
            {
                "context": t.sl_zb_sec_man_context_t,
            }.values()
        ),
        tuple(
            {
                "key": EmberKeyData,
                "status": t.sl_Status,
            }.values()
        ),
    ),
    "exportLinkKeyByEui": (
        0x010D,
        tuple(
            {
                "eui64": t.EmberEUI64,
            }.values()
        ),
        tuple(
            {
                "plaintext_key": EmberKeyData,
                "index": t.uint8_t,
                "key_data": t.sl_zb_sec_man_aps_key_metadata_t,
                "status": t.sl_Status,
            }.values()
        ),
    ),
    "exportLinkKeyByIndex": (
        0x010F,
        tuple(
            {
                "index": t.uint8_t,
            }.values()
        ),
        tuple(
            {
                "eui64": t.EmberEUI64,
                "plaintext_key": EmberKeyData,
                "key_data": t.sl_zb_sec_man_aps_key_metadata_t,
                "status": t.sl_Status,
            }.values()
        ),
    ),
    "exportTransientKeyByEui": (
        0x0113,
        tuple(
            {
                "eui64": t.EmberEUI64,
            }.values()
        ),
        tuple(
            {
                "context": t.sl_zb_sec_man_context_t,
                "plaintext_key": EmberKeyData,
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
                "plaintext_key": EmberKeyData,
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
                "eui": t.EmberEUI64,
                "key_data": t.sl_zb_sec_man_aps_key_metadata_t,
                "status": t.sl_Status,
            }.values()
        ),
    ),
    "gpSinkCommission": (
        0x010A,
        tuple(
            {
                "options": t.uint8_t,
                "gpmAddrForSecurity": t.uint16_t,
                "gpmAddrForPairing": t.uint16_t,
                "sinkEndpoint": t.uint8_t,
            }.values()
        ),
        tuple(
            {
                "status": t.EmberStatus,
            }.values()
        ),
    ),
    "gpTranslationTableClear": (
        0x010B,
        (),
        (),
    ),
    "importKey": (
        0x0115,
        tuple(
            {
                "context": t.sl_zb_sec_man_context_t,
                "key": EmberKeyData,
            }.values()
        ),
        tuple(
            {
                "status": t.sl_Status,
            }.values()
        ),
    ),
    "importLinkKey": (
        0x010E,
        tuple(
            {
                "index": t.uint8_t,
                "address": t.EmberEUI64,
                "key": EmberKeyData,
            }.values()
        ),
        tuple(
            {
                "status": t.sl_Status,
            }.values()
        ),
    ),
    "importTransientKey": (
        0x0111,
        tuple(
            {
                "eui64": t.EmberEUI64,
                "plaintext_key": EmberKeyData,
                "flags": t.sl_zb_sec_man_flags_t,
            }.values()
        ),
        tuple(
            {
                "status": t.sl_Status,
            }.values()
        ),
    ),
}
