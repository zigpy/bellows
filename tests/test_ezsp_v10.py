from unittest.mock import AsyncMock, MagicMock, call, patch

import pytest

from bellows.exception import InvalidCommandError
from bellows.ezsp.v9.commands import GetTokenDataRsp
import bellows.ezsp.v10
import bellows.types as t

from tests.common import mock_ezsp_commands


@pytest.fixture
def ezsp_f():
    """EZSP v10 protocol handler."""
    ezsp = bellows.ezsp.v10.EZSPv10(MagicMock(), MagicMock())
    mock_ezsp_commands(ezsp)

    return ezsp


def test_ezsp_frame(ezsp_f):
    ezsp_f._seq = 0x22
    data = ezsp_f._ezsp_frame("version", 10)
    assert data == b"\x22\x00\x01\x00\x00\x0a"


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

    # Mock NVRAM entries with correct flags
    eui64_1 = t.EUI64.convert("00:0b:57:ff:fe:2b:d4:57")
    eui64_2 = t.EUI64.convert("00:18:4b:00:1c:a1:b8:46")

    def mock_get_token_data(token, index):
        if index == 0:
            return GetTokenDataRsp(
                status=t.EmberStatus.SUCCESS,
                value=t.NV3ChildTableEntry(
                    eui64=eui64_1, id=0xC06B, flags=0x80
                ).serialize(),
            )
        elif index == 1:
            return GetTokenDataRsp(
                status=t.EmberStatus.SUCCESS,
                value=t.NV3ChildTableEntry(
                    eui64=eui64_2, id=0x1234, flags=0x80
                ).serialize(),
            )
        else:
            return GetTokenDataRsp(status=t.EmberStatus.ERR_FATAL, value=b"")

    ezsp_f.getTokenData = AsyncMock(side_effect=mock_get_token_data)
    ezsp_f.setTokenData = AsyncMock(return_value=[t.EmberStatus.SUCCESS])

    await ezsp_f.write_child_data({eui64_1: 0xC06B, eui64_2: 0x1234})

    assert ezsp_f.setChildData.mock_calls == [
        call(
            index=0,
            child_data=t.EmberChildDataV10(
                eui64=t.EUI64.convert("00:0b:57:ff:fe:2b:d4:57"),
                type=t.EmberNodeType.SLEEPY_END_DEVICE,
                id=0xC06B,
                phy=0,
                power=0,
                timeout=0,
                timeout_remaining=0,
            ),
        ),
        call(
            index=1,
            child_data=t.EmberChildDataV10(
                eui64=t.EUI64.convert("00:18:4b:00:1c:a1:b8:46"),
                type=t.EmberNodeType.SLEEPY_END_DEVICE,
                id=0x1234,
                phy=0,
                power=0,
                timeout=0,
                timeout_remaining=0,
            ),
        ),
    ]

    assert ezsp_f.getTokenData.mock_calls == [
        call(token=t.NV3KeyId.NVM3KEY_STACK_CHILD_TABLE, index=0),
        call(token=t.NV3KeyId.NVM3KEY_STACK_CHILD_TABLE, index=1),
    ]
    assert ezsp_f.setTokenData.mock_calls == []


async def test_write_child_data_nvram_read_failure(ezsp_f) -> None:
    """Test write_child_data when NVRAM read fails for some entries."""
    ezsp_f.setChildData.return_value = [t.EmberStatus.SUCCESS]

    def mock_get_token_data(token, index):
        if index == 0:
            return GetTokenDataRsp(status=t.EmberStatus.ERR_FATAL, value=b"")
        elif index == 1:
            return GetTokenDataRsp(
                status=t.EmberStatus.SUCCESS,
                value=t.NV3ChildTableEntry(
                    eui64=t.EUI64.convert("00:18:4b:00:1c:a1:b8:46"),
                    id=0x1234,
                    flags=0x80,
                ).serialize(),
            )
        else:
            return GetTokenDataRsp(status=t.EmberStatus.ERR_FATAL, value=b"")

    ezsp_f.getTokenData = AsyncMock(side_effect=mock_get_token_data)
    ezsp_f.setTokenData = AsyncMock(return_value=[t.EmberStatus.SUCCESS])

    await ezsp_f.write_child_data(
        {
            t.EUI64.convert("00:0b:57:ff:fe:2b:d4:57"): 0xC06B,
            t.EUI64.convert("00:18:4b:00:1c:a1:b8:46"): 0x1234,
        }
    )

    assert ezsp_f.getTokenData.mock_calls == [
        call(token=t.NV3KeyId.NVM3KEY_STACK_CHILD_TABLE, index=0),
        call(token=t.NV3KeyId.NVM3KEY_STACK_CHILD_TABLE, index=1),
    ]
    assert ezsp_f.setTokenData.mock_calls == []


async def test_write_child_data_nvram_format_mismatch(ezsp_f) -> None:
    """Test write_child_data when NVRAM format doesn't match expected format."""
    ezsp_f.setChildData.return_value = [t.EmberStatus.SUCCESS]

    ezsp_f.getTokenData = AsyncMock(
        return_value=GetTokenDataRsp(
            status=t.EmberStatus.SUCCESS,
            value=b"\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b",  # Wrong format
        )
    )
    ezsp_f.setTokenData = AsyncMock(return_value=[t.EmberStatus.SUCCESS])

    await ezsp_f.write_child_data({t.EUI64.convert("00:0b:57:ff:fe:2b:d4:57"): 0xC06B})

    assert ezsp_f.getTokenData.mock_calls == [
        call(token=t.NV3KeyId.NVM3KEY_STACK_CHILD_TABLE, index=0)
    ]
    # No setTokenData due to format mismatch
    assert ezsp_f.setTokenData.mock_calls == []


async def test_write_child_data_nvram_flags_correction_needed(ezsp_f) -> None:
    """Test write_child_data when NVRAM flags need correction."""
    ezsp_f.setChildData.return_value = [t.EmberStatus.SUCCESS]

    ezsp_f.getTokenData = AsyncMock(
        return_value=GetTokenDataRsp(
            status=t.EmberStatus.SUCCESS,
            value=t.NV3ChildTableEntry(
                eui64=t.EUI64.convert("00:0b:57:ff:fe:2b:d4:57"), id=0xC06B, flags=0x00
            ).serialize(),
        )
    )
    ezsp_f.setTokenData = AsyncMock(return_value=[t.EmberStatus.SUCCESS])

    await ezsp_f.write_child_data({t.EUI64.convert("00:0b:57:ff:fe:2b:d4:57"): 0xC06B})

    assert ezsp_f.getTokenData.mock_calls == [
        call(token=t.NV3KeyId.NVM3KEY_STACK_CHILD_TABLE, index=0)
    ]

    assert ezsp_f.setTokenData.mock_calls == [
        call(
            token=t.NV3KeyId.NVM3KEY_STACK_CHILD_TABLE,
            index=0,
            token_data=t.NV3ChildTableEntry(
                eui64=t.EUI64.convert("00:0b:57:ff:fe:2b:d4:57"), id=0xC06B, flags=0x80
            ).serialize(),
        )
    ]


async def test_write_child_data_nvram_flags_already_correct(ezsp_f) -> None:
    """Test write_child_data when NVRAM flags are already correct."""
    ezsp_f.setChildData.return_value = [t.EmberStatus.SUCCESS]

    ezsp_f.getTokenData = AsyncMock(
        return_value=GetTokenDataRsp(
            status=t.EmberStatus.SUCCESS,
            value=t.NV3ChildTableEntry(
                eui64=t.EUI64.convert("00:0b:57:ff:fe:2b:d4:57"), id=0xC06B, flags=0x80
            ).serialize(),
        )
    )
    ezsp_f.setTokenData = AsyncMock(return_value=[t.EmberStatus.SUCCESS])

    await ezsp_f.write_child_data({t.EUI64.convert("00:0b:57:ff:fe:2b:d4:57"): 0xC06B})

    assert ezsp_f.getTokenData.mock_calls == [
        call(token=t.NV3KeyId.NVM3KEY_STACK_CHILD_TABLE, index=0)
    ]
    assert ezsp_f.setTokenData.mock_calls == []


async def test_write_child_data_nvram_set_token_failure(ezsp_f) -> None:
    """Test write_child_data when setTokenData fails during flag correction."""
    ezsp_f.setChildData.return_value = [t.EmberStatus.SUCCESS]

    ezsp_f.getTokenData = AsyncMock(
        return_value=GetTokenDataRsp(
            status=t.EmberStatus.SUCCESS,
            value=t.NV3ChildTableEntry(
                eui64=t.EUI64.convert("00:0b:57:ff:fe:2b:d4:57"), id=0xC06B, flags=0x00
            ).serialize(),
        )
    )
    ezsp_f.setTokenData = AsyncMock(return_value=[t.EmberStatus.ERR_FATAL])

    with pytest.raises(AssertionError):
        await ezsp_f.write_child_data(
            {t.EUI64.convert("00:0b:57:ff:fe:2b:d4:57"): 0xC06B}
        )


async def test_write_child_data_multiple_entries_mixed_scenarios(ezsp_f) -> None:
    """Test write_child_data with multiple entries covering various scenarios."""
    ezsp_f.setChildData.return_value = [t.EmberStatus.SUCCESS]

    def mock_get_token_data(token, index):
        if index == 0:  # Read failure
            return GetTokenDataRsp(status=t.EmberStatus.ERR_FATAL, value=b"")
        elif index == 1:  # Needs correction
            return GetTokenDataRsp(
                status=t.EmberStatus.SUCCESS,
                value=t.NV3ChildTableEntry(
                    eui64=t.EUI64.convert("00:18:4b:00:1c:a1:b8:46"),
                    id=0x1234,
                    flags=0x00,
                ).serialize(),
            )
        elif index == 2:  # Already correct
            return GetTokenDataRsp(
                status=t.EmberStatus.SUCCESS,
                value=t.NV3ChildTableEntry(
                    eui64=t.EUI64.convert("00:22:33:44:55:66:77:88"),
                    id=0x5678,
                    flags=0x80,
                ).serialize(),
            )
        return GetTokenDataRsp(status=t.EmberStatus.ERR_FATAL, value=b"")

    ezsp_f.getTokenData = AsyncMock(side_effect=mock_get_token_data)
    ezsp_f.setTokenData = AsyncMock(return_value=[t.EmberStatus.SUCCESS])

    await ezsp_f.write_child_data(
        {
            t.EUI64.convert("00:0b:57:ff:fe:2b:d4:57"): 0xC06B,
            t.EUI64.convert("00:18:4b:00:1c:a1:b8:46"): 0x1234,
            t.EUI64.convert("00:22:33:44:55:66:77:88"): 0x5678,
        }
    )

    assert ezsp_f.getTokenData.mock_calls == [
        call(token=t.NV3KeyId.NVM3KEY_STACK_CHILD_TABLE, index=0),
        call(token=t.NV3KeyId.NVM3KEY_STACK_CHILD_TABLE, index=1),
        call(token=t.NV3KeyId.NVM3KEY_STACK_CHILD_TABLE, index=2),
    ]

    # Only entry 2 needs flag correction
    assert ezsp_f.setTokenData.mock_calls == [
        call(
            token=t.NV3KeyId.NVM3KEY_STACK_CHILD_TABLE,
            index=1,
            token_data=t.NV3ChildTableEntry(
                eui64=t.EUI64.convert("00:18:4b:00:1c:a1:b8:46"), id=0x1234, flags=0x80
            ).serialize(),
        )
    ]


async def test_write_child_data_nv3_interface_unavailable(ezsp_f) -> None:
    """Test write_child_data when NV3 interface is not available."""
    ezsp_f.setChildData.return_value = [t.EmberStatus.SUCCESS]
    ezsp_f.getTokenData = AsyncMock(
        side_effect=InvalidCommandError("NV3 not available")
    )
    ezsp_f.setTokenData = AsyncMock(return_value=[t.EmberStatus.SUCCESS])

    # Should complete without raising an exception
    await ezsp_f.write_child_data({t.EUI64.convert("00:0b:57:ff:fe:2b:d4:57"): 0xC06B})

    assert ezsp_f.getTokenData.mock_calls == [
        call(token=t.NV3KeyId.NVM3KEY_STACK_CHILD_TABLE, index=0)
    ]
    assert ezsp_f.setTokenData.mock_calls == []
