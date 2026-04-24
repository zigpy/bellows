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


def test_ember_gp_address_source_id():
    """In SrcID mode (applicationId == 0) the first 4 bytes are the 32-bit ID.

    The remaining 4 bytes of the 8-byte union are padding per the GP spec.
    """
    addr = t.EmberGpAddress(
        applicationId=t.uint8_t(0),
        id=t.FixedList[t.uint8_t, 8](b"\x86\xf8\x71\x01" + b"\x00" * 4),
        endpoint=t.uint8_t(0),
    )
    assert addr.source_id == 0x0171F886


def test_ember_gp_address_gpd_ieee_address():
    """In IEEE mode (applicationId == 2) the full 8 bytes form the EUI64.

    Covers the ``gpd_ieee_address`` property used when the GP stack gets an
    IEEE-addressed frame. bellows' dispatcher currently drops these frames
    without touching the property, so this is the only place the accessor
    is exercised.
    """
    raw = b"\x11\x22\x33\x44\x55\x66\x77\x88"
    addr = t.EmberGpAddress(
        applicationId=t.uint8_t(2),
        id=t.FixedList[t.uint8_t, 8](raw),
        endpoint=t.uint8_t(3),
    )
    assert addr.gpd_ieee_address == t.EUI64(raw)
