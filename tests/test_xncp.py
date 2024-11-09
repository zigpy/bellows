from __future__ import annotations

from unittest.mock import AsyncMock, call

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
    command.status = t.EmberStatus.ERR_FATAL

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
                    flow_control_type=xncp.FlowControlType.Hardware
                )
            ).serialize(),
        ]
    )

    assert await ezsp_f.xncp_get_flow_control_type() == xncp.FlowControlType.Hardware
    assert customFrame.mock_calls == [
        call(xncp.XncpCommand.from_payload(xncp.GetFlowControlTypeReq()).serialize())
    ]
