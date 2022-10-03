"""EZSP protocol."""

from __future__ import annotations

import asyncio
import functools
import logging
from typing import Any, Callable, Dict, List, Tuple, Union
import urllib.parse

import zigpy.config

from bellows.config import (
    CONF_DEVICE,
    CONF_DEVICE_BAUDRATE,
    CONF_DEVICE_PATH,
    SCHEMA_DEVICE,
)
from bellows.exception import EzspError
import bellows.types as t
import bellows.uart

from . import v4, v5, v6, v7, v8, v9

EZSP_LATEST = v9.EZSP_VERSION
PROBE_TIMEOUT = 3
NETWORK_OPS_TIMEOUT = 10
LOGGER = logging.getLogger(__name__)
MTOR_MIN_INTERVAL = 10
MTOR_MAX_INTERVAL = 90
MTOR_ROUTE_ERROR_THRESHOLD = 4
MTOR_DELIVERY_FAIL_THRESHOLD = 3

NETWORK_COORDINATOR_STARTUP_RESET_WAIT = 1


class EZSP:
    _BY_VERSION = {
        v4.EZSP_VERSION: v4.EZSPv4,
        v5.EZSP_VERSION: v5.EZSPv5,
        v6.EZSP_VERSION: v6.EZSPv6,
        v7.EZSP_VERSION: v7.EZSPv7,
        v8.EZSP_VERSION: v8.EZSPv8,
        v9.EZSP_VERSION: v9.EZSPv9,
    }

    def __init__(self, device_config: Dict):
        self._config = device_config
        self._callbacks = {}
        self._ezsp_event = asyncio.Event()
        self._ezsp_version = v4.EZSP_VERSION
        self._gw = None
        self._protocol = None

    @classmethod
    async def probe(cls, device_config: Dict) -> bool | dict[str, int | str | bool]:
        """Probe port for the device presence."""
        for config in ({**device_config, CONF_DEVICE_BAUDRATE: 115200}, device_config):
            ezsp = cls(SCHEMA_DEVICE(config))
            try:
                await asyncio.wait_for(ezsp._probe(), timeout=PROBE_TIMEOUT)
                return config
            except Exception as exc:
                LOGGER.debug(
                    "Unsuccessful radio probe of '%s' port",
                    device_config[CONF_DEVICE_PATH],
                    exc_info=exc,
                )
            finally:
                ezsp.close()

        return False

    async def _probe(self) -> None:
        """Open port and try sending a command"""
        await self.connect()
        await self._startup_reset()
        await self.version()

    async def _startup_reset(self):
        """Start EZSP and reset the stack."""
        # `zigbeed` resets on startup
        parsed_path = urllib.parse.urlparse(self._config[CONF_DEVICE_PATH])
        if parsed_path.scheme == "socket":
            try:
                await asyncio.wait_for(
                    self._gw.wait_for_startup_reset(),
                    NETWORK_COORDINATOR_STARTUP_RESET_WAIT,
                )
            except asyncio.TimeoutError:
                pass
            else:
                LOGGER.debug("Received a reset on startup, not resetting again")
                self.start_ezsp()

        if not self.is_ezsp_running:
            await self.reset()

    @classmethod
    async def initialize(cls, zigpy_config: Dict) -> "EZSP":
        """Return initialized EZSP instance."""
        ezsp = cls(zigpy_config[CONF_DEVICE])
        await ezsp.connect()

        try:
            await ezsp._startup_reset()
            await ezsp.version()
            await ezsp._protocol.initialize(zigpy_config)

            if zigpy_config[zigpy.config.CONF_SOURCE_ROUTING]:
                await ezsp.set_source_routing()
        except Exception:
            ezsp.close()
            raise

        return ezsp

    async def connect(self) -> None:
        assert self._gw is None
        self._gw = await bellows.uart.connect(self._config, self)
        self._protocol = v4.EZSPv4(self.handle_callback, self._gw)

    async def reset(self):
        LOGGER.debug("Resetting EZSP")
        self.stop_ezsp()
        await self._gw.reset()
        self.start_ezsp()

    async def version(self):
        ver, stack_type, stack_version = await self._command(
            "version", self.ezsp_version
        )
        if ver != self.ezsp_version:
            self._ezsp_version = ver
            LOGGER.debug("Switching to EZSP protocol version %d", self.ezsp_version)
            try:
                protcol_cls = self._BY_VERSION[ver]
            except KeyError:
                LOGGER.warning(
                    "Protocol version %s is not supported, using version %s instead",
                    ver,
                    EZSP_LATEST,
                )
                protcol_cls = self._BY_VERSION[EZSP_LATEST]
            self._protocol = protcol_cls(self.handle_callback, self._gw)
            await self._command("version", ver)
        LOGGER.debug(
            "EZSP Stack Type: %s, Stack Version: %04x, Protocol version: %s",
            stack_type,
            stack_version,
            ver,
        )

    def close(self):
        self.stop_ezsp()
        if self._gw:
            self._gw.close()
            self._gw = None

    def _command(self, name: str, *args: Tuple[Any, ...]) -> asyncio.Future:
        if not self.is_ezsp_running:
            LOGGER.debug(
                "Couldn't send command %s(%s). EZSP is not running", name, args
            )
            raise EzspError("EZSP is not running")

        return self._protocol.command(name, *args)

    async def _list_command(self, name, item_frames, completion_frame, spos, *args):
        """Run a command, returning result callbacks as a list"""
        fut = asyncio.Future()
        results = []

        def cb(frame_name, response):
            if frame_name in item_frames:
                results.append(response)
            elif frame_name == completion_frame:
                fut.set_result(response)

        cbid = self.add_callback(cb)
        try:
            v = await self._command(name, *args)
            if v[0] != t.EmberStatus.SUCCESS:
                raise Exception(v)
            v = await fut
            if v[spos] != t.EmberStatus.SUCCESS:
                raise Exception(v)
        finally:
            self.remove_callback(cbid)

        return results

    startScan = functools.partialmethod(
        _list_command,
        "startScan",
        ["energyScanResultHandler", "networkFoundHandler"],
        "scanCompleteHandler",
        1,
    )
    pollForData = functools.partialmethod(
        _list_command, "pollForData", ["pollHandler"], "pollCompleteHandler", 0
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

    async def leaveNetwork(
        self, timeout: Union[float, int] = NETWORK_OPS_TIMEOUT
    ) -> List:
        """Send leaveNetwork command and wait for stackStatusHandler frame."""
        stack_status = asyncio.Future()

        def cb(frame_name: str, response: List) -> None:
            if (
                frame_name == "stackStatusHandler"
                and response[0] == t.EmberStatus.NETWORK_DOWN
            ):
                stack_status.set_result(response)

        cb_id = self.add_callback(cb)
        try:
            (status,) = await self._command("leaveNetwork")
            if status != t.EmberStatus.SUCCESS:
                raise EzspError(f"failed to leave network: {status.name}")
            result = await asyncio.wait_for(stack_status, timeout=timeout)
            return result
        finally:
            self.remove_callback(cb_id)

    def connection_lost(self, exc):
        """Lost serial connection."""
        LOGGER.debug(
            "%s connection lost unexpectedly: %s", self._config[CONF_DEVICE_PATH], exc
        )
        self.enter_failed_state(f"Serial connection loss: {exc!r}")

    def enter_failed_state(self, error):
        """UART received error frame."""
        if self._callbacks:
            LOGGER.error("NCP entered failed state. Requesting APP controller restart")
            self.close()
            self.handle_callback("_reset_controller_application", (error,))
        else:
            LOGGER.info(
                "NCP entered failed state. No application handler registered, ignoring..."
            )

    def __getattr__(self, name: str) -> Callable:
        if name not in self._protocol.COMMANDS:
            return getattr(self._protocol, name)

        return functools.partial(self._command, name)

    async def formNetwork(self, parameters):  # noqa: N802
        fut = asyncio.Future()

        def cb(frame_name, response):
            nonlocal fut
            if frame_name == "stackStatusHandler":
                fut.set_result(response)

        self.add_callback(cb)
        v = await self._command("formNetwork", parameters)
        if v[0] != self.types.EmberStatus.SUCCESS:
            raise Exception(f"Failure forming network: {v}")

        v = await fut
        if v[0] != self.types.EmberStatus.NETWORK_UP:
            raise Exception(f"Failure forming network: {v}")

        return v

    def frame_received(self, data: bytes) -> None:
        """Handle a received EZSP frame

        The protocol has taken care of UART specific framing etc, so we should
        just have EZSP application stuff here, with all escaping/stuffing and
        data randomization removed.
        """
        self._protocol(data)

    async def get_board_info(self) -> Tuple[str, str, str]:
        """Return board info."""

        tokens = []

        for token in (t.EzspMfgTokenId.MFG_STRING, t.EzspMfgTokenId.MFG_BOARD_NAME):
            (value,) = await self.getMfgToken(token)
            LOGGER.debug("Read %s token: %s", token.name, value)

            # Tokens are fixed-length and initially filled with \xFF
            result = value.rstrip(b"\xFF").split(b"\x00", 1)[0]

            try:
                result = result.decode("utf-8")
            except UnicodeDecodeError:
                result = "0x" + result.hex().upper()

            tokens.append(result)

        (status, ver_info_bytes) = await self.getValue(
            self.types.EzspValueId.VALUE_VERSION_INFO
        )

        if status == t.EmberStatus.SUCCESS:
            build, ver_info_bytes = t.uint16_t.deserialize(ver_info_bytes)
            major, ver_info_bytes = t.uint8_t.deserialize(ver_info_bytes)
            minor, ver_info_bytes = t.uint8_t.deserialize(ver_info_bytes)
            patch, ver_info_bytes = t.uint8_t.deserialize(ver_info_bytes)
            special, ver_info_bytes = t.uint8_t.deserialize(ver_info_bytes)
            version = f"{major}.{minor}.{patch}.{special} build {build}"
        else:
            version = "unknown stack version"
        return tokens[0], tokens[1], version

    async def can_write_custom_eui64(self) -> bool:
        """Checks if the write-once custom EUI64 token has been written."""
        (custom_eui_64,) = await self.getMfgToken(t.EzspMfgTokenId.MFG_CUSTOM_EUI_64)

        return custom_eui_64 == b"\xFF" * 8

    def add_callback(self, cb):
        id_ = hash(cb)
        while id_ in self._callbacks:
            id_ += 1
        self._callbacks[id_] = cb
        return id_

    def remove_callback(self, id_):
        return self._callbacks.pop(id_)

    def handle_callback(self, *args):
        for callback_id, handler in self._callbacks.items():
            try:
                handler(*args)
            except Exception as e:
                LOGGER.exception("Exception running handler", exc_info=e)

    async def set_source_routing(self) -> None:
        """Enable source routing on NCP."""
        res = await self.setConcentrator(
            True,
            self.types.EmberConcentratorType.HIGH_RAM_CONCENTRATOR,
            MTOR_MIN_INTERVAL,
            MTOR_MAX_INTERVAL,
            MTOR_ROUTE_ERROR_THRESHOLD,
            MTOR_DELIVERY_FAIL_THRESHOLD,
            0,
        )
        LOGGER.debug("Set concentrator type: %s", res)
        if res[0] != self.types.EmberStatus.SUCCESS:
            LOGGER.warning("Couldn't set concentrator type %s: %s", True, res)
        await self._protocol.set_source_routing()

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
