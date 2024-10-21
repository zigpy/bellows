from zigpy.types import EUI64, NWK, BroadcastAddress, Struct

import bellows.types as t

from ..v13.commands import COMMANDS as COMMANDS_v13


class GetTokenDataRsp(Struct):
    status: t.sl_Status
    value: t.LVBytes32


# EmberStatus and EzspStatus have been replaced with sl_Status globally.
# The `status` field is also moved to be the first parameter in most responses.
_REPLACEMENTS = {
    t.EmberStatus: t.sl_Status,
    t.EzspStatus: t.sl_Status,
}

COMMANDS = {
    "setExtendedTimeout": (
        0x007E,
        {
            "remoteEui64": t.EUI64,
            "extendedTimeout": t.Bool,
        },
        {
            "status": t.sl_Status,
        },
    ),
    "getTokenData": (
        0x0102,
        {
            "token": t.uint32_t,
            "index": t.uint32_t,
        },
        GetTokenDataRsp,
    ),
    "exportLinkKeyByIndex": (
        0x010F,
        {
            "index": t.uint8_t,
        },
        {
            "status": t.sl_Status,
            "context": t.SecurityManagerContextV13,
            "plaintext_key": t.KeyData,
            "key_data": t.SecurityManagerAPSKeyMetadata,
        },
    ),
    "exportKey": (
        0x0114,
        {
            "context": t.SecurityManagerContextV13,
        },
        {
            "status": t.sl_Status,
            "key": t.KeyData,
            "context": t.SecurityManagerContextV13,
        },
    ),
    "getAddressTableInfo": (
        0x005E,
        {
            "index": t.uint8_t,
        },
        {
            "status": t.sl_Status,
            "nwk": NWK,
            "eui64": EUI64,
        },
    ),
    "incomingMessageHandler": (
        0x0045,
        {},
        {
            "message_type": t.EmberIncomingMessageType,
            "aps_frame": t.EmberApsFrame,
            "nwk": NWK,
            "eui64": EUI64,
            "binding_index": t.uint8_t,
            "address_index": t.uint8_t,
            "lqi": t.uint8_t,
            "rssi": t.int8s,
            "timestamp": t.uint32_t,
            "message": t.LVBytes,
        },
    ),
    "messageSentHandler": (
        0x003F,
        {},
        {
            "status": t.sl_Status,
            "message_type": t.EmberOutgoingMessageType,
            "nwk": NWK,
            "aps_frame": t.EmberApsFrame,
            "message_tag": t.uint16_t,
            "message": t.LVBytes,
        },
    ),
    "sendUnicast": (
        0x0034,
        {
            "message_type": t.EmberOutgoingMessageType,
            "nwk": NWK,
            "aps_frame": t.EmberApsFrame,
            "message_tag": t.uint16_t,
            "message": t.LVBytes,
        },
        {
            "status": t.sl_Status,
            "sequence": t.uint8_t,
        },
    ),
    "sendBroadcast": (
        0x0036,
        {
            "alias": t.uint16_t,
            "destination": BroadcastAddress,
            "sequence": t.uint8_t,
            "aps_frame": t.EmberApsFrame,
            "radius": t.uint8_t,
            "message_tag": t.uint16_t,
            "message": t.LVBytes,
        },
        {
            "status": t.sl_Status,
            "sequence": t.uint8_t,
        },
    ),
    "sendMulticast": (
        0x0038,
        {
            "aps_frame": t.EmberApsFrame,
            "hops": t.uint8_t,
            "broadcast_addr": t.BroadcastAddress,
            "alias": t.uint16_t,
            "sequence": t.uint8_t,
            "message_tag": t.uint16_t,
            "message": t.LVBytes,
        },
        {
            "status": t.sl_Status,
            "sequence": t.uint8_t,
        },
    ),
    "launchStandaloneBootloader": (
        0x008F,
        {
            "mode": t.uint8_t,
        },
        {
            # XXX: One of the few commands that does *not* migrate to `sl_Status`!
            "status": t.EmberStatus,
        },
    ),
}


for name, (command_id, tx_schema, rx_schema) in COMMANDS_v13.items():
    if name in COMMANDS:
        continue

    if isinstance(tx_schema, dict):
        tx_schema = {k: _REPLACEMENTS.get(v, v) for k, v in tx_schema.items()}

    if isinstance(rx_schema, dict):
        rx_schema = {k: _REPLACEMENTS.get(v, v) for k, v in rx_schema.items()}

    COMMANDS[name] = (command_id, tx_schema, rx_schema)

del COMMANDS["getAddressTableRemoteEui64"]
