import bellows.types as t

from ..v16.commands import COMMANDS as COMMANDS_v16

COMMANDS = {
    **COMMANDS_v16,
    "gpProxyTableRemoveEntry": (
        0x005D,
        {
            "proxyIndex": t.uint8_t,
        },
        {},
    ),
    "gpClearProxyTable": (
        0x005F,
        {},
        {},
    ),
    "muxInvalidRxHandler": (
        0x0062,
        {},
        {
            "newRxChannel": t.uint8_t,
            "oldRxChannel": t.uint8_t,
        },
    ),
    "gpepIncomingMessageHandler": (
        0x00C5,
        {},
        {
            "status": t.sl_GpStatus,
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
