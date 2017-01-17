import bellows.types as t


def test_basic():
    assert t.uint8_t.deserialize(b'\x08') == (8, b'')


def test_extra_data():
    assert t.uint8_t.deserialize(b'\x08extra') == (8, b'extra')


def test_multibyte():
    assert t.uint16_t.deserialize(b'\x08\x01') == (0x0108, b'')


def test_length_value_string():
    assert t.LVString.deserialize(b'\x0412345') == (b'1234', b'5')
