from unittest.mock import MagicMock, call

import pytest
import zigpy.state

import bellows.ezsp.v5
import bellows.types as t

from tests.common import mock_ezsp_commands


@pytest.fixture
def ezsp_f():
    """EZSP v5 protocol handler."""
    ezsp = bellows.ezsp.v5.EZSPv5(MagicMock(), MagicMock())
    mock_ezsp_commands(ezsp)

    return ezsp


def test_ezsp_frame(ezsp_f):
    ezsp_f._seq = 0x22
    data = ezsp_f._ezsp_frame("version", 5)
    assert data == b"\x22\x00\xff\x00\x00\x05"


def test_ezsp_frame_rx(ezsp_f):
    """Test receiving a version frame."""
    ezsp_f(b"\x01\x00\xff\x00\x00\x01\x02\x34\x12")
    assert ezsp_f._handle_callback.call_count == 1
    assert ezsp_f._handle_callback.call_args[0][0] == "version"
    assert ezsp_f._handle_callback.call_args[0][1] == [0x01, 0x02, 0x1234]


async def test_pre_permit(ezsp_f):
    """Test pre permit."""
    ezsp_f.addTransientLinkKey.return_value = [t.EmberStatus.SUCCESS]
    await ezsp_f.pre_permit(1)

    assert ezsp_f.addTransientLinkKey.mock_calls == [
        call(
            partner=t.EUI64.convert("ff:ff:ff:ff:ff:ff:ff:ff"),
            transientKey=t.KeyData(b"ZigBeeAlliance09"),
        )
    ]


async def test_read_address_table(ezsp_f):
    def get_addr_table_node_id(addressTableIndex):
        return (
            {
                16: t.EmberNodeId(0x44CB),
                17: t.EmberNodeId(0x0702),
                18: t.EmberNodeId(0x0000),  # bogus entry
            }.get(addressTableIndex, t.EmberNodeId(0xFFFF)),
        )

    ezsp_f.getAddressTableRemoteNodeId.side_effect = get_addr_table_node_id

    def get_addr_table_eui64(addressTableIndex):
        if addressTableIndex < 16:
            return (t.EUI64.convert("ff:ff:ff:ff:ff:ff:ff:ff"),)
        elif 16 <= addressTableIndex <= 18:
            return (
                {
                    16: t.EUI64.convert("cc:cc:cc:ff:fe:e6:8e:ca"),
                    17: t.EUI64.convert("ec:1b:bd:ff:fe:2f:41:a4"),
                    18: t.EUI64.convert("00:00:00:00:00:00:00:00"),
                }[addressTableIndex],
            )
        else:
            return (t.EUI64.convert("00:00:00:00:00:00:00:00"),)

    ezsp_f.getConfigurationValue.return_value = (t.EmberStatus.SUCCESS, 20)
    ezsp_f.getAddressTableRemoteEui64.side_effect = get_addr_table_eui64

    address_table = [key async for key in ezsp_f.read_address_table()]
    assert address_table == [
        (0x44CB, t.EUI64.convert("cc:cc:cc:ff:fe:e6:8e:ca")),
        (0x0702, t.EUI64.convert("ec:1b:bd:ff:fe:2f:41:a4")),
    ]


async def test_write_nwk_frame_counter(ezsp_f) -> None:
    ezsp_f.networkState.return_value = (t.EmberNetworkStatus.NO_NETWORK,)
    ezsp_f.setValue.return_value = (t.EmberStatus.SUCCESS,)
    await ezsp_f.write_nwk_frame_counter(12345678)

    assert ezsp_f.setValue.mock_calls == [
        call(
            valueId=t.EzspValueId.VALUE_NWK_FRAME_COUNTER,
            value=t.uint32_t(12345678).serialize(),
        ),
    ]


async def test_write_aps_frame_counter(ezsp_f) -> None:
    ezsp_f.networkState.return_value = (t.EmberNetworkStatus.NO_NETWORK,)
    ezsp_f.setValue.return_value = (t.EmberStatus.SUCCESS,)
    await ezsp_f.write_aps_frame_counter(12345678)

    assert ezsp_f.setValue.mock_calls == [
        call(
            valueId=t.EzspValueId.VALUE_APS_FRAME_COUNTER,
            value=t.uint32_t(12345678).serialize(),
        ),
    ]
