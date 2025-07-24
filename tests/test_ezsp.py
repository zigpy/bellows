from __future__ import annotations

import asyncio
import functools
import logging
import sys

import pytest
import zigpy.config

from bellows import config, uart
from bellows.ash import NcpFailure
from bellows.exception import EzspError, InvalidCommandError
from bellows.ezsp import EZSP, EZSP_LATEST, xncp
import bellows.types as t

if sys.version_info[:2] < (3, 11):
    from async_timeout import timeout as asyncio_timeout  # pragma: no cover
else:
    from asyncio import timeout as asyncio_timeout  # pragma: no cover

from unittest.mock import ANY, AsyncMock, MagicMock, call, patch

from bellows.ezsp.v9.commands import GetTokenDataRsp

DEVICE_CONFIG = {
    zigpy.config.CONF_DEVICE_PATH: "/dev/null",
    zigpy.config.CONF_DEVICE_BAUDRATE: 115200,
}


def make_ezsp(config: dict = DEVICE_CONFIG, version: int = 4):
    api = EZSP(config)

    async def mock_command(command, *args, **kwargs):
        if command in api._mock_commands:
            return await api._mock_commands[command](*args, **kwargs)

        raise RuntimeError(f"Command has not been mocked: {command}({args}, {kwargs})")

    api._mock_commands = {}
    api._mock_commands["version"] = AsyncMock(return_value=[version, 0, 0])
    api._mock_commands["customFrame"] = AsyncMock(
        return_value=[t.EmberStatus.LIBRARY_NOT_PRESENT, b""]
    )
    api._command = AsyncMock(side_effect=mock_command)

    return api


async def make_connected_ezsp(config: dict = DEVICE_CONFIG, version: int = 4):
    with patch("bellows.uart.connect"):
        ezsp = make_ezsp(config=config, version=version)
        await ezsp.connect()

    return ezsp


@pytest.fixture
async def ezsp_f() -> EZSP:
    with patch("bellows.uart.connect"):
        ezsp = make_ezsp(version=12)

        assert ezsp._ezsp_version == 4
        await ezsp.connect()
        assert ezsp._ezsp_version == 12

        yield ezsp


async def test_reset(ezsp_f):
    ezsp_f.stop_ezsp = MagicMock()
    ezsp_f.start_ezsp = MagicMock()

    reset_mock = AsyncMock()
    ezsp_f._gw.reset = MagicMock(side_effect=reset_mock)

    await ezsp_f.reset()
    assert ezsp_f._gw.reset.call_count == 1
    assert ezsp_f.start_ezsp.call_count == 1
    assert ezsp_f.stop_ezsp.call_count == 1
    assert len(ezsp_f._callbacks) == 1


async def test_disconnect(ezsp_f):
    gw_disconnect = ezsp_f._gw.disconnect
    await ezsp_f.disconnect()
    assert len(gw_disconnect.mock_calls) == 1


def test_attr(ezsp_f):
    m = ezsp_f.getValue
    assert isinstance(m, functools.partial)
    assert callable(m)


async def test_non_existent_attr(ezsp_f):
    with pytest.raises(AttributeError):
        await ezsp_f.nonexistentMethod()


async def test_command(ezsp_f):
    # Un-mock it
    ezsp_f._command = EZSP._command.__get__(ezsp_f, EZSP)

    with patch.object(ezsp_f._protocol, "command") as cmd_mock:
        await ezsp_f.nop()
    assert cmd_mock.call_count == 1


async def test_command_ezsp_stopped(ezsp_f):
    # Un-mock it
    ezsp_f._command = EZSP._command.__get__(ezsp_f, EZSP)
    ezsp_f.stop_ezsp()

    with pytest.raises(EzspError):
        await ezsp_f._command("version")


async def test_list_command():
    ezsp = await make_connected_ezsp(version=4)

    async def mockcommand(name, *args, **kwargs):
        assert name == "startScan"
        ezsp.frame_received(b"\x01\x00\x1b" + b"\x00" * 20)
        ezsp.frame_received(b"\x02\x00\x1b" + b"\x00" * 20)
        ezsp.frame_received(b"\x03\x00\x1c" + b"\x00" * 20)

        return [t.EmberStatus.SUCCESS]

    ezsp._command = mockcommand

    result = await ezsp._list_command(
        "startScan",
        ["networkFoundHandler"],
        "scanCompleteHandler",
        1,
    )
    assert len(result) == 2


async def test_list_command_initial_failure():
    ezsp = await make_connected_ezsp(version=4)

    async def mockcommand(name, *args, **kwargs):
        assert name == "startScan"
        return [t.EmberStatus.FAILURE]

    ezsp._command = mockcommand

    with pytest.raises(Exception):
        await ezsp._list_command(
            "startScan",
            ["networkFoundHandler"],
            "scanCompleteHandler",
            1,
        )


async def test_list_command_later_failure():
    ezsp = await make_connected_ezsp(version=4)

    async def mockcommand(name, *args, **kwargs):
        assert name == "startScan"
        ezsp.frame_received(b"\x01\x00\x1b" + b"\x00" * 20)
        ezsp.frame_received(b"\x02\x00\x1b" + b"\x00" * 20)
        ezsp.frame_received(b"\x03\x00\x1c\x01\x01")

        return [t.EmberStatus.SUCCESS]

    ezsp._command = mockcommand

    with pytest.raises(Exception):
        await ezsp._list_command(
            "startScan",
            ["networkFoundHandler"],
            "scanCompleteHandler",
            1,
        )


async def _test_form_network(ezsp, initial_result, final_result):
    async def mockcommand(name, *args, **kwargs):
        assert name == "formNetwork"
        ezsp.frame_received(b"\x01\x00\x19" + final_result)
        return initial_result

    ezsp._command = mockcommand

    await ezsp.formNetwork(MagicMock())


async def test_form_network():
    ezsp = await make_connected_ezsp(version=4)

    await _test_form_network(ezsp, [t.EmberStatus.SUCCESS], b"\x90")


async def test_form_network_fail():
    ezsp = await make_connected_ezsp(version=4)

    with pytest.raises(Exception):
        await _test_form_network(ezsp, [t.EmberStatus.FAILURE], b"\x90")


@patch("bellows.ezsp.NETWORK_OPS_TIMEOUT", 0.1)
async def test_form_network_fail_stack_status():
    ezsp = await make_connected_ezsp(version=4)

    with pytest.raises(Exception):
        await _test_form_network(ezsp, [t.EmberStatus.SUCCESS], b"\x00")


async def test_receive_new():
    ezsp = await make_connected_ezsp(version=4)

    callback = MagicMock()
    ezsp.add_callback(callback)
    ezsp.frame_received(b"\x00\xff\x00\x04\x05\x06\x00")
    assert callback.call_count == 1


def test_callback(ezsp_f):
    testcb = MagicMock()

    cbid = ezsp_f.add_callback(testcb)
    ezsp_f.handle_callback(1, 2, 3)

    assert testcb.call_count == 1

    ezsp_f.remove_callback(cbid)
    ezsp_f.handle_callback(4, 5, 6)
    assert testcb.call_count == 1


def test_callback_multi(ezsp_f):
    testcb = MagicMock()

    cbid1 = ezsp_f.add_callback(testcb)
    ezsp_f.add_callback(testcb)

    ezsp_f.handle_callback(1, 2, 3)

    assert testcb.call_count == 2

    ezsp_f.remove_callback(cbid1)

    ezsp_f.handle_callback(4, 5, 6)
    testcb.assert_has_calls([call(1, 2, 3), call(1, 2, 3), call(4, 5, 6)])


def test_callback_exc(ezsp_f):
    testcb = MagicMock()
    testcb.side_effect = Exception("Testing")

    ezsp_f.add_callback(testcb)
    ezsp_f.handle_callback(1)
    assert testcb.call_count == 1


@pytest.mark.parametrize("version, call_count", ((4, 1), (5, 2), (6, 2), (99, 2)))
async def test_change_version(version, call_count):
    ezsp = await make_connected_ezsp(version=4)

    async def mockcommand(name, *args, **kwargs):
        assert name == "version"
        ezsp.frame_received(b"\x01\x00\x00\x21\x22\x23\x24")
        return [version, 2, 2046]

    ezsp._command = AsyncMock(side_effect=mockcommand)
    await ezsp.version()
    assert ezsp.ezsp_version == version
    assert ezsp._command.call_count == call_count


def test_stop_ezsp(ezsp_f):
    ezsp_f._ezsp_event.set()
    ezsp_f.stop_ezsp()
    assert ezsp_f._ezsp_event.is_set() is False


def test_start_ezsp(ezsp_f):
    ezsp_f._ezsp_event.clear()
    ezsp_f.start_ezsp()
    assert ezsp_f._ezsp_event.is_set() is True


def test_enter_failed_state(ezsp_f):
    ezsp_f._application = MagicMock()
    ezsp_f.enter_failed_state(t.NcpResetCode.RESET_SOFTWARE)

    assert ezsp_f._application.connection_lost.mock_calls == [
        call(NcpFailure(code=t.NcpResetCode.RESET_SOFTWARE))
    ]


@patch.object(EZSP, "version", side_effect=RuntimeError("Uh oh"))
@patch.object(EZSP, "reset", new_callable=AsyncMock)
@patch.object(EZSP, "disconnect", new_callable=AsyncMock)
async def test_ezsp_connect_failure(disconnect_mock, reset_mock, version_mock):
    """Test initialize method failing."""
    with patch("bellows.uart.connect") as conn_mock:
        ezsp = make_ezsp(version=4)

        with pytest.raises(RuntimeError):
            await ezsp.connect()

    assert conn_mock.await_count == 1
    assert reset_mock.await_count == 1
    assert version_mock.await_count == 1
    assert disconnect_mock.call_count == 1


async def test_ezsp_newer_version(ezsp_f):
    """Test newer version of ezsp."""
    with patch.object(
        ezsp_f, "_command", new=AsyncMock(return_value=(9, 0x12, 0x12345))
    ):
        await ezsp_f.version()


@pytest.mark.parametrize(
    (
        "mfg_board_name",
        "mfg_string",
        "xncp_build_string",
        "value_version_info",
        "expected",
    ),
    [
        (
            (b"\xfe\xff\xff\xff",),
            (b"Manufacturer\xff\xff\xff",),
            (InvalidCommandError("XNCP is not supported"),),
            (t.EmberStatus.SUCCESS, b"\x01\x02\x03\x04\x05\x06"),
            ("Manufacturer", "0xFE", "3.4.5.6 build 513"),
        ),
        (
            (b"\xfe\xff\xff\xff",),
            (b"Manufacturer\xff\xff\xff",),
            (InvalidCommandError("XNCP is not supported"),),
            (t.EmberStatus.ERR_FATAL, b"\x01\x02\x03\x04\x05\x06"),
            ("Manufacturer", "0xFE", None),
        ),
        (
            (b"SkyBlue v0.1\x00\xff\xff\xff",),
            (b"Nabu Casa\x00\xff\xff\xff\xff\xff\xff",),
            (InvalidCommandError("XNCP is not supported"),),
            (t.EmberStatus.SUCCESS, b"\xbf\x00\x07\x01\x00\x00\xaa"),
            ("Nabu Casa", "SkyBlue v0.1", "7.1.0.0 build 191"),
        ),
        (
            (b"\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff",),
            (b"\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff",),
            (InvalidCommandError("XNCP is not supported"),),
            (t.EmberStatus.SUCCESS, b"\xbf\x00\x07\x01\x00\x00\xaa"),
            (None, None, "7.1.0.0 build 191"),
        ),
        (
            (b"\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff",),
            (b"\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x00\x00",),
            (InvalidCommandError("XNCP is not supported"),),
            (t.EmberStatus.SUCCESS, b")\x01\x06\n\x03\x00\xaa"),
            (None, None, "6.10.3.0 build 297"),
        ),
        (
            (b"SkyBlue v0.1\x00\xff\xff\xff",),
            (b"Nabu Casa\x00\xff\xff\xff\xff\xff\xff",),
            ("special build",),
            (t.EmberStatus.SUCCESS, b"\xbf\x00\x07\x01\x00\x00\xaa"),
            ("Nabu Casa", "SkyBlue v0.1", "7.1.0.0 build 191 (special build)"),
        ),
    ],
)
async def test_board_info(
    ezsp_f,
    mfg_board_name: bytes,
    mfg_string: bytes,
    xncp_build_string: str | Exception,
    value_version_info: tuple[t.EmberStatus, bytes],
    expected: tuple[str | None, str | None, str],
):
    """Test getting board info."""

    def cmd_mock(config):
        async def replacement(command_name, tokenId=None, valueId=None):
            return config[command_name, tokenId or valueId]

        return replacement

    if not isinstance(xncp_build_string, InvalidCommandError):
        ezsp_f._xncp_features |= xncp.FirmwareFeatures.BUILD_STRING

    with patch.object(
        ezsp_f,
        "_command",
        new=cmd_mock(
            {
                ("getMfgToken", t.EzspMfgTokenId.MFG_BOARD_NAME): mfg_board_name,
                ("getMfgToken", t.EzspMfgTokenId.MFG_STRING): mfg_string,
                ("getValue", t.EzspValueId.VALUE_VERSION_INFO): value_version_info,
            }
        ),
    ), patch.object(ezsp_f, "xncp_get_build_string", side_effect=xncp_build_string):
        mfg, brd, ver = await ezsp_f.get_board_info()

    assert (mfg, brd, ver) == expected


async def test_set_enable_source_routing(ezsp_f):
    """Test enabling source routing."""
    ezsp_f.setConcentrator = AsyncMock(return_value=(t.EmberStatus.SUCCESS,))
    ezsp_f.setSourceRouteDiscoveryMode = AsyncMock()

    await ezsp_f.set_source_routing(enabled=True)
    assert len(ezsp_f.setSourceRouteDiscoveryMode.mock_calls) == 1
    assert (
        ezsp_f.setSourceRouteDiscoveryMode.mock_calls[0].kwargs["mode"]
        == t.SourceRouteDiscoveryMode.ON
    )


async def test_set_disable_source_routing(ezsp_f):
    """Test disabling source routing."""
    ezsp_f.setConcentrator = AsyncMock(return_value=(t.EmberStatus.SUCCESS,))
    ezsp_f.setSourceRouteDiscoveryMode = AsyncMock()

    await ezsp_f.set_source_routing(enabled=False)
    assert len(ezsp_f.setSourceRouteDiscoveryMode.mock_calls) == 1
    assert (
        ezsp_f.setSourceRouteDiscoveryMode.mock_calls[0].kwargs["mode"]
        == t.SourceRouteDiscoveryMode.OFF
    )


async def test_leave_network_error(ezsp_f):
    """Test EZSP leaveNetwork command failure."""

    with patch.object(ezsp_f, "_command", new_callable=AsyncMock) as cmd_mock:
        cmd_mock.return_value = [t.EmberStatus.ERR_FATAL]
        with pytest.raises(EzspError):
            await ezsp_f.leaveNetwork(timeout=0.01)


async def test_leave_network_no_stack_status(ezsp_f):
    """Test EZSP leaveNetwork command, no stackStatusHandler callback."""

    with patch.object(ezsp_f, "_command", new_callable=AsyncMock) as cmd_mock:
        cmd_mock.return_value = [t.EmberStatus.SUCCESS]
        with pytest.raises(asyncio.TimeoutError):
            await ezsp_f.leaveNetwork(timeout=0.01)


async def test_leave_network(ezsp_f):
    """Test EZSP leaveNetwork command."""

    async def _mock_cmd(*args, **kwargs):
        ezsp_f.handle_callback("stackStatusHandler", [t.EmberStatus.NETWORK_UP])
        ezsp_f.handle_callback("stackStatusHandler", [t.EmberStatus.NETWORK_UP])
        ezsp_f.handle_callback("stackStatusHandler", [t.EmberStatus.NETWORK_DOWN])
        return [t.EmberStatus.SUCCESS]

    with patch.object(ezsp_f, "_command", new_callable=AsyncMock) as cmd_mock:
        cmd_mock.side_effect = _mock_cmd
        await ezsp_f.leaveNetwork(timeout=0.01)


async def test_xncp_token_override(ezsp_f):
    ezsp_f.getMfgToken = AsyncMock(return_value=[b"firmware value"])
    ezsp_f.xncp_get_mfg_token_override = AsyncMock(return_value=b"xncp value")

    # Without firmware support, the XNCP command isn't sent
    assert (
        await ezsp_f.get_mfg_token(t.EzspMfgTokenId.MFG_CUSTOM_EUI_64)
    ) == b"firmware value"

    # With firmware support, it is
    ezsp_f._xncp_features |= xncp.FirmwareFeatures.MFG_TOKEN_OVERRIDES
    assert (
        await ezsp_f.get_mfg_token(t.EzspMfgTokenId.MFG_CUSTOM_EUI_64)
    ) == b"xncp value"

    # Tokens without overrides are still read normally
    ezsp_f.xncp_get_mfg_token_override.side_effect = InvalidCommandError
    assert (
        await ezsp_f.get_mfg_token(t.EzspMfgTokenId.MFG_CUSTOM_EUI_64)
    ) == b"firmware value"


@pytest.mark.parametrize(
    "value, expected_result",
    [
        (b"\xFF" * 8, True),
        (bytes.fromhex("0846b8a11c004b1200"), False),
        (b"", False),
    ],
)
async def test_can_burn_userdata_custom_eui64(ezsp_f, value, expected_result):
    """Test detecting if a custom EUI64 has been written."""
    ezsp_f.getMfgToken = AsyncMock(return_value=[value])

    assert await ezsp_f.can_burn_userdata_custom_eui64() == expected_result

    ezsp_f.getMfgToken.assert_called_once_with(
        tokenId=t.EzspMfgTokenId.MFG_CUSTOM_EUI_64
    )


@pytest.mark.parametrize(
    "tokens, expected_key, expected_result",
    [
        ({}, None, False),
        (
            {t.NV3KeyId.CREATOR_STACK_RESTORED_EUI64: b"\xAA" * 8},
            t.NV3KeyId.CREATOR_STACK_RESTORED_EUI64,
            True,
        ),
        (
            {t.NV3KeyId.NVM3KEY_STACK_RESTORED_EUI64: b"\xAA" * 8},
            t.NV3KeyId.NVM3KEY_STACK_RESTORED_EUI64,
            True,
        ),
    ],
)
async def test_can_rewrite_custom_eui64(ezsp_f, tokens, expected_key, expected_result):
    """Test detecting if a custom EUI64 can be rewritten in NV3."""

    def get_token_data(token, index):
        if token not in tokens or index != 0:
            return GetTokenDataRsp(status=t.EmberStatus.ERR_FATAL)

        return GetTokenDataRsp(status=t.EmberStatus.SUCCESS, value=tokens[token])

    ezsp_f.getTokenData = AsyncMock(side_effect=get_token_data)

    key = await ezsp_f._get_nv3_restored_eui64_key()
    assert key == expected_key
    assert await ezsp_f.can_rewrite_custom_eui64() == expected_result


async def test_can_rewrite_custom_eui64_old_ezsp(ezsp_f):
    """Test detecting if a custom EUI64 can be rewritten in NV3, but with old EZSP."""

    ezsp_f._ezsp_version = 4
    ezsp_f.getTokenData = AsyncMock(side_effect=InvalidCommandError)
    assert await ezsp_f._get_nv3_restored_eui64_key() is None
    assert not await ezsp_f.can_rewrite_custom_eui64()


async def test_write_custom_eui64(ezsp_f):
    """Test writing a custom EUI64."""

    old_eui64 = t.EUI64.convert("AA" * 8)
    new_eui64 = t.EUI64.convert("BB" * 8)

    ezsp_f.getEui64 = AsyncMock(return_value=[old_eui64])
    ezsp_f.setMfgToken = AsyncMock(return_value=[t.EmberStatus.SUCCESS])
    ezsp_f.setTokenData = AsyncMock(return_value=[t.EmberStatus.SUCCESS])
    ezsp_f._get_mfg_custom_eui_64 = AsyncMock(return_value=old_eui64)
    ezsp_f._get_nv3_restored_eui64_key = AsyncMock(return_value=None)

    # Nothing is done when the EUI64 write is a no-op
    await ezsp_f.write_custom_eui64(old_eui64)

    ezsp_f.setMfgToken.assert_not_called()
    ezsp_f.setTokenData.assert_not_called()

    # If NV3 exists, all writes succeed
    ezsp_f._get_nv3_restored_eui64_key.return_value = (
        t.NV3KeyId.NVM3KEY_STACK_RESTORED_EUI64
    )
    await ezsp_f.write_custom_eui64(new_eui64)
    await ezsp_f.write_custom_eui64(new_eui64, burn_into_userdata=True)

    ezsp_f.setMfgToken.assert_not_called()
    ezsp_f.setTokenData.mock_calls == 2 * [
        call(
            t.NV3KeyId.NVM3KEY_STACK_RESTORED_EUI64,
            0,
            new_eui64.serialize(),
        )
    ]

    ezsp_f.setTokenData.reset_mock()

    # If NV3 does not and the MFG token does not, we conditionally write
    ezsp_f._get_mfg_custom_eui_64.return_value = None
    ezsp_f._get_nv3_restored_eui64_key.return_value = None

    with pytest.raises(EzspError):
        await ezsp_f.write_custom_eui64(new_eui64)

    # Burn kwarg not passed, so nothing is done
    ezsp_f.setMfgToken.assert_not_called()
    ezsp_f.setTokenData.assert_not_called()

    await ezsp_f.write_custom_eui64(new_eui64, burn_into_userdata=True)

    ezsp_f.setMfgToken.assert_called_once_with(
        tokenId=t.EzspMfgTokenId.MFG_CUSTOM_EUI_64, tokenData=new_eui64.serialize()
    )
    ezsp_f.setTokenData.assert_not_called()

    ezsp_f.setMfgToken.reset_mock()

    # If no method is viable, throw an error
    ezsp_f._get_mfg_custom_eui_64.return_value = old_eui64

    with pytest.raises(EzspError):
        await ezsp_f.write_custom_eui64(new_eui64)

    with pytest.raises(EzspError):
        await ezsp_f.write_custom_eui64(new_eui64, burn_into_userdata=True)

    ezsp_f.setMfgToken.assert_not_called()
    ezsp_f.setTokenData.assert_not_called()


async def test_write_custom_eui64_rcp(ezsp_f):
    """Test writing a custom EUI64 with RPC firmware."""

    old_eui64 = t.EUI64.convert("AA" * 8)
    new_eui64 = t.EUI64.convert("BB" * 8)

    ezsp_f.getEui64 = AsyncMock(return_value=[old_eui64])
    ezsp_f.setMfgToken = AsyncMock(return_value=[t.EmberStatus.INVALID_CALL])
    ezsp_f.setTokenData = AsyncMock(return_value=[t.EmberStatus.SUCCESS])

    # RCP firmware does not support manufacturing tokens
    ezsp_f.getMfgToken = AsyncMock(return_value=[b""])
    ezsp_f.getTokenData = AsyncMock(
        return_value=GetTokenDataRsp(status=t.EmberStatus.SUCCESS, value=b"\xFF" * 8)
    )

    await ezsp_f.write_custom_eui64(new_eui64)

    ezsp_f.setMfgToken.assert_not_called()
    ezsp_f.setTokenData.mock_calls == [
        call(
            t.NV3KeyId.NVM3KEY_STACK_RESTORED_EUI64,
            0,
            new_eui64.serialize(),
        )
    ]


async def test_write_nwk_update_id(ezsp_f):
    """Test writing network update ID to NVRAM token."""
    # Mock the token data response
    mock_token_data = t.NV3StackNetworkManagementToken(
        active_channels=t.Channels(0x07FFF800),
        manager_node_id=t.NWK(0x0000),
        update_id=t.uint8_t(0),
        padding=t.uint8_t(0),
    )

    ezsp_f.getTokenData = AsyncMock(
        return_value=GetTokenDataRsp(
            status=t.EmberStatus.SUCCESS,
            value=mock_token_data.serialize(),
        )
    )
    ezsp_f.setTokenData = AsyncMock(return_value=[t.EmberStatus.SUCCESS])

    # Test writing update ID
    await ezsp_f.write_nwk_update_id(7)

    # Verify getTokenData was called
    ezsp_f.getTokenData.assert_called_once_with(
        token=t.NV3KeyId.NVM3KEY_STACK_NETWORK_MANAGEMENT,
        index=0,
    )

    # Verify setTokenData was called with updated token
    ezsp_f.setTokenData.assert_called_once()
    call_args = ezsp_f.setTokenData.call_args[1]
    assert call_args["token"] == t.NV3KeyId.NVM3KEY_STACK_NETWORK_MANAGEMENT
    assert call_args["index"] == 0

    # Deserialize the token data to verify the update ID was set correctly
    updated_token, remaining = t.NV3StackNetworkManagementToken.deserialize(
        call_args["token_data"]
    )
    assert not remaining
    assert updated_token.update_id == 7
    assert updated_token.active_channels == t.Channels(0x07FFF800)
    assert updated_token.manager_node_id == t.NWK(0x0000)


async def test_write_nwk_update_id_nv3_unavailable(ezsp_f):
    """Test writing network update ID when NV3 is not available."""
    # Mock InvalidCommandError to simulate NV3 not being available
    ezsp_f.getTokenData = AsyncMock(
        side_effect=InvalidCommandError("NV3 not available")
    )

    # Should not raise an exception, just log a warning
    await ezsp_f.write_nwk_update_id(7)

    # Verify getTokenData was called
    ezsp_f.getTokenData.assert_called_once_with(
        token=t.NV3KeyId.NVM3KEY_STACK_NETWORK_MANAGEMENT,
        index=0,
    )


async def test_write_nwk_update_id_failure(ezsp_f):
    """Test writing network update ID when token read fails."""
    # Mock failure response
    ezsp_f.getTokenData = AsyncMock(
        return_value=GetTokenDataRsp(
            status=t.EmberStatus.INVALID_CALL,
            value=b"",
        )
    )

    # Should not raise an exception, just log a warning
    await ezsp_f.write_nwk_update_id(7)

    # Verify getTokenData was called
    ezsp_f.getTokenData.assert_called_once_with(
        token=t.NV3KeyId.NVM3KEY_STACK_NETWORK_MANAGEMENT,
        index=0,
    )


@patch.object(EZSP, "version", new_callable=AsyncMock)
@patch.object(EZSP, "reset", new_callable=AsyncMock)
@patch.object(EZSP, "get_xncp_features", new_callable=AsyncMock)
async def test_ezsp_init_zigbeed(xncp_mock, reset_mock, version_mock):
    """Test initialize method with a received startup reset frame."""
    ezsp = make_ezsp(
        config={
            **DEVICE_CONFIG,
            zigpy.config.CONF_DEVICE_PATH: "socket://localhost:1234",
        }
    )

    with patch("bellows.uart.connect") as conn_mock:
        gw_wait_reset_mock = conn_mock.return_value.wait_for_startup_reset = AsyncMock()
        await ezsp.connect()

    assert conn_mock.await_count == 1
    assert reset_mock.await_count == 0  # Reset is not called
    assert gw_wait_reset_mock.await_count == 1
    assert version_mock.await_count == 1


@patch.object(EZSP, "version", new_callable=AsyncMock)
@patch.object(EZSP, "reset", new_callable=AsyncMock)
@patch.object(EZSP, "get_xncp_features", new_callable=AsyncMock)
@patch("bellows.ezsp.NETWORK_COORDINATOR_STARTUP_RESET_WAIT", 0.01)
async def test_ezsp_init_zigbeed_timeout(reset_mock, xncp_mock, version_mock):
    """Test initialize method with a received startup reset frame."""
    ezsp = make_ezsp(
        config={
            **DEVICE_CONFIG,
            zigpy.config.CONF_DEVICE_PATH: "socket://localhost:1234",
        }
    )

    async def wait_forever(*args, **kwargs):
        return await asyncio.get_running_loop().create_future()

    with patch("bellows.uart.connect") as conn_mock:
        gw_wait_reset_mock = conn_mock.return_value.wait_for_startup_reset = AsyncMock(
            side_effect=wait_forever
        )
        await ezsp.connect()

    assert conn_mock.await_count == 1
    assert reset_mock.await_count == 1  # Reset will be called
    assert gw_wait_reset_mock.await_count == 1
    assert version_mock.await_count == 1


async def test_wait_for_stack_status(ezsp_f):
    assert not ezsp_f._stack_status_listeners[t.sl_Status.NETWORK_DOWN]

    # Cancellation clears handlers
    with ezsp_f.wait_for_stack_status(t.sl_Status.NETWORK_DOWN) as stack_status:
        with pytest.raises(asyncio.TimeoutError):
            async with asyncio_timeout(0.1):
                assert ezsp_f._stack_status_listeners[t.sl_Status.NETWORK_DOWN]
                await stack_status

    assert not ezsp_f._stack_status_listeners[t.sl_Status.NETWORK_DOWN]

    # Receiving multiple also works
    with ezsp_f.wait_for_stack_status(t.sl_Status.NETWORK_DOWN) as stack_status:
        ezsp_f.handle_callback("stackStatusHandler", [t.EmberStatus.NETWORK_UP])
        ezsp_f.handle_callback("stackStatusHandler", [t.EmberStatus.NETWORK_DOWN])
        ezsp_f.handle_callback("stackStatusHandler", [t.EmberStatus.NETWORK_DOWN])

        await stack_status

    assert not ezsp_f._stack_status_listeners[t.sl_Status.NETWORK_DOWN]


def test_ezsp_versions(ezsp_f):
    for version in range(4, EZSP_LATEST + 1):
        # Version 15 was never released, so skip it
        if version == 15:
            continue
        assert version in ezsp_f._BY_VERSION
        assert ezsp_f._BY_VERSION[version].__name__ == f"EZSPv{version}"
        assert ezsp_f._BY_VERSION[version].VERSION == version


async def test_config_initialize_husbzb1():
    """Test timeouts are properly set for HUSBZB-1."""

    ezsp = await make_connected_ezsp(version=4)

    ezsp.getConfigurationValue = AsyncMock(return_value=(t.EzspStatus.SUCCESS, 0))
    ezsp.setConfigurationValue = AsyncMock(return_value=(t.EzspStatus.SUCCESS,))
    ezsp.networkState = AsyncMock(return_value=(t.EmberNetworkStatus.JOINED_NETWORK,))

    expected_calls = [
        call(configId=t.EzspConfigId.CONFIG_SOURCE_ROUTE_TABLE_SIZE, value=16),
        call(configId=t.EzspConfigId.CONFIG_END_DEVICE_POLL_TIMEOUT, value=60),
        call(configId=t.EzspConfigId.CONFIG_END_DEVICE_POLL_TIMEOUT_SHIFT, value=8),
        call(configId=t.EzspConfigId.CONFIG_INDIRECT_TRANSMISSION_TIMEOUT, value=7680),
        call(configId=t.EzspConfigId.CONFIG_STACK_PROFILE, value=2),
        call(configId=t.EzspConfigId.CONFIG_SUPPORTED_NETWORKS, value=1),
        call(configId=t.EzspConfigId.CONFIG_MULTICAST_TABLE_SIZE, value=16),
        call(configId=t.EzspConfigId.CONFIG_TRUST_CENTER_ADDRESS_CACHE_SIZE, value=2),
        call(configId=t.EzspConfigId.CONFIG_SECURITY_LEVEL, value=5),
        call(configId=t.EzspConfigId.CONFIG_ADDRESS_TABLE_SIZE, value=16),
        call(configId=t.EzspConfigId.CONFIG_PAN_ID_CONFLICT_REPORT_THRESHOLD, value=2),
        call(configId=t.EzspConfigId.CONFIG_KEY_TABLE_SIZE, value=4),
        call(configId=t.EzspConfigId.CONFIG_MAX_END_DEVICE_CHILDREN, value=32),
        call(
            configId=t.EzspConfigId.CONFIG_APPLICATION_ZDO_FLAGS,
            value=(
                t.EmberZdoConfigurationFlags.APP_HANDLES_UNSUPPORTED_ZDO_REQUESTS
                | t.EmberZdoConfigurationFlags.APP_RECEIVES_SUPPORTED_ZDO_REQUESTS
            ),
        ),
        call(configId=t.EzspConfigId.CONFIG_PACKET_BUFFER_COUNT, value=255),
    ]

    await ezsp.write_config({})
    assert ezsp.setConfigurationValue.mock_calls == expected_calls


@pytest.mark.parametrize("version", EZSP._BY_VERSION)
async def test_config_initialize(version: int, caplog):
    """Test config initialization for all protocol versions."""

    ezsp = await make_connected_ezsp(version=version)

    with patch.object(ezsp, "_command", AsyncMock(return_value=[version, 2, 2046])):
        await ezsp.version()

    assert ezsp.ezsp_version == version

    ezsp.getConfigurationValue = AsyncMock(return_value=(t.EzspStatus.SUCCESS, 0))
    ezsp.setConfigurationValue = AsyncMock(return_value=(t.EzspStatus.SUCCESS,))
    ezsp.networkState = AsyncMock(return_value=(t.EmberNetworkStatus.JOINED_NETWORK,))

    ezsp.setValue = AsyncMock(return_value=(t.EzspStatus.SUCCESS,))
    ezsp.getValue = AsyncMock(return_value=(t.EzspStatus.SUCCESS, b"\xFF"))

    await ezsp.write_config({})

    with caplog.at_level(logging.DEBUG):
        ezsp.setConfigurationValue.return_value = (t.EzspStatus.ERROR_OUT_OF_MEMORY,)
        await ezsp.write_config({})

    assert "Could not set config" in caplog.text
    ezsp.setConfigurationValue.return_value = (t.EzspStatus.SUCCESS,)
    caplog.clear()

    # EZSPv6 does not set any values on startup
    if version < 7:
        return

    ezsp.setValue.reset_mock()
    ezsp.getValue.return_value = (t.EzspStatus.ERROR_INVALID_ID, b"")
    await ezsp.write_config({})
    assert len(ezsp.setValue.mock_calls) == 1

    ezsp.getValue = AsyncMock(return_value=(t.EzspStatus.SUCCESS, b"\xFF"))
    caplog.clear()

    with caplog.at_level(logging.DEBUG):
        ezsp.setValue.return_value = (t.EzspStatus.ERROR_INVALID_ID,)
        await ezsp.write_config({})

    assert "Could not set value" in caplog.text
    ezsp.setValue.return_value = (t.EzspStatus.SUCCESS,)
    caplog.clear()


async def test_cfg_initialize_skip():
    """Test initialization."""

    ezsp = await make_connected_ezsp(version=4)

    ezsp.networkState = AsyncMock(return_value=(t.EmberNetworkStatus.JOINED_NETWORK,))

    p1 = patch.object(
        ezsp,
        "setConfigurationValue",
        new=AsyncMock(return_value=(t.EzspStatus.SUCCESS,)),
    )
    p2 = patch.object(
        ezsp,
        "getConfigurationValue",
        new=AsyncMock(return_value=(t.EzspStatus.SUCCESS, 22)),
    )
    with p1, p2:
        await ezsp.write_config({"CONFIG_END_DEVICE_POLL_TIMEOUT": None})

        # Config not set when it is explicitly disabled
        with pytest.raises(AssertionError):
            ezsp.setConfigurationValue.assert_called_with(
                configId=t.EzspConfigId.CONFIG_END_DEVICE_POLL_TIMEOUT, value=ANY
            )

    with p1, p2:
        await ezsp.write_config({"CONFIG_MULTICAST_TABLE_SIZE": 123})

        # Config is overridden
        ezsp.setConfigurationValue.assert_any_call(
            configId=t.EzspConfigId.CONFIG_MULTICAST_TABLE_SIZE, value=123
        )

    with p1, p2:
        await ezsp.write_config({})

        # Config is set by default
        ezsp.setConfigurationValue.assert_any_call(
            configId=t.EzspConfigId.CONFIG_END_DEVICE_POLL_TIMEOUT, value=ANY
        )


async def test_reset_custom_eui64(ezsp_f):
    """Test resetting custom EUI64."""
    # No NV3 interface
    ezsp_f.getTokenData = AsyncMock(side_effect=InvalidCommandError)
    ezsp_f.setTokenData = AsyncMock(return_value=[t.EmberStatus.SUCCESS])
    await ezsp_f.reset_custom_eui64()

    assert len(ezsp_f.setTokenData.mock_calls) == 0

    # With NV3 interface
    ezsp_f.getTokenData = AsyncMock(
        return_value=GetTokenDataRsp(status=t.EmberStatus.SUCCESS, value=b"\xAB" * 8)
    )
    await ezsp_f.reset_custom_eui64()
    assert ezsp_f.setTokenData.mock_calls == [
        call(t.NV3KeyId.CREATOR_STACK_RESTORED_EUI64, 0, t.LVBytes32(b"\xFF" * 8))
    ]


def test_empty_frame_received(ezsp_f):
    """Test dropping of invalid, empty frames."""
    ezsp_f._protocol = MagicMock(spec_set=ezsp_f._protocol)
    ezsp_f._protocol.__call__ = MagicMock()
    ezsp_f.frame_received(b"")

    assert ezsp_f._protocol.__call__.mock_calls == []


def test_frame_parsing_error_doesnt_disconnect(ezsp_f, caplog):
    """Test that frame parsing error doesn't trigger a disconnect."""
    ezsp_f._protocol = MagicMock(spec_set=ezsp_f._protocol, side_effect=RuntimeError())

    with caplog.at_level(logging.WARNING):
        ezsp_f.frame_received(b"test")

    assert "Failed to parse frame" in caplog.text
