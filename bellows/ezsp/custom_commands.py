"""Custom EZSP commands."""

import zigpy.types as t


class CustomCommand(t.enum8):
    CMD_GET_SUPPORTED_FEATURES = 0x00


class FirmwareFeatures(t.bitmap32):
    # The firmware passes through all group traffic, regardless of group membership
    MEMBER_OF_ALL_GROUPS = 0b00000000_00000000_00000000_00000001
