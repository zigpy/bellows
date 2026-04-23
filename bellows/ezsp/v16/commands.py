import bellows.types as t

from ..v14.commands import COMMANDS as COMMANDS_v14

COMMANDS = {
    **COMMANDS_v14,
    # EZSP v16 appends an ``EmberRxPacketInfo`` struct after the LVBytes
    # payload in ``gpepIncomingMessageHandler``. zigbee-herdsman gates the
    # read on ``version >= 0x10`` (see
    # ``src/adapter/ember/ezsp/ezsp.ts`` in the ``ember`` adapter), so v13
    # and v14 do not carry this trailer but v16 does. v17 and v18 override
    # the whole command again, so this entry only matters for v16.
    "gpepIncomingMessageHandler": (
        0x00C5,
        {},
        {
            "status": t.uint8_t,
            "gpdLink": t.uint8_t,
            "sequenceNumber": t.uint8_t,
            "addr": t.EmberGpAddress,
            "gpdfSecurityLevel": t.EmberGpSecurityLevel,
            "gpdfSecurityKeyType": t.EmberGpKeyType,
            "autoCommissioning": t.Bool,
            "bidirectionalInfo": t.uint8_t,
            "gpdSecurityFrameCounter": t.uint32_t,
            "gpdCommandId": t.uint8_t,
            "mic": t.uint32_t,
            "proxyTableIndex": t.uint8_t,
            "gpdCommandPayload": t.LVBytes,
            "packetInfo": t.SlRxPacketInfo,
        },
    ),
}
