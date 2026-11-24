from unittest.mock import MagicMock, call

import pytest
import zigpy.state

from bellows.exception import InvalidCommandError
import bellows.ezsp.v6
import bellows.types as t

from tests.common import mock_ezsp_commands


@pytest.fixture
def ezsp_f():
    """EZSP v6 protocol handler."""
    ezsp = bellows.ezsp.v6.EZSPv6(MagicMock(), MagicMock())
    mock_ezsp_commands(ezsp)

    return ezsp


def test_ezsp_frame(ezsp_f):
    ezsp_f._seq = 0x22
    data = ezsp_f._ezsp_frame("version", 6)
    assert data == b"\x22\x00\xff\x00\x00\x06"


def test_ezsp_frame_rx(ezsp_f):
    """Test receiving a version frame."""
    ezsp_f(b"\x01\x00\xff\x00\x00\x01\x02\x34\x12")
    assert ezsp_f._handle_callback.call_count == 1
    assert ezsp_f._handle_callback.call_args[0][0] == "version"
    assert ezsp_f._handle_callback.call_args[0][1] == [0x01, 0x02, 0x1234]


async def test_initialize_network(ezsp_f) -> None:
    ezsp_f.networkInit.return_value = (t.EmberStatus.SUCCESS,)
    assert await ezsp_f.initialize_network() == t.sl_Status.OK
    assert ezsp_f.networkInit.mock_calls == [
        call(networkInitBitmask=t.EmberNetworkInitBitmask.NETWORK_INIT_NO_OPTIONS)
    ]


async def test_send_multicast_with_alias(ezsp_f) -> None:
    ezsp_f.sendMulticastWithAlias.return_value = (t.EmberStatus.SUCCESS, 0x42)
    status, message_tag = await ezsp_f.send_multicast(
        aps_frame=t.EmberApsFrame(),
        radius=12,
        non_member_radius=34,
        message_tag=0x42,
        data=b"hello",
        alias=t.NWK(0xABCD),
        alias_seq=t.uint8_t(0x56),
    )

    assert status == t.sl_Status.OK
    assert message_tag == 0x42
    assert len(ezsp_f.sendMulticast.mock_calls) == 0
    assert ezsp_f.sendMulticastWithAlias.mock_calls == [
        call(
            apsFrame=t.EmberApsFrame(),
            hops=12,
            nonmemberRadius=34,
            alias=0xABCD,
            nwkSequence=0x56,
            messageTag=0x42,
            messageContents=b"hello",
        )
    ]


async def test_send_multicast_without_alias(ezsp_f) -> None:
    ezsp_f.sendMulticast.return_value = (t.EmberStatus.SUCCESS, 0x42)
    status, message_tag = await ezsp_f.send_multicast(
        aps_frame=t.EmberApsFrame(),
        radius=12,
        non_member_radius=34,
        message_tag=0x42,
        data=b"hello",
    )

    assert status == t.sl_Status.OK
    assert message_tag == 0x42
    assert len(ezsp_f.sendMulticastWithAlias.mock_calls) == 0
    assert len(ezsp_f.sendMulticast.mock_calls) == 1


async def test_clear_gp_tables(ezsp_f) -> None:
    """Only the sink table has a bulk clear before EZSPv17."""
    ezsp_f.gpClearSinkTable.return_value = []

    await ezsp_f.clear_gp_tables()

    assert ezsp_f.gpClearSinkTable.mock_calls == [call()]


async def test_clear_gp_tables_unsupported(ezsp_f, caplog) -> None:
    """An NCP built without Green Power rejects the command."""
    ezsp_f.gpClearSinkTable.side_effect = InvalidCommandError("No GP")

    await ezsp_f.clear_gp_tables()

    assert "no Green Power sink table" in caplog.text
