import enum
from typing import Callable, TypeVar

CALLABLE_T = TypeVar("CALLABLE_T", bound=Callable)  # pylint: disable=invalid-name


class int_t(int):  # noqa: N801
    _signed = True

    def serialize(self):
        return self.to_bytes(self._size, "little", signed=self._signed)

    @classmethod
    def deserialize(cls, data):
        # Work around https://bugs.python.org/issue23640
        r = cls(int.from_bytes(data[: cls._size], "little", signed=cls._signed))
        data = data[cls._size :]
        return r, data


class int8s(int_t):  # noqa: N801
    _size = 1


class int16s(int_t):  # noqa: N801
    _size = 2


class int24s(int_t):  # noqa: N801
    _size = 3


class int32s(int_t):  # noqa: N801
    _size = 4


class int40s(int_t):  # noqa: N801
    _size = 5


class int48s(int_t):  # noqa: N801
    _size = 6


class int56s(int_t):  # noqa: N801
    _size = 7


class int64s(int_t):  # noqa: N801
    _size = 8


class uint_t(int_t):  # noqa: N801
    _signed = False


class uint8_t(uint_t):  # noqa: N801
    _size = 1


class uint16_t(uint_t):  # noqa: N801
    _size = 2


class uint24_t(uint_t):  # noqa: N801
    _size = 3


class uint32_t(uint_t):  # noqa: N801
    _size = 4


class uint40_t(uint_t):  # noqa: N801
    _size = 5


class uint48_t(uint_t):  # noqa: N801
    _size = 6


class uint56_t(uint_t):  # noqa: N801
    _size = 7


class uint64_t(uint_t):  # noqa: N801
    _size = 8


class LVBytes(bytes):
    def serialize(self):
        return bytes([len(self)]) + self

    @classmethod
    def deserialize(cls, data):
        bytes = int.from_bytes(data[:1], "little")
        s = data[1 : bytes + 1]
        return s, data[bytes + 1 :]


class _List(list):
    _length = None

    def serialize(self):
        assert self._length is None or len(self) == self._length
        return b"".join([self._itemtype(i).serialize() for i in self])

    @classmethod
    def deserialize(cls, data):
        r = cls()
        while data:
            item, data = r._itemtype.deserialize(data)
            r.append(item)
        return r, data


class _LVList(_List):
    def serialize(self):
        head = len(self).to_bytes(1, "little")
        data = super().serialize()
        return head + data

    @classmethod
    def deserialize(cls, data):
        r = cls()
        length, data = data[0], data[1:]
        for i in range(length):
            item, data = r._itemtype.deserialize(data)
            r.append(item)
        return r, data


def List(itemtype):  # noqa: N802
    class List(_List):
        _itemtype = itemtype

    return List


def LVList(itemtype):  # noqa: N802
    class LVList(_LVList):
        _itemtype = itemtype

    return LVList


class _FixedList(_List):
    @classmethod
    def deserialize(cls, data):
        r = cls()
        for i in range(r._length):
            item, data = r._itemtype.deserialize(data)
            r.append(item)
        return r, data


def fixed_list(length, itemtype):
    class FixedList(_FixedList):
        _length = length
        _itemtype = itemtype

    return FixedList


class HexRepr:
    _hex_len = 2

    def __repr__(self):
        return ("0x{:0" + str(self._hex_len) + "x}").format(self)

    def __str__(self):
        return ("0x{:0" + str(self._hex_len) + "x}").format(self)


def bitmap_factory(int_type: CALLABLE_T = uint8_t) -> CALLABLE_T:
    """Bitmap factory."""

    class _NewBitmap(enum.IntFlag):
        def serialize(self):
            """Serialize enum."""
            return int_type(self.value).serialize()

        @classmethod
        def deserialize(cls, data: bytes) -> (bytes, bytes):
            """Deserialize data."""
            val, data = int_type.deserialize(data)
            return cls(val), data

    return _NewBitmap


class bitmap8(bitmap_factory(uint8_t)):  # noqa: N801
    """8 bit bitmap class."""


class bitmap16(bitmap_factory(uint16_t)):  # noqa: N801
    """16 bit bitmap class."""


class _IntEnumMeta(enum.EnumMeta):
    def __call__(cls, value, names=None, *args, **kwargs):  # noqa: N805
        if isinstance(value, str) and value.startswith("0x"):
            value = int(value, base=16)
        else:
            value = int(value)
        return super().__call__(value, names, *args, **kwargs)


def enum_factory(int_type: CALLABLE_T, undefined: str = "undefined") -> CALLABLE_T:
    """Enum factory."""

    class _NewEnum(enum.IntEnum, metaclass=_IntEnumMeta):
        def serialize(self):
            """Serialize enum."""
            return int_type(self.value).serialize()

        @classmethod
        def deserialize(cls, data: bytes) -> (bytes, bytes):
            """Deserialize data."""
            val, data = int_type.deserialize(data)
            return cls(val), data

        @classmethod
        def _missing_(cls, value):
            new = int_type.__new__(cls, value)
            name = f"{undefined}_0x{{:0{int_type._size * 2}x}}"  # pylint: disable=protected-access
            new._name_ = name.format(value)
            new._value_ = value
            return new

    return _NewEnum


class enum8(enum_factory(uint8_t)):  # noqa: N801
    pass


class enum16(enum_factory(uint16_t)):  # noqa: N801
    pass


class enum32(enum_factory(uint16_t)):  # noqa: N801
    pass
