from zigpy.types import EUI64, NWK, Struct, StructField

from . import types as t
from ..v13.commands import COMMANDS as COMMANDS_v13


class GetTokenDataRsp(Struct):
    status: t.sl_Status
    value: t.LVBytes32 = StructField(
        requires=lambda rsp: rsp.status == t.EmberStatus.SUCCESS
    )


# EmberStatus and EzspStatus have been replaced with sl_Status globally
_REPLACEMENTS = {
    t.EmberStatus: t.sl_Status,
    t.EzspStatus: t.sl_Status,
}

COMMANDS = {
    "getTokenData": (
        0x0102,
        tuple({"token": t.uint32_t, "index": t.uint32_t}.values()),
        GetTokenDataRsp,
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
                "status": t.sl_Status,
                "key": t.KeyData,
                "context": t.sl_zb_sec_man_context_t,
            }.values()
        ),
    ),
    "getAddressTableInfo": (
        0x005E,
        tuple(
            {
                "index": t.uint8_t,
            }.values()
        ),
        tuple(
            {
                "status": t.sl_Status,
                "nwk": NWK,
                "eui64": EUI64,
            }.values()
        ),
    ),
    "incomingMessageHandler": (
        0x0045,
        tuple({}.values()),
        tuple(
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
            }.values()
        ),
    ),
    "messageSentHandler": (
        0x003F,
        tuple({}.values()),
        tuple(
            {
                "status": t.sl_Status,
                "message_type": t.EmberOutgoingMessageType,
                "nwk": NWK,
                "aps_frame": t.EmberApsFrame,
                "message_tag": t.uint8_t,
                "message": t.LVBytes,
            }.values()
        ),
    ),
}


for name, (command_id, tx_schema, rx_schema) in COMMANDS_v13.items():
    if name in COMMANDS:
        continue

    if not isinstance(tx_schema, Struct):
        tx_schema = tuple([_REPLACEMENTS.get(s, s) for s in tx_schema])

    if not isinstance(tx_schema, Struct):
        rx_schema = tuple([_REPLACEMENTS.get(s, s) for s in rx_schema])

    COMMANDS[name] = (command_id, tx_schema, rx_schema)

del COMMANDS["getAddressTableRemoteEui64"]
