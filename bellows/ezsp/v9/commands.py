from zigpy.types import Struct, StructField

from bellows.ezsp.v8.commands import COMMANDS as COMMANDS_v8

from . import types as t


class GetTokenDataRsp(Struct):
    status: t.EmberStatus
    value: t.LVBytes32 = StructField(
        requires=lambda rsp: rsp.status == t.EmberStatus.SUCCESS
    )


COMMANDS = {
    **COMMANDS_v8,
    "setChildData": (
        0x00AC,
        (t.uint8_t, t.EmberChildData),
        (t.EmberStatus,),
    ),
    "setNeighborFrameCounter": (0x00AD, (t.EUI64,), (t.EmberStatus, t.uint32_t)),
    "setRadioIeee802154CcaMode": (0x0095, (t.uint8_t,), (t.EmberStatus,)),
    # 18 Token Interface Frames
    "getTokenCount": (0x0100, (), (t.uint8_t,)),
    "getTokenInfo": (0x0101, (t.uint8_t,), (t.EmberStatus, t.EmberTokenInfo)),
    "getTokenData": (
        0x0102,
        (t.uint32_t, t.uint32_t),
        GetTokenDataRsp,
    ),
    "setTokenData": (
        0x0103,
        (t.uint32_t, t.uint32_t, t.LVBytes32),
        (t.EmberStatus,),
    ),
    "resetNode": (0x0104, (), ()),
}

del COMMANDS["setGpioCurrentConfiguration"]
del COMMANDS["setGpioPowerUpDownConfiguration"]
del COMMANDS["overrideCurrentChannel"]
