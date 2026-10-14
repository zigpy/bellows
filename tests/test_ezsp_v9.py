from unittest.mock import AsyncMock, MagicMock, call, patch

import pytest

import bellows.ezsp.v9
import bellows.types as t

from tests.common import mock_ezsp_commands


@pytest.fixture
def ezsp_f():
    """EZSP v9 protocol handler."""
    ezsp = bellows.ezsp.v9.EZSPv9(MagicMock(), MagicMock())
    mock_ezsp_commands(ezsp)

    return ezsp


def test_ezsp_frame(ezsp_f):
    ezsp_f._seq = 0x22
    data = ezsp_f._ezsp_frame("version", 8)
    assert data == b"\x22\x00\x01\x00\x00\x08"


def test_ezsp_frame_rx(ezsp_f):
    """Test receiving a version frame."""
    ezsp_f(b"\x01\x01\x80\x00\x00\x01\x02\x34\x12")
    assert ezsp_f._handle_callback.call_count == 1
    assert ezsp_f._handle_callback.call_args[0][0] == "version"
    assert ezsp_f._handle_callback.call_args[0][1] == [0x01, 0x02, 0x1234]


async def test_pre_permit(ezsp_f):
    """Test pre permit."""
    p1 = patch.object(ezsp_f, "setPolicy", new=AsyncMock())
    p2 = patch.object(
        ezsp_f,
        "addTransientLinkKey",
        new=AsyncMock(return_value=[t.EmberStatus.SUCCESS]),
    )
    with p1 as pre_permit_mock, p2 as tclk_mock:
        await ezsp_f.pre_permit(-1.9)
    assert pre_permit_mock.await_count == 2
    assert tclk_mock.await_count == 1


async def test_write_child_data(ezsp_f) -> None:
    ezsp_f.setChildData.return_value = [t.EmberStatus.SUCCESS]

    await ezsp_f.write_child_data(
        {
            t.EUI64.convert("00:0b:57:ff:fe:2b:d4:57"): 0xC06B,
            t.EUI64.convert("00:18:4b:00:1c:a1:b8:46"): 0x1234,
        }
    )

    assert ezsp_f.setChildData.mock_calls == [
        call(
            index=0,
            child_data=t.EmberChildDataV7(
                eui64=t.EUI64.convert("00:0b:57:ff:fe:2b:d4:57"),
                type=t.EmberNodeType.SLEEPY_END_DEVICE,
                id=0xC06B,
                phy=0,
                power=0,
                timeout=0,
            ),
        ),
        call(
            index=1,
            child_data=t.EmberChildDataV7(
                eui64=t.EUI64.convert("00:18:4b:00:1c:a1:b8:46"),
                type=t.EmberNodeType.SLEEPY_END_DEVICE,
                id=0x1234,
                phy=0,
                power=0,
                timeout=0,
            ),
        ),
    ]


async def test_source_route(ezsp_f) -> None:
    ezsp_f.setSourceRoute.return_value = (t.EmberStatus.SUCCESS,)

    status = await ezsp_f.set_source_route(nwk=0x1234, relays=[0x5678, 0xABCD])
    assert status == t.sl_Status.OK

    # Nothing happens
    assert ezsp_f.setSourceRoute.mock_calls == []


@pytest.mark.parametrize(
    ("payload", "src_id"),
    [
        # EnOcean PTM 215Z: commissioning, then presses
        (
            "7cdf1b00e61c7701e61c77010000000000ffffffffe0ffffffffff2e02c5f210405e0513cb"
            "556a00ee94019ee66218118edec91b03000004111011121314151617226062636465666768",
            0x01771CE6,
        ),
        ("7fe11c00e61c7701e61c770100020100001c03000068e3ff0356ff00", 0x01771CE6),
        ("7fe11d00e61c7701e61c770100020100001d03000012be6d0773ff00", 0x01771CE6),
        ("7fe22500e61c7701e61c770100020100002503000064b4e65552ff00", 0x01771CE6),
        # Moes 3-gang switch: commissioning, then encrypted presses
        (
            "7cdc7400425374f3425374f30000000000ffffffffe0ffffffffff2b0289f3a86f2ed35956"
            "0f929469d868472c2639e1be6d66741a00007165726837706f78404750303030318e",
            0xF3745342,
        ),
        ("7fe97d00425374f3425374f300030100007d1a000045dc3f907bff00", 0xF3745342),
        ("7fe98600425374f3425374f30003010000861a000088f258ed78ff00", 0xF3745342),
    ],
)
def test_gpep_incoming_frame(payload: str, src_id: int, ezsp_f) -> None:
    """Parse incoming GP frames."""
    ezsp_frame = (
        bytes([0x42, 0x00, 0x01])  # seq + control bytes
        + t.uint16_t(0x00C5).serialize()  # frame_id LE
        + bytes.fromhex(payload)
    )

    ezsp_f(ezsp_frame)

    [(name, args, *_)] = [c.args for c in ezsp_f._handle_callback.mock_calls]
    assert name == "gpepIncomingMessageHandler"
    assert args[3].source_id == src_id
