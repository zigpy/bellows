from zigpy.types import Struct, StructField

from bellows.ezsp.v8.commands import COMMANDS as COMMANDS_v8
import bellows.types as t


class GetTokenDataRsp(Struct):
    status: t.EmberStatus
    value: t.LVBytes32 = StructField(
        requires=lambda rsp: rsp.status == t.EmberStatus.SUCCESS
    )


COMMANDS = {
    **COMMANDS_v8,
    "setChildData": (
        0x00AC,
        {
            "index": t.uint8_t,
            "child_data": t.EmberChildDataV7,
        },
        {
            "status": t.EmberStatus,
        },
    ),
    "setNeighborFrameCounter": (
        0x00AD,
        {
            "eui64": t.EUI64,
            "frame_counter": t.uint32_t,
        },
        {
            "status": t.EmberStatus,
        },
    ),
    "setRadioIeee802154CcaMode": (
        0x0095,
        {
            "cca_mode": t.uint8_t,
        },
        {
            "status": t.EmberStatus,
        },
    ),
    # 18 Token Interface Frames
    "getTokenCount": (
        0x0100,
        {},
        {
            "count": t.uint8_t,
        },
    ),
    "getTokenInfo": (
        0x0101,
        {
            "index": t.uint8_t,
        },
        {
            "status": t.EmberStatus,
            "token_info": t.EmberTokenInfo,
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
    "setTokenData": (
        0x0103,
        {
            "token": t.uint32_t,
            "index": t.uint32_t,
            "token_data": t.LVBytes32,
        },
        {
            "status": t.EmberStatus,
        },
    ),
    "resetNode": (
        0x0104,
        {},
        {},
    ),
}

del COMMANDS["setGpioCurrentConfiguration"]
del COMMANDS["setGpioPowerUpDownConfiguration"]
del COMMANDS["overrideCurrentChannel"]
