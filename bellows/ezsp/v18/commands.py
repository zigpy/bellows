from zigpy.types import EUI64, NWK, BroadcastAddress

import bellows.types as t

from ..v17.commands import COMMANDS as COMMANDS_v17

COMMANDS = {
    **COMMANDS_v17,
    "sendUnicast": (
        0x0034,
        {
            "message_type": t.EmberOutgoingMessageType,
            "nwk": NWK,
            "aps_frame": t.EmberApsFrameV18,  # APS frame format has changed
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
            "aps_frame": t.EmberApsFrameV18,  # APS frame format has changed
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
            "aps_frame": t.EmberApsFrameV18,  # APS frame format has changed
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
    "sendReply": (
        0x0039,
        {
            "sender": t.NWK,
            "aps_frame": t.EmberApsFrameV18,  # APS frame format has changed
            "message": t.LVBytes,
        },
        {
            "status": t.sl_Status,
        },
    ),
    "incomingMessageHandler": (
        0x0045,
        {},
        {
            "message_type": t.EmberIncomingMessageType,
            "aps_frame": t.EmberApsFrameV18,  # APS frame format has changed
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
            "aps_frame": t.EmberApsFrameV18,  # APS frame format has changed
            "message_tag": t.uint16_t,
            "message": t.LVBytes,
        },
    ),
    "macFilterMatchMessageHandler": (
        0x46,
        {},
        {
            "filterValueMatch": t.uint16_t,  # Was `filterIndexMatch: uint8_t`
            "legacyPassthroughType": t.EmberMacPassthroughType,
            "lastHopLqi": t.uint8_t,
            "lastHopRssi": t.int8s,
            "messageContents": t.LVBytes,
        },
    ),
}
