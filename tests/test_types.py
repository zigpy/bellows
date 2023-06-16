import pytest
import zigpy.zdo.types as zdo_t

import bellows.types as t


def test_basic():
    assert t.uint8_t.deserialize(b"\x08") == (8, b"")


def test_extra_data():
    assert t.uint8_t.deserialize(b"\x08extra") == (8, b"extra")


def test_multibyte():
    assert t.uint16_t.deserialize(b"\x08\x01") == (0x0108, b"")


def test_lvbytes():
    d, r = t.LVBytes.deserialize(b"\x0412345")
    assert r == b"5"
    assert d == b"1234"

    assert t.LVBytes.serialize(d) == b"\x041234"

    with pytest.raises(ValueError):
        t.LVBytes.deserialize(b"\x04123")


def test_lvbytes32():
    d, r = t.LVBytes32.deserialize(b"\x04\x00\x00\x0012345")
    assert r == b"5"
    assert d == b"1234"

    assert t.LVBytes32.serialize(d) == b"\x04\x00\x00\x001234"


def test_lvlist():
    d, r = t.LVList(t.uint8_t).deserialize(b"\x0412345")
    assert r == b"5"
    assert d == list(map(ord, "1234"))
    assert t.LVList(t.uint8_t).serialize(d) == b"\x041234"


def test_list():
    expected = list(map(ord, "\x0123"))
    assert t.List(t.uint8_t).deserialize(b"\x0123") == (expected, b"")


def test_struct():
    class TestStruct(t.EzspStruct):
        a: t.uint8_t
        b: t.uint8_t

        @property
        def test(self):
            return None

    ts = TestStruct()
    ts.a = t.uint8_t(0xAA)
    ts.b = t.uint8_t(0xBB)
    ts2 = TestStruct(ts)
    assert ts2.a == ts.a
    assert ts2.b == ts.b

    r = repr(ts)
    assert "TestStruct" in r
    assert r.startswith("TestStruct") and r.endswith(")")

    s = ts2.serialize()
    assert s == b"\xaa\xbb"


def test_str():
    assert str(t.EzspStatus.deserialize(b"\0")[0]) == "EzspStatus.SUCCESS"


def test_ember_eui64():
    serialized = b"\x00\x01\x02\x03\x04\x05\x06\x07"
    eui64, data = t.EmberEUI64.deserialize(serialized)
    assert data == b""
    assert eui64.serialize() == serialized


def test_hex_repr():
    class NwkAsHex(t.HexRepr, t.uint16_t):
        _hex_len = 4

    nwk = NwkAsHex(0x1234)
    assert str(nwk) == "0x1234"
    assert repr(nwk) == "0x1234"


def test_bitmap():
    """Test bitmaps."""

    class TestBitmap(t.bitmap16):
        CH_1 = 0x0010
        CH_2 = 0x0020
        CH_3 = 0x0040
        CH_4 = 0x0080
        ALL = 0x00F0

    extra = b"extra data\xaa\55"
    data = b"\xf0\x00"
    r, rest = TestBitmap.deserialize(data + extra)
    assert rest == extra
    assert r is TestBitmap.ALL
    assert r.name == "ALL"
    assert r.value == 0x00F0
    assert r.serialize() == data

    data = b"\x60\x00"
    r, rest = TestBitmap.deserialize(data + extra)
    assert rest == extra
    assert TestBitmap.CH_1 not in r
    assert TestBitmap.CH_2 in r
    assert TestBitmap.CH_3 in r
    assert TestBitmap.CH_4 not in r
    assert TestBitmap.ALL not in r
    assert r.value == 0x0060
    assert r.serialize() == data


def test_bitmap_undef():
    """Test bitmaps with some undefined flags."""

    class TestBitmap(t.bitmap16):
        CH_1 = 0x0010
        CH_2 = 0x0020
        CH_3 = 0x0040
        CH_4 = 0x0080
        ALL = 0x00F0

    extra = b"extra data\xaa\55"
    data = b"\x60\x0f"
    r, rest = TestBitmap.deserialize(data + extra)
    assert rest == extra
    assert TestBitmap.CH_1 not in r
    assert TestBitmap.CH_2 in r
    assert TestBitmap.CH_3 in r
    assert TestBitmap.CH_4 not in r
    assert TestBitmap.ALL not in r
    assert r.value == 0x0F60
    assert r.serialize() == data


def test_enum_undef():
    class TestEnum(t.enum8):
        ALL = 0xAA

    data = b"\x55"
    extra = b"extra"

    r, rest = TestEnum.deserialize(data + extra)
    assert rest == extra
    assert r == 0x55
    assert r.value == 0x55
    assert r.name == "undefined_0x55"
    assert r.serialize() == data
    assert isinstance(r, TestEnum)

    r = TestEnum("85")
    assert r == 0x55
    assert r.value == 0x55
    assert r.name == "undefined_0x55"
    assert r.serialize() == data
    assert isinstance(r, TestEnum)

    r = TestEnum("0x55")
    assert r == 0x55
    assert r.value == 0x55
    assert r.name == "undefined_0x55"
    assert r.serialize() == data
    assert isinstance(r, TestEnum)


def test_enum():
    class TestEnum(t.enum8):
        ALL = 0x55
        ERR = 1

    data = b"\x55"
    extra = b"extra"

    r, rest = TestEnum.deserialize(data + extra)
    assert rest == extra
    assert r == 0x55
    assert r.value == 0x55
    assert r.name == "ALL"
    assert isinstance(r, TestEnum)
    assert TestEnum.ALL + TestEnum.ERR == 0x56

    r = TestEnum("85")
    assert r == 0x55
    assert r.value == 0x55
    assert r.name == "ALL"
    assert isinstance(r, TestEnum)
    assert TestEnum.ALL + TestEnum.ERR == 0x56

    r = TestEnum("0x55")
    assert r == 0x55
    assert r.value == 0x55
    assert r.name == "ALL"
    assert isinstance(r, TestEnum)
    assert TestEnum.ALL + TestEnum.ERR == 0x56


def test_fixed_list():
    list_type = t.fixed_list(2, t.uint8_t)
    data = b"\x01\xFE"
    extra = b"extarlist \xaa\55"

    res, rest = list_type.deserialize(data + extra)
    assert rest == extra
    assert res == [1, 254]


@pytest.mark.parametrize(
    "node_type, logical_type",
    (
        (0, 7),
        (1, 0),
        (2, 1),
        (3, 2),
        (4, 7),
        (0xFF, 7),
    ),
)
def test_ember_node_type_to_zdo_logical_type(node_type, logical_type):
    """Test conversion of node type to logical type."""

    node_type = t.EmberNodeType(node_type)
    assert node_type.zdo_logical_type == zdo_t.LogicalType(logical_type)
