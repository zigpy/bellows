from __future__ import annotations

from zigpy.types import (  # noqa: F401
    FixedList,
    List,
    LVBytes,
    LVList,
    bitmap8,
    bitmap16,
    enum8,
    enum16,
    enum32,
    int8s,
    int16s,
    int24s,
    int32s,
    int40s,
    int48s,
    int56s,
    int64s,
    uint8_t,
    uint16_t,
    uint24_t,
    uint32_t,
    uint40_t,
    uint48_t,
    uint56_t,
    uint64_t,
    uint_t,
)


class LVBytes32(LVBytes):
    _prefix_length = 4


class uint128_t(uint_t, bits=128):
    pass
