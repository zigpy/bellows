"""EZSP protocol."""

from __future__ import annotations

import asyncio
import collections
import contextlib
import dataclasses
import functools
import logging
import sys
from typing import Any, Callable, Generator
import urllib.parse

from bellows.ash import NcpFailure

if sys.version_info[:2] < (3, 11):
    from async_timeout import timeout as asyncio_timeout  # pragma: no cover
else:
    from asyncio import timeout as asyncio_timeout  # pragma: no cover

import zigpy.config

import bellows.config as conf
from bellows.exception import EzspError, InvalidCommandError
from bellows.ezsp import xncp
from bellows.ezsp.config import DEFAULT_CONFIG, RuntimeConfig, ValueConfig
from bellows.ezsp.xncp import FirmwareFeatures, FlowControlType
import bellows.types as t
import bellows.uart

from . import v4, v5, v6, v7, v8, v9, v10, v11, v12, v13, v14

EZSP_LATEST = v14.EZSPv14.VERSION
LOGGER = logging.getLogger(__name__)
MTOR_MIN_INTERVAL = 60
MTOR_MAX_INTERVAL = 3600
MTOR_ROUTE_ERROR_THRESHOLD = 8
MTOR_DELIVERY_FAIL_THRESHOLD = 8

UART_PROBE_TIMEOUT = 3
NETWORK_PROBE_TIMEOUT = 7
NETWORK_OPS_TIMEOUT = 10
NETWORK_COORDINATOR_STARTUP_RESET_WAIT = 1


class EZSP:
    _BY_VERSION = {
        v4.EZSPv4.VERSION: v4.EZSPv4,
        v5.EZSPv5.VERSION: v5.EZSPv5,
        v6.EZSPv6.VERSION: v6.EZSPv6,
        v7.EZSPv7.VERSION: v7.EZSPv7,
        v8.EZSPv8.VERSION: v8.EZSPv8,
        v9.EZSPv9.VERSION: v9.EZSPv9,
        v10.EZSPv10.VERSION: v10.EZSPv10,
        v11.EZSPv11.VERSION: v11.EZSPv11,
        v12.EZSPv12.VERSION: v12.EZSPv12,
        v13.EZSPv13.VERSION: v13.EZSPv13,
        v14.EZSPv14.VERSION: v14.EZSPv14,
    }

    def __init__(self, device_config: dict, application: Any | None = None):
        self._config = device_config
        self._callbacks = {}
        self._ezsp_event = asyncio.Event()
        self._ezsp_version = v4.EZSPv4.VERSION
        self._xncp_features = FirmwareFeatures.NONE
        self._gw = None
        self._protocol = None
        self._application = application

        self._stack_status_listeners: collections.defaultdict[
            t.sl_Status, list[asyncio.Future]
        ] = collections.defaultdict(list)

        self.add_callback(self.stack_status_callback)

    def stack_status_callback(self, frame_name: str, args: list[Any]) -> None:
        """Callback for `stackStatusHandler` messages."""
        if frame_name != "stackStatusHandler":
            return

        status = t.sl_Status.from_ember_status(args[0])

        for listener in self._stack_status_listeners[status]:
            listener.set_result(status)

    @contextlib.contextmanager
    def wait_for_stack_status(self, status: t.sl_Status) -> Generator[asyncio.Future]:
        """Waits for a `stackStatusHandler` to come in with the provided status."""
        listeners = self._stack_status_listeners[status]

        future = asyncio.get_running_loop().create_future()

        @future.add_done_callback
        def maybe_remove(_):
            with contextlib.suppress(ValueError):
                listeners.remove(future)

        listeners.append(future)

        try:
            yield future
        finally:
            with contextlib.suppress(ValueError):
                listeners.remove(future)

    @property
    def is_tcp_serial_port(self) -> bool:
        parsed_path = urllib.parse.urlparse(self._config[conf.CONF_DEVICE_PATH])
        return parsed_path.scheme == "socket"

    async def startup_reset(self) -> None:
        """Start EZSP and reset the stack."""
        # `zigbeed` resets on startup
        if self.is_tcp_serial_port:
            try:
                async with asyncio_timeout(NETWORK_COORDINATOR_STARTUP_RESET_WAIT):
                    await self._gw.wait_for_startup_reset()
            except asyncio.TimeoutError:
                pass
            else:
                LOGGER.debug("Received a reset on startup, not resetting again")
                self.start_ezsp()

        if not self.is_ezsp_running:
            await self.reset()

        await self.version()
        await self.get_xncp_features()

    async def connect(self, *, use_thread: bool = True) -> None:
        assert self._gw is None
        self._gw = await bellows.uart.connect(self._config, self, use_thread=use_thread)

        try:
            self._protocol = v4.EZSPv4(self.handle_callback, self._gw)
            await self.startup_reset()
        except Exception:
            await self.disconnect()
            raise

    async def reset(self):
        LOGGER.debug("Resetting EZSP")
        self.stop_ezsp()
        await self._gw.reset()

        # Always switch back to protocol v4 after a reset
        self._switch_protocol_version(v4.EZSPv4.VERSION)
        self.start_ezsp()

    def _switch_protocol_version(self, version: int) -> None:
        LOGGER.debug("Switching to EZSP protocol version %d", version)
        self._ezsp_version = version

        if version not in self._BY_VERSION:
            LOGGER.warning(
                "Protocol version %s is not supported, using version %s instead",
                version,
                EZSP_LATEST,
            )
            # We replace the protocol object but keep the version correct
            version = EZSP_LATEST

        self._protocol = self._BY_VERSION[version](self.handle_callback, self._gw)

    async def version(self):
        ver, stack_type, stack_version = await self._command(
            "version", desiredProtocolVersion=self.ezsp_version
        )
        if ver != self.ezsp_version:
            self._switch_protocol_version(ver)
            await self._command("version", desiredProtocolVersion=ver)

        LOGGER.debug(
            ("EZSP Stack Type: %s" ", Stack Version: %04x" ", Protocol version: %s"),
            stack_type,
            stack_version,
            ver,
        )

    async def get_xncp_features(self) -> xncp.FirmwareFeatures:
        # Some older gateways seem to have their own XNCP protocol. Ignore them.
        if self._ezsp_version < 13:
            return FirmwareFeatures.NONE

        try:
            self._xncp_features = await self.xncp_get_supported_firmware_features()
        except InvalidCommandError:
            self._xncp_features = xncp.FirmwareFeatures.NONE

        # Disable the XNCP feature flag, it doesn't seem to work correctly
        if FirmwareFeatures.MEMBER_OF_ALL_GROUPS in self._xncp_features:
            _, _, version = await self.get_board_info()

            if version == "7.4.4.0 build 0":
                self._xncp_features &= ~FirmwareFeatures.MEMBER_OF_ALL_GROUPS

        LOGGER.debug("XNCP features: %s", self._xncp_features)
        return self._xncp_features

    async def disconnect(self):
        self.stop_ezsp()
        if self._gw:
            await self._gw.disconnect()
            self._gw = None

    async def _command(self, name: str, *args: Any, **kwargs: Any) -> Any:
        command = getattr(self._protocol, name)

        if not self.is_ezsp_running:
            LOGGER.debug(
                "Couldn't send command %s(%s, %s). EZSP is not running",
                name,
                args,
                kwargs,
            )
            raise EzspError("EZSP is not running")

        return await command(*args, **kwargs)

    async def _list_command(
        self, name, item_frames, completion_frame, spos, *args, **kwargs
    ):
        """Run a command, returning result callbacks as a list"""
        queue = asyncio.Queue()
        results = []

        with self.callback_for_commands(
            commands=set(item_frames) | {completion_frame},
            callback=lambda command, response: queue.put_nowait((command, response)),
        ):
            v = await self._command(name, *args, **kwargs)
            if t.sl_Status.from_ember_status(v[0]) != t.sl_Status.OK:
                raise Exception(v)

            while True:
                command, response = await queue.get()
                if command == completion_frame:
                    if t.sl_Status.from_ember_status(response[spos]) != t.sl_Status.OK:
                        raise Exception(response)

                    break

                results.append(response)

        return results

    @contextlib.contextmanager
    def callback_for_commands(
        self, commands: set[str], callback: Callable
    ) -> Generator[None]:
        def cb(frame_name, response):
            if frame_name in commands:
                callback(frame_name, response)

        cbid = self.add_callback(cb)

        try:
            yield
        finally:
            self.remove_callback(cbid)

    startScan = functools.partialmethod(
        _list_command,
        "startScan",
        ["energyScanResultHandler", "networkFoundHandler"],
        "scanCompleteHandler",
        1,
    )
    pollForData = functools.partialmethod(
        _list_command,
        "pollForData",
        ["pollHandler"],
        "pollCompleteHandler",
        0,
    )
    zllStartScan = functools.partialmethod(
        _list_command,
        "zllStartScan",
        ["zllNetworkFoundHandler"],
        "zllScanCompleteHandler",
        0,
    )
    rf4ceDiscovery = functools.partialmethod(
        _list_command,
        "rf4ceDiscovery",
        ["rf4ceDiscoveryResponseHandler"],
        "rf4ceDiscoveryCompleteHandler",
        0,
    )

    async def leaveNetwork(self, timeout: float | int = NETWORK_OPS_TIMEOUT) -> None:
        """Send leaveNetwork command and wait for stackStatusHandler frame."""
        stack_status = asyncio.Future()

        with self.wait_for_stack_status(t.sl_Status.NETWORK_DOWN) as stack_status:
            (status,) = await self._command("leaveNetwork")
            if status != t.sl_Status.OK:
                raise EzspError(f"failed to leave network: {status.name}")

            async with asyncio_timeout(timeout):
                await stack_status

    def connection_lost(self, exc):
        """Lost serial connection."""
        if self._application is not None:
            self._application.connection_lost(exc)

    def enter_failed_state(self, code: t.NcpResetCode) -> None:
        """UART received reset code."""
        self.connection_lost(NcpFailure(code=code))

    def __getattr__(self, name: str) -> Callable:
        if name not in self._protocol.COMMANDS:
            return getattr(self._protocol, name)

        return functools.partial(self._command, name)

    async def formNetwork(self, parameters: t.EmberNetworkParameters) -> None:
        with self.wait_for_stack_status(t.sl_Status.NETWORK_UP) as stack_status:
            v = await self._command("formNetwork", parameters=parameters)

            if t.sl_Status.from_ember_status(v[0]) != t.sl_Status.OK:
                raise zigpy.exceptions.FormationFailure(f"Failure forming network: {v}")

            async with asyncio_timeout(NETWORK_OPS_TIMEOUT):
                await stack_status

    def frame_received(self, data: bytes) -> None:
        """Handle a received EZSP frame

        The protocol has taken care of UART specific framing etc, so we should
        just have EZSP application stuff here, with all escaping/stuffing and
        data randomization removed.
        """

        if self._protocol is None:
            LOGGER.debug("Ignoring frame, protocol is not configured: %r", data)
            return

        if not data:
            LOGGER.debug("Ignoring empty frame")
            return

        try:
            self._protocol(data)
        except Exception:
            LOGGER.warning("Failed to parse frame, ignoring")

    async def get_board_info(
        self,
    ) -> tuple[str, str, str | None] | tuple[None, None, str | None]:
        """Return board info."""

        tokens: dict[t.EzspMfgTokenId, str | None] = {}

        for token_id in (t.EzspMfgTokenId.MFG_STRING, t.EzspMfgTokenId.MFG_BOARD_NAME):
            value = await self.get_mfg_token(token_id)

            # Tokens are fixed-length and initially filled with \xFF but also can end
            # with \x00
            while value.endswith((b"\xFF", b"\x00")):
                value = value.rstrip(b"\xFF").rstrip(b"\x00")

            try:
                result = value.decode("utf-8")
            except UnicodeDecodeError:
                result = "0x" + value.hex().upper()

            tokens[token_id] = result or None

        (status, ver_info_bytes) = await self.getValue(
            valueId=t.EzspValueId.VALUE_VERSION_INFO
        )
        version = None

        if t.sl_Status.from_ember_status(status) == t.sl_Status.OK:
            build, ver_info_bytes = t.uint16_t.deserialize(ver_info_bytes)
            major, ver_info_bytes = t.uint8_t.deserialize(ver_info_bytes)
            minor, ver_info_bytes = t.uint8_t.deserialize(ver_info_bytes)
            patch, ver_info_bytes = t.uint8_t.deserialize(ver_info_bytes)
            special, ver_info_bytes = t.uint8_t.deserialize(ver_info_bytes)
            version = f"{major}.{minor}.{patch}.{special} build {build}"
            build_string = None

            if FirmwareFeatures.BUILD_STRING in self._xncp_features:
                with contextlib.suppress(InvalidCommandError):
                    build_string = await self.xncp_get_build_string()

            if build_string:
                version = f"{version} ({build_string})"

        return (
            tokens[t.EzspMfgTokenId.MFG_STRING],
            tokens[t.EzspMfgTokenId.MFG_BOARD_NAME],
            version,
        )

    async def _get_nv3_restored_eui64_key(self) -> t.NV3KeyId | None:
        """Get the NV3 key for the device's restored EUI64, if one exists."""
        for key in (
            t.NV3KeyId.CREATOR_STACK_RESTORED_EUI64,  # NCP firmware
            t.NV3KeyId.NVM3KEY_STACK_RESTORED_EUI64,  # RCP firmware
        ):
            try:
                rsp = await self.getTokenData(token=key, index=0)
            except (InvalidCommandError, AttributeError):
                # Either the command doesn't exist in the EZSP version, or the command
                # is not implemented in the firmware
                return None

            if t.sl_Status.from_ember_status(rsp.status) == t.sl_Status.OK:
                nv3_restored_eui64, _ = t.EUI64.deserialize(rsp.value)
                LOGGER.debug("NV3 restored EUI64: %s=%s", key, nv3_restored_eui64)

                return key

        return None

    async def get_mfg_token(self, token: t.EzspMfgTokenId) -> bytes:
        (value,) = await self.getMfgToken(tokenId=token)
        LOGGER.debug("Read manufacturing token %s: %s", token.name, value)

        override_value = None

        if FirmwareFeatures.MFG_TOKEN_OVERRIDES in self._xncp_features:
            with contextlib.suppress(InvalidCommandError):
                override_value = await self.xncp_get_mfg_token_override(token)

            LOGGER.debug("XNCP override token %s: %s", token.name, override_value)

        return override_value or value

    async def _get_mfg_custom_eui_64(self) -> t.EUI64 | None:
        """Get the custom EUI 64 manufacturing token, if it has a valid value."""
        data = await self.get_mfg_token(t.EzspMfgTokenId.MFG_CUSTOM_EUI_64)

        # Manufacturing tokens do not exist in RCP firmware: all reads are empty
        if not data:
            raise ValueError("Firmware does not support MFG_CUSTOM_EUI_64 token")

        mfg_custom_eui64, _ = t.EUI64.deserialize(data)

        if mfg_custom_eui64 == t.EUI64.convert("FF:FF:FF:FF:FF:FF:FF:FF"):
            return None

        return mfg_custom_eui64

    async def can_burn_userdata_custom_eui64(self) -> bool:
        """Checks if the device EUI64 can be burned into USERDATA."""
        try:
            return await self._get_mfg_custom_eui_64() is None
        except ValueError:
            return False

    async def can_rewrite_custom_eui64(self) -> bool:
        """Checks if the device EUI64 can be written any number of times."""
        return await self._get_nv3_restored_eui64_key() is not None

    async def reset_custom_eui64(self) -> None:
        """Reset the custom EUI64, if possible."""

        nv3_eui64_key = await self._get_nv3_restored_eui64_key()
        if nv3_eui64_key is None:
            return

        (status,) = await self.setTokenData(
            nv3_eui64_key,
            0,
            t.LVBytes32(t.EUI64.convert("FF:FF:FF:FF:FF:FF:FF:FF").serialize()),
        )
        assert t.sl_Status.from_ember_status(status) == t.sl_Status.OK

    async def write_custom_eui64(
        self, ieee: t.EUI64, *, burn_into_userdata: bool = False
    ) -> None:
        """Sets the device's IEEE address."""

        (current_eui64,) = await self.getEui64()
        if current_eui64 == ieee:
            return

        # A custom EUI64 can be stored in NV3 storage (rewritable)
        nv3_eui64_key = await self._get_nv3_restored_eui64_key()

        try:
            mfg_custom_eui64 = await self._get_mfg_custom_eui_64()
        except ValueError:
            mfg_custom_eui64 = None

        if nv3_eui64_key is not None:
            # Prefer NV3 storage over MFG_CUSTOM_EUI_64, as it can be rewritten
            (status,) = await self.setTokenData(
                token=nv3_eui64_key,
                index=0,
                token_data=t.LVBytes32(ieee.serialize()),
            )
            assert t.sl_Status.from_ember_status(status) == t.sl_Status.OK
        elif mfg_custom_eui64 is None and burn_into_userdata:
            (status,) = await self.setMfgToken(
                tokenId=t.EzspMfgTokenId.MFG_CUSTOM_EUI_64,
                tokenData=ieee.serialize(),
            )
            assert t.sl_Status.from_ember_status(status) == t.sl_Status.OK
        elif mfg_custom_eui64 is None and not burn_into_userdata:
            raise EzspError(
                f"Firmware does not support NV3 tokens. Custom IEEE {ieee} will not be"
                f" written unless `burn_into_userdata` is passed."
            )
        else:
            raise EzspError(
                f"Firmware does not support NV3 tokens. Custom device IEEE address has"
                f" already been written once and is set to {mfg_custom_eui64}, it"
                f" cannot be written again without erasing flash."
            )

    def add_callback(self, cb):
        id_ = hash(cb)
        while id_ in self._callbacks:
            id_ += 1
        self._callbacks[id_] = cb
        return id_

    def remove_callback(self, id_):
        return self._callbacks.pop(id_)

    def handle_callback(self, *args):
        for _callback_id, handler in self._callbacks.items():
            try:
                handler(*args)
            except Exception as e:
                LOGGER.exception("Exception running handler", exc_info=e)

    async def set_source_routing(self) -> None:
        """Enable source routing on NCP."""
        res = await self.setConcentrator(
            on=True,
            concentratorType=t.EmberConcentratorType.HIGH_RAM_CONCENTRATOR,
            minTime=MTOR_MIN_INTERVAL,
            maxTime=MTOR_MAX_INTERVAL,
            routeErrorThreshold=MTOR_ROUTE_ERROR_THRESHOLD,
            deliveryFailureThreshold=MTOR_DELIVERY_FAIL_THRESHOLD,
            maxHops=0,
        )
        LOGGER.debug("Set concentrator type: %s", res)
        if t.sl_Status.from_ember_status(res[0]) != t.sl_Status.OK:
            LOGGER.warning("Couldn't set concentrator type %s: %s", True, res)

        if self._ezsp_version >= 8:
            await self.setSourceRouteDiscoveryMode(mode=1)

    def start_ezsp(self):
        """Mark EZSP as running."""
        self._ezsp_event.set()

    def stop_ezsp(self):
        """Mark EZSP stopped."""
        self._ezsp_event.clear()

    @property
    def is_ezsp_running(self):
        """Return True if EZSP is running."""
        return self._ezsp_event.is_set()

    @property
    def ezsp_version(self):
        """Return protocol version."""
        return self._ezsp_version

    @property
    def types(self):
        """Return EZSP types for this specific version."""
        return self._protocol.types

    async def write_config(self, config: dict) -> None:
        """Initialize EmberZNet Stack."""
        config = self._protocol.SCHEMAS[conf.CONF_EZSP_CONFIG](config)

        # Not all config will be present in every EZSP version so only use valid keys
        ezsp_config = {}
        ezsp_values = {}

        for cfg in DEFAULT_CONFIG[self._ezsp_version]:
            if isinstance(cfg, RuntimeConfig):
                ezsp_config[cfg.config_id.name] = dataclasses.replace(
                    cfg, config_id=t.EzspConfigId[cfg.config_id.name]
                )
            elif isinstance(cfg, ValueConfig):
                ezsp_values[cfg.value_id.name] = dataclasses.replace(
                    cfg, value_id=t.EzspValueId[cfg.value_id.name]
                )

        # Override the defaults with user-specified values (or `None` for deletions)
        for name, value in config.items():
            if value is None:
                ezsp_config.pop(name)
                continue

            ezsp_config[name] = RuntimeConfig(
                config_id=t.EzspConfigId[name],
                value=value,
            )

        # Make sure CONFIG_PACKET_BUFFER_COUNT is always set last
        if t.EzspConfigId.CONFIG_PACKET_BUFFER_COUNT.name in ezsp_config:
            ezsp_config = {
                **ezsp_config,
                t.EzspConfigId.CONFIG_PACKET_BUFFER_COUNT.name: ezsp_config[
                    t.EzspConfigId.CONFIG_PACKET_BUFFER_COUNT.name
                ],
            }

        # First, set the values
        for cfg in ezsp_values.values():
            # XXX: A read failure does not mean the value is not writeable!
            status, current_value = await self.getValue(valueId=cfg.value_id)

            if t.sl_Status.from_ember_status(status) == t.sl_Status.OK:
                current_value, _ = type(cfg.value).deserialize(current_value)
            else:
                current_value = None

            LOGGER.debug(
                "Setting value %s = %s (old value %s)",
                cfg.value_id.name,
                cfg.value,
                current_value,
            )

            (status,) = await self.setValue(
                valueId=cfg.value_id, value=cfg.value.serialize()
            )

            if t.sl_Status.from_ember_status(status) != t.sl_Status.OK:
                LOGGER.debug(
                    "Could not set value %s = %s: %s",
                    cfg.value_id.name,
                    cfg.value,
                    status,
                )
                continue

        # Finally, set the config
        for cfg in ezsp_config.values():
            (status, current_value) = await self.getConfigurationValue(
                configId=cfg.config_id
            )

            # Only grow some config entries, all others should be set
            if (
                t.sl_Status.from_ember_status(status) == t.sl_Status.OK
                and cfg.minimum
                and current_value >= cfg.value
            ):
                LOGGER.debug(
                    "Current config %s = %s exceeds the default of %s, skipping",
                    cfg.config_id.name,
                    current_value,
                    cfg.value,
                )
                continue

            LOGGER.debug(
                "Setting config %s = %s (old value %s)",
                cfg.config_id.name,
                cfg.value,
                current_value,
            )

            (status,) = await self.setConfigurationValue(
                configId=cfg.config_id, value=cfg.value
            )
            if t.sl_Status.from_ember_status(status) != t.sl_Status.OK:
                LOGGER.debug(
                    "Could not set config %s = %s: %s",
                    cfg.config_id,
                    cfg.value,
                    status,
                )
                continue

    async def send_xncp_frame(
        self, payload: xncp.XncpCommandPayload
    ) -> xncp.XncpCommandPayload:
        """Send an XNCP frame."""
        req_frame = xncp.XncpCommand.from_payload(payload)
        LOGGER.debug("Sending XNCP frame: %s", req_frame)
        status, data = await self.customFrame(req_frame.serialize())

        if status != t.EmberStatus.SUCCESS:
            raise InvalidCommandError("XNCP is not supported")

        try:
            rsp_frame = xncp.XncpCommand.from_bytes(data)
        except ValueError:
            raise InvalidCommandError(f"Invalid XNCP response: {data!r}")

        if isinstance(rsp_frame.payload, xncp.Unknown):
            raise InvalidCommandError(f"XNCP firmware does not support {payload}")

        LOGGER.debug("Received XNCP frame: %s", rsp_frame)

        if rsp_frame.status != t.EmberStatus.SUCCESS:
            raise InvalidCommandError(f"XNCP response error: {rsp_frame.status}")

        return rsp_frame.payload

    async def xncp_get_supported_firmware_features(self) -> xncp.FirmwareFeatures:
        """Get supported firmware extensions."""
        rsp = await self.send_xncp_frame(xncp.GetSupportedFeaturesReq())
        return rsp.features

    async def xncp_set_manual_source_route(
        self, destination: t.NWK, route: list[t.NWK]
    ) -> None:
        """Set a manual source route."""
        await self.send_xncp_frame(
            xncp.SetSourceRouteReq(
                destination=destination,
                source_route=route,
            )
        )

    async def xncp_get_mfg_token_override(self, token: t.EzspMfgTokenId) -> bytes:
        """Get manufacturing token override."""
        rsp = await self.send_xncp_frame(xncp.GetMfgTokenOverrideReq(token=token))
        return rsp.value

    async def xncp_get_build_string(self) -> str:
        """Get build string."""
        rsp = await self.send_xncp_frame(xncp.GetBuildStringReq())
        return rsp.build_string.decode("utf-8")

    async def xncp_get_flow_control_type(self) -> FlowControlType:
        """Get flow control type."""
        rsp = await self.send_xncp_frame(xncp.GetFlowControlTypeReq())
        return rsp.flow_control_type
