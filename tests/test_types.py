import pytest
import zigpy.zdo.types as zdo_t

import bellows.types as t


def test_lvbytes32():
    d, r = t.LVBytes32.deserialize(b"\x04\x00\x00\x0012345")
    assert r == b"5"
    assert d == b"1234"

    assert t.LVBytes32.serialize(d) == b"\x04\x00\x00\x001234"


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
