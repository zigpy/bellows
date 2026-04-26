import bellows.types as t

from ..v14.commands import COMMANDS as COMMANDS_v14

COMMANDS = {
    **COMMANDS_v14,
    # v16 appends an SlRxPacketInfo trailer to the v13/v14 layout.
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
