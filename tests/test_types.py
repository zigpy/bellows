import bellows.types as t


def test_basic():
    assert t.uint8_t.deserialize(b'\x08') == (8, b'')


def test_extra_data():
    assert t.uint8_t.deserialize(b'\x08extra') == (8, b'extra')


def test_multibyte():
    assert t.uint16_t.deserialize(b'\x08\x01') == (0x0108, b'')


def test_lvbytes():
    d, r = t.LVBytes.deserialize(b'\x0412345')
    assert r == b'5'
    assert d == b'1234'

    assert t.LVBytes.serialize(d) == b'\x041234'


def test_lvlist():
    d, r = t.LVList(t.uint8_t).deserialize(b'\x0412345')
    assert r == b'5'
    assert d == list(map(ord, '1234'))
    assert t.LVList(t.uint8_t).serialize(d) == b'\x041234'


def test_list():
    expected = list(map(ord, '\x0123'))
    assert t.List(t.uint8_t).deserialize(b'\x0123') == (expected, b'')


def test_struct():
    class TestStruct(t.EzspStruct):
        _fields = [('a', t.uint8_t), ('b', t.uint8_t)]

    ts = TestStruct()
    ts.a = t.uint8_t(0xaa)
    ts.b = t.uint8_t(0xbb)
    ts2 = TestStruct(ts)
    assert ts2.a == ts.a
    assert ts2.b == ts.b

    r = repr(ts)
    assert 'TestStruct' in r
    assert r.startswith('<') and r.endswith('>')

    s = ts2.serialize()
    assert s == b'\xaa\xbb'


def test_str():
    assert str(t.EzspStatus.deserialize(b'\0')[0]) == 'EzspStatus.SUCCESS'


def test_ember_eui64():
    ser = b'\x00\x01\x02\x03\x04\x05\x06\x07'
    eui64, data = t.EmberEUI64.deserialize(ser)
    assert data == b''
    assert eui64.serialize() == ser
