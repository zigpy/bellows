"""Custom EZSP commands."""
from __future__ import annotations

import zigpy.types as t


class Bytes(bytes):
    def serialize(self) -> Bytes:
        return self

    @classmethod
    def deserialize(cls, data: bytes) -> tuple[Bytes, bytes]:
        return cls(data), b""

    def __repr__(self) -> str:
        # Reading byte sequences like \x200\x21 is extremely annoying
        # compared to \x20\x30\x21
        escaped = "".join(f"\\x{b:02X}" for b in self)

        return f"b'{escaped}'"

    __str__ = __repr__


class CustomCommandId(t.enum16):
    CMD_GET_PROTOCOL_VERSION_REQ = 0x0000
    CMD_GET_PROTOCOL_VERSION_RSP = 0x8000

    CMD_GET_SUPPORTED_FEATURES_REQ = 0x0001
    CMD_GET_SUPPORTED_FEATURES_RSP = 0x8001


class CustomCommand(t.Struct):
    command_id: CustomCommandId
    payload: Bytes


class FirmwareFeatures(t.bitmap32):
    NONE = 0

    # The firmware passes through all group traffic, regardless of group membership
    MEMBER_OF_ALL_GROUPS = 1 << 0


class GetSupportedFeaturesReq(t.Struct):
    pass


class GetSupportedFeaturesRsp(t.Struct):
    features: FirmwareFeatures
