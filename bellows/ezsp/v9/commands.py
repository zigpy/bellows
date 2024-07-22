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
        tuple(
            {
                "index": t.uint8_t,
                "child_data": t.EmberChildDataV7,
            }.values()
        ),
        tuple(
            {
                "status": t.EmberStatus,
            }.values()
        ),
    ),
    "setNeighborFrameCounter": (
        0x00AD,
        tuple(
            {
                "eui64": t.EUI64,
                "frame_counter": t.uint32_t,
            }.values()
        ),
        tuple(
            {
                "status": t.EmberStatus,
            }.values()
        ),
    ),
    "setRadioIeee802154CcaMode": (
        0x0095,
        tuple(
            {
                "cca_mode": t.uint8_t,
            }.values()
        ),
        tuple(
            {
                "status": t.EmberStatus,
            }.values()
        ),
    ),
    # 18 Token Interface Frames
    "getTokenCount": (
        0x0100,
        tuple({}.values()),
        tuple(
            {
                "count": t.uint8_t,
            }.values()
        ),
    ),
    "getTokenInfo": (
        0x0101,
        tuple(
            {
                "index": t.uint8_t,
            }.values()
        ),
        tuple(
            {
                "status": t.EmberStatus,
                "token_info": t.EmberTokenInfo,
            }.values()
        ),
    ),
    "getTokenData": (
        0x0102,
        tuple(
            {
                "token": t.uint32_t,
                "index": t.uint32_t,
            }.values()
        ),
        GetTokenDataRsp,
    ),
    "setTokenData": (
        0x0103,
        tuple(
            {
                "token": t.uint32_t,
                "index": t.uint32_t,
                "token_data": t.LVBytes32,
            }.values()
        ),
        tuple(
            {
                "status": t.EmberStatus,
            }.values()
        ),
    ),
    "resetNode": (
        0x0104,
        tuple({}.values()),
        tuple({}.values()),
    ),
}

del COMMANDS["setGpioCurrentConfiguration"]
del COMMANDS["setGpioPowerUpDownConfiguration"]
del COMMANDS["overrideCurrentChannel"]
