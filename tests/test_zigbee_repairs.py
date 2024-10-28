"""Test network state repairs."""

import logging
from unittest.mock import AsyncMock, call

import pytest

from bellows.exception import InvalidCommandError
from bellows.ezsp import EZSP
from bellows.ezsp.v9.commands import GetTokenDataRsp
import bellows.types as t
from bellows.zigbee import repairs

from tests.test_ezsp import ezsp_f, make_connected_ezsp


@pytest.fixture
def ezsp_tclk_f(ezsp_f: EZSP) -> EZSP:
    """Mock an EZSP instance with a valid TCLK."""
    ezsp_f.getEui64 = AsyncMock(
        return_value=[t.EUI64.convert("AA:AA:AA:AA:AA:AA:AA:AA")]
    )
    ezsp_f.getTokenData = AsyncMock(side_effect=InvalidCommandError())
    ezsp_f.getCurrentSecurityState = AsyncMock(
        return_value=[
            t.EmberStatus.SUCCESS,
            t.EmberCurrentSecurityState(
                bitmask=(
                    t.EmberCurrentSecurityBitmask.GLOBAL_LINK_KEY
                    | t.EmberCurrentSecurityBitmask.HAVE_TRUST_CENTER_LINK_KEY
                    | 224
                ),
                trustCenterLongAddress=t.EUI64.convert("AA:AA:AA:AA:AA:AA:AA:AA"),
            ),
        ]
    )
    return ezsp_f


async def test_fix_invalid_tclk_noop(ezsp_tclk_f: EZSP, caplog) -> None:
    """Test that the TCLK is not rewritten unnecessarily."""

    ezsp_tclk_f.getEui64.return_value[0] = t.EUI64.convert("AA:AA:AA:AA:AA:AA:AA:AA")
    ezsp_tclk_f.getCurrentSecurityState.return_value[
        1
    ].trustCenterLongAddress = t.EUI64.convert("AA:AA:AA:AA:AA:AA:AA:AA")

    with caplog.at_level(logging.WARNING):
        assert await repairs.fix_invalid_tclk_partner_ieee(ezsp_tclk_f) is False

    assert "Fixing invalid TCLK" not in caplog.text


async def test_fix_invalid_tclk_old_firmware(ezsp_tclk_f: EZSP, caplog) -> None:
    """Test that the TCLK is not rewritten when the firmware is too old."""

    ezsp_tclk_f.getTokenData = AsyncMock(side_effect=InvalidCommandError())
    ezsp_tclk_f.getEui64.return_value[0] = t.EUI64.convert("AA:AA:AA:AA:AA:AA:AA:AA")
    ezsp_tclk_f.getCurrentSecurityState.return_value[
        1
    ].trustCenterLongAddress = t.EUI64.convert("BB:BB:BB:BB:BB:BB:BB:BB")

    with caplog.at_level(logging.WARNING):
        assert await repairs.fix_invalid_tclk_partner_ieee(ezsp_tclk_f) is False

    assert "Fixing invalid TCLK" in caplog.text
    assert "NV3 interface not available in this firmware" in caplog.text


async def test_fix_invalid_tclk(ezsp_tclk_f: EZSP, caplog) -> None:
    """Test that the TCLK is not rewritten when the firmware is too old."""

    ezsp_tclk_f.setTokenData = AsyncMock(return_value=[t.EmberStatus.SUCCESS])
    ezsp_tclk_f.getTokenData = AsyncMock(
        return_value=GetTokenDataRsp(
            status=t.EmberStatus.SUCCESS,
            value=t.NV3StackTrustCenterToken(
                mode=228,
                eui64=t.EUI64.convert("BB:BB:BB:BB:BB:BB:BB:BB"),
                key=t.KeyData.convert(
                    "21:8e:df:b8:50:a0:4a:b6:8b:c6:10:25:bc:4e:93:6a"
                ),
            ).serialize(),
        )
    )
    ezsp_tclk_f.getEui64.return_value[0] = t.EUI64.convert("AA:AA:AA:AA:AA:AA:AA:AA")
    ezsp_tclk_f.getCurrentSecurityState.return_value[
        1
    ].trustCenterLongAddress = t.EUI64.convert("BB:BB:BB:BB:BB:BB:BB:BB")

    with caplog.at_level(logging.WARNING):
        assert await repairs.fix_invalid_tclk_partner_ieee(ezsp_tclk_f) is True

    assert "Fixing invalid TCLK" in caplog.text
    assert "NV3 interface not available in this firmware" not in caplog.text

    assert ezsp_tclk_f.setTokenData.mock_calls == [
        call(
            token=t.NV3KeyId.NVM3KEY_STACK_TRUST_CENTER,
            index=0,
            token_data=t.NV3StackTrustCenterToken(
                mode=228,
                eui64=t.EUI64.convert("AA:AA:AA:AA:AA:AA:AA:AA"),
                key=t.KeyData.convert(
                    "21:8e:df:b8:50:a0:4a:b6:8b:c6:10:25:bc:4e:93:6a"
                ),
            ).serialize(),
        )
    ]


@pytest.mark.parametrize("version", EZSP._BY_VERSION)
@pytest.mark.parametrize("has_library", [(True, False)])
async def test_fix_invalid_tclk_all_versions(
    version: int, has_library: bool, ezsp_tclk_f: EZSP, caplog
) -> None:
    """Test that the TCLK is fixed (or not) on all versions."""

    ezsp = await make_connected_ezsp(version=version)

    fw_has_token_interface = hasattr(ezsp, "setTokenData")

    if fw_has_token_interface:
        ezsp.setTokenData = AsyncMock(return_value=[t.EmberStatus.SUCCESS])
        ezsp.getTokenData = AsyncMock(
            return_value=GetTokenDataRsp(
                status=t.EmberStatus.SUCCESS,
                value=t.NV3StackTrustCenterToken(
                    mode=228,
                    eui64=t.EUI64.convert("BB:BB:BB:BB:BB:BB:BB:BB"),
                    key=t.KeyData.convert(
                        "21:8e:df:b8:50:a0:4a:b6:8b:c6:10:25:bc:4e:93:6a"
                    ),
                ).serialize(),
            )
        )

    if not has_library:
        ezsp.setTokenData = AsyncMock(return_value=[t.EmberStatus.LIBRARY_NOT_LOADED])
        ezsp.getTokenData = AsyncMock(
            return_value=GetTokenDataRsp(status=t.EmberStatus.LIBRARY_NOT_LOADED)
        )

    ezsp.getEui64 = ezsp_tclk_f.getEui64
    ezsp.getCurrentSecurityState = ezsp_tclk_f.getCurrentSecurityState

    ezsp.getEui64.return_value[0] = t.EUI64.convert("AA:AA:AA:AA:AA:AA:AA:AA")
    ezsp.getCurrentSecurityState.return_value[
        1
    ].trustCenterLongAddress = t.EUI64.convert("BB:BB:BB:BB:BB:BB:BB:BB")

    with caplog.at_level(logging.WARNING):
        assert (
            await repairs.fix_invalid_tclk_partner_ieee(ezsp) is fw_has_token_interface
        )

    assert "Fixing invalid TCLK" in caplog.text

    if fw_has_token_interface and has_library:
        assert "NV3 interface not available in this firmware" not in caplog.text

        assert ezsp.setTokenData.mock_calls == [
            call(
                token=t.NV3KeyId.NVM3KEY_STACK_TRUST_CENTER,
                index=0,
                token_data=t.NV3StackTrustCenterToken(
                    mode=228,
                    eui64=t.EUI64.convert("AA:AA:AA:AA:AA:AA:AA:AA"),
                    key=t.KeyData.convert(
                        "21:8e:df:b8:50:a0:4a:b6:8b:c6:10:25:bc:4e:93:6a"
                    ),
                ).serialize(),
            )
        ]
    else:
        assert "NV3 interface not available in this firmware" in caplog.text
