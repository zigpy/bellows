from __future__ import annotations

import logging
from unittest.mock import AsyncMock, call, patch

import pytest

from bellows.exception import InvalidCommandError
from bellows.ezsp import EZSP, xncp
import bellows.types as t

from tests.test_ezsp import ezsp_f


async def test_xncp_failure(ezsp_f: EZSP) -> None:
    """Test XNCP failure."""

    command = xncp.XncpCommand.from_payload(
        xncp.GetSupportedFeaturesRsp(features=xncp.FirmwareFeatures.MANUAL_SOURCE_ROUTE)
    )
    command.status = xncp.XncpStatus.EMBER_BAD_ARGUMENT

    ezsp_f._mock_commands["customFrame"] = customFrame = AsyncMock(
        return_value=[
            t.EmberStatus.SUCCESS,  # The frame itself encodes a status code
            command.serialize(),
        ]
    )

    with pytest.raises(InvalidCommandError):
        await ezsp_f.xncp_get_supported_firmware_features()

    assert customFrame.mock_calls == [
        call(xncp.XncpCommand.from_payload(xncp.GetSupportedFeaturesReq()).serialize())
    ]


@pytest.mark.parametrize(
    "rsp",
    [
        # Gecko SDK 4.x firmware replies with an `EmberStatus`: `EMBER_NOT_FOUND`
        b"\x02\x80\x03",
        # Simplicity SDK firmware replies with the low octet of an
        # `sl_status_t`: `SL_STATUS_NOT_FOUND`
        b"\x02\x80\x2D",
    ],
)
async def test_xncp_missing_mfg_token_override(
    ezsp_f: EZSP, rsp: bytes, caplog
) -> None:
    """Test that a token without an override fails quietly, regardless of the SDK."""
    ezsp_f._mock_commands["customFrame"] = AsyncMock(
        return_value=[t.EmberStatus.SUCCESS, rsp]
    )
    ezsp_f._mock_commands["getMfgToken"] = AsyncMock(return_value=[b"\xFF" * 8])
    ezsp_f._xncp_features |= xncp.FirmwareFeatures.MFG_TOKEN_OVERRIDES

    with caplog.at_level(logging.WARNING, logger="bellows"):
        assert (
            await ezsp_f.get_mfg_token(t.EzspMfgTokenId.MFG_CUSTOM_EUI_64)
        ) == b"\xFF" * 8

    # An unsupported override is an expected condition, not a warning
    assert [
        r.getMessage()
        for r in caplog.records
        if r.name.startswith("bellows.") and r.levelno >= logging.WARNING
    ] == []


async def test_xncp_failure_multiprotocol(ezsp_f: EZSP) -> None:
    """Test XNCP failure with multiprotocol firmware."""
    ezsp_f._mock_commands["customFrame"] = customFrame = AsyncMock(
        return_value=[t.EmberStatus.SUCCESS, b""]
    )

    with pytest.raises(InvalidCommandError):
        await ezsp_f.xncp_get_supported_firmware_features()

    assert customFrame.mock_calls == [
        call(xncp.XncpCommand.from_payload(xncp.GetSupportedFeaturesReq()).serialize())
    ]


async def test_xncp_failure_lidl(ezsp_f: EZSP) -> None:
    """Test XNCP failure with hacked LIDL gateway."""
    ezsp_f._mock_commands["customFrame"] = customFrame = AsyncMock(
        return_value=[t.EmberStatus.SUCCESS, b"\x00\x01\x03"]
    )

    with pytest.raises(InvalidCommandError):
        await ezsp_f.xncp_get_supported_firmware_features()

    assert customFrame.mock_calls == [
        call(xncp.XncpCommand.from_payload(xncp.GetSupportedFeaturesReq()).serialize())
    ]


async def test_xncp_failure_unknown(ezsp_f: EZSP) -> None:
    """Test XNCP failure, unknown command."""
    ezsp_f._mock_commands["customFrame"] = customFrame = AsyncMock(
        return_value=[
            t.EmberStatus.SUCCESS,
            xncp.XncpCommand.from_payload(xncp.Unknown()).serialize(),
        ]
    )

    with pytest.raises(InvalidCommandError):
        await ezsp_f.xncp_get_supported_firmware_features()

    assert customFrame.mock_calls == [
        call(xncp.XncpCommand.from_payload(xncp.GetSupportedFeaturesReq()).serialize())
    ]


async def test_xncp_get_supported_firmware_features(ezsp_f: EZSP) -> None:
    """Test XNCP get_supported_firmware_features."""
    ezsp_f._mock_commands["customFrame"] = customFrame = AsyncMock(
        return_value=[
            t.EmberStatus.SUCCESS,
            xncp.XncpCommand.from_payload(
                xncp.GetSupportedFeaturesRsp(
                    features=xncp.FirmwareFeatures.MANUAL_SOURCE_ROUTE
                )
            ).serialize(),
        ]
    )

    assert (
        await ezsp_f.xncp_get_supported_firmware_features()
    ) == xncp.FirmwareFeatures.MANUAL_SOURCE_ROUTE
    assert customFrame.mock_calls == [
        call(xncp.XncpCommand.from_payload(xncp.GetSupportedFeaturesReq()).serialize())
    ]


async def test_xncp_get_build_string(ezsp_f: EZSP) -> None:
    """Test XNCP get_build_string."""
    ezsp_f._mock_commands["customFrame"] = customFrame = AsyncMock(
        return_value=[
            t.EmberStatus.SUCCESS,
            xncp.XncpCommand.from_payload(
                xncp.GetBuildStringRsp(build_string="Some complex string 🦜".encode())
            ).serialize(),
        ]
    )

    assert await ezsp_f.xncp_get_build_string() == "Some complex string 🦜"
    assert customFrame.mock_calls == [
        call(xncp.XncpCommand.from_payload(xncp.GetBuildStringReq()).serialize())
    ]


async def test_xncp_set_manual_source_route(ezsp_f: EZSP) -> None:
    """Test XNCP set_manual_source_route."""
    ezsp_f._mock_commands["customFrame"] = customFrame = AsyncMock(
        return_value=[
            t.EmberStatus.SUCCESS,
            (
                xncp.XncpCommand.from_payload(xncp.SetSourceRouteRsp()).serialize()
                + b"some extra data"
            ),
        ]
    )

    await ezsp_f.xncp_set_manual_source_route(
        destination=0x1234, route=[0x5678, 0xABCD]
    )
    assert customFrame.mock_calls == [
        call(
            xncp.XncpCommand.from_payload(
                xncp.SetSourceRouteReq(
                    destination=0x1234, source_route=[0x5678, 0xABCD]
                )
            ).serialize()
        )
    ]


async def test_xncp_get_mfg_token_override(ezsp_f: EZSP) -> None:
    """Test XNCP get_mfg_token_override."""
    ezsp_f._mock_commands["customFrame"] = customFrame = AsyncMock(
        return_value=[
            t.EmberStatus.SUCCESS,
            xncp.XncpCommand.from_payload(
                xncp.GetMfgTokenOverrideRsp(value=b"value")
            ).serialize(),
        ]
    )

    await ezsp_f.xncp_get_mfg_token_override(token=t.EzspMfgTokenId.MFG_CUSTOM_EUI_64)
    assert customFrame.mock_calls == [
        call(
            xncp.XncpCommand.from_payload(
                xncp.GetMfgTokenOverrideReq(token=t.EzspMfgTokenId.MFG_CUSTOM_EUI_64)
            ).serialize()
        )
    ]


async def test_xncp_get_flow_control_type(ezsp_f: EZSP) -> None:
    """Test XNCP get_flow_control_type."""
    ezsp_f._mock_commands["customFrame"] = customFrame = AsyncMock(
        return_value=[
            t.EmberStatus.SUCCESS,
            xncp.XncpCommand.from_payload(
                xncp.GetFlowControlTypeRsp(
                    flow_control_type=xncp.FlowControlType.HARDWARE
                )
            ).serialize(),
        ]
    )

    assert await ezsp_f.xncp_get_flow_control_type() == xncp.FlowControlType.HARDWARE
    assert customFrame.mock_calls == [
        call(xncp.XncpCommand.from_payload(xncp.GetFlowControlTypeReq()).serialize())
    ]


async def test_xncp_get_xncp_features_fixes(ezsp_f: EZSP) -> None:
    """Test XNCP `get_xncp_features`, with fixes."""
    ezsp_f._ezsp_version = 13

    ezsp_f._mock_commands["customFrame"] = customFrame = AsyncMock(
        return_value=[
            t.EmberStatus.SUCCESS,
            xncp.XncpCommand.from_payload(
                xncp.GetSupportedFeaturesRsp(
                    features=(
                        xncp.FirmwareFeatures.MANUAL_SOURCE_ROUTE
                        | xncp.FirmwareFeatures.MEMBER_OF_ALL_GROUPS
                    )
                )
            ).serialize(),
        ]
    )

    # In 7.4.4.0, it's broken
    with patch.object(
        ezsp_f,
        "get_board_info",
        return_value=("Model", "Manufacturer", "7.4.4.0 build 0"),
    ):
        assert (
            await ezsp_f.get_xncp_features()
        ) == xncp.FirmwareFeatures.MANUAL_SOURCE_ROUTE

    # In a hypothetical new release, it's not
    with patch.object(
        ezsp_f,
        "get_board_info",
        return_value=("Model", "Manufacturer", "7.4.4.0 build 1"),
    ):
        assert (await ezsp_f.get_xncp_features()) == (
            xncp.FirmwareFeatures.MANUAL_SOURCE_ROUTE
            | xncp.FirmwareFeatures.MEMBER_OF_ALL_GROUPS
        )

    # XNCP is ignored for older EmberZNet
    ezsp_f._ezsp_version = 8
    assert (await ezsp_f.get_xncp_features()) == xncp.FirmwareFeatures.NONE

    assert customFrame.mock_calls == [
        call(xncp.XncpCommand.from_payload(xncp.GetSupportedFeaturesReq()).serialize()),
        call(xncp.XncpCommand.from_payload(xncp.GetSupportedFeaturesReq()).serialize()),
    ]


async def test_xncp_route_table_operations(ezsp_f: EZSP) -> None:
    """Test XNCP get and set route table entry commands."""
    # Test get route table entry
    ezsp_f._mock_commands["customFrame"] = customFrame = AsyncMock(
        return_value=[
            t.EmberStatus.SUCCESS,
            xncp.XncpCommand.from_payload(
                xncp.GetRouteTableEntryRsp(
                    destination=t.NWK(0x1234),
                    next_hop=t.NWK(0x5678),
                    status=t.RouteRecordStatus.ACTIVE_AGE_2,
                    cost=3,
                )
            ).serialize(),
        ]
    )

    rsp = await ezsp_f.xncp_get_route_table_entry(index=5)
    assert rsp.destination == 0x1234
    assert rsp.next_hop == 0x5678
    assert rsp.status == t.RouteRecordStatus.ACTIVE_AGE_2
    assert rsp.cost == 3
    assert customFrame.mock_calls == [
        call(
            xncp.XncpCommand.from_payload(
                xncp.GetRouteTableEntryReq(index=5)
            ).serialize()
        )
    ]

    # Test set route table entry
    customFrame.reset_mock()
    ezsp_f._mock_commands["customFrame"] = customFrame = AsyncMock(
        return_value=[
            t.EmberStatus.SUCCESS,
            xncp.XncpCommand.from_payload(xncp.SetRouteTableEntryRsp()).serialize(),
        ]
    )

    await ezsp_f.xncp_set_route_table_entry(
        index=10,
        destination=t.NWK(0xABCD),
        next_hop=t.NWK(0xEF01),
        status=t.RouteRecordStatus.ACTIVE_AGE_0,
        cost=1,
    )
    assert customFrame.mock_calls == [
        call(
            xncp.XncpCommand.from_payload(
                xncp.SetRouteTableEntryReq(
                    index=10,
                    destination=t.NWK(0xABCD),
                    next_hop=t.NWK(0xEF01),
                    status=t.RouteRecordStatus.ACTIVE_AGE_0,
                    cost=1,
                )
            ).serialize()
        )
    ]


async def test_xncp_get_tx_power_info(ezsp_f: EZSP) -> None:
    """Test XNCP get_tx_power_info."""
    ezsp_f._mock_commands["customFrame"] = customFrame = AsyncMock(
        return_value=[
            t.EmberStatus.SUCCESS,
            xncp.XncpCommand.from_payload(
                xncp.GetTxPowerInfoRsp(recommended_power_dbm=10, max_power_dbm=20)
            ).serialize(),
        ]
    )

    rsp = await ezsp_f.xncp_get_tx_power_info("us")
    assert rsp.recommended_power_dbm == 10
    assert rsp.max_power_dbm == 20
    assert customFrame.mock_calls == [
        call(
            xncp.XncpCommand.from_payload(
                xncp.GetTxPowerInfoReq(country_code=b"US")
            ).serialize()
        )
    ]
