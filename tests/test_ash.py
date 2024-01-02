from bellows.ash import PSEUDO_RANDOM_DATA_SEQUENCE, AshProtocol


def test_stuffing():
    assert AshProtocol._stuff_bytes(b"\x7E") == b"\x7D\x5E"
    assert AshProtocol._stuff_bytes(b"\x11") == b"\x7D\x31"
    assert AshProtocol._stuff_bytes(b"\x13") == b"\x7D\x33"
    assert AshProtocol._stuff_bytes(b"\x18") == b"\x7D\x38"
    assert AshProtocol._stuff_bytes(b"\x1A") == b"\x7D\x3A"
    assert AshProtocol._stuff_bytes(b"\x7D") == b"\x7D\x5D"

    assert AshProtocol._unstuff_bytes(b"\x7D\x5E") == b"\x7E"
    assert AshProtocol._unstuff_bytes(b"\x7D\x31") == b"\x11"
    assert AshProtocol._unstuff_bytes(b"\x7D\x33") == b"\x13"
    assert AshProtocol._unstuff_bytes(b"\x7D\x38") == b"\x18"
    assert AshProtocol._unstuff_bytes(b"\x7D\x3A") == b"\x1A"
    assert AshProtocol._unstuff_bytes(b"\x7D\x5D") == b"\x7D"


def test_pseudo_random_data_sequence():
    assert PSEUDO_RANDOM_DATA_SEQUENCE.startswith(b"\x42\x21\xA8\x54\x2A")
