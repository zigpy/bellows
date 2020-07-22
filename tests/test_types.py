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
    ser = b"\x00\x01\x02\x03\x04\x05\x06\x07"
    eui64, data = t.EmberEUI64.deserialize(ser)
    assert data == b""
    assert eui64.serialize() == ser


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
