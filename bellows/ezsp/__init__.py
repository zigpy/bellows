"""EZSP protocol."""

import asyncio
import functools
import logging
from typing import Any, Callable, Coroutine, Dict, Tuple

from bellows.config import (
    CONF_DEVICE,
    CONF_DEVICE_PATH,
    CONF_EZSP_CONFIG,
    SCHEMA_DEVICE,
)
from bellows.exception import APIException, EzspError
import bellows.types as t
import bellows.uart
import serial

from . import v4, v5, v6, v7, v8

EZSP_LATEST = v8.EZSP_VERSION
PROBE_TIMEOUT = 3
LOGGER = logging.getLogger(__name__)


class EZSP:
    _BY_VERSION = {
        v4.EZSP_VERSION: v4.EZSPv4,
        v5.EZSP_VERSION: v5.EZSPv5,
        v6.EZSP_VERSION: v6.EZSPv6,
        v7.EZSP_VERSION: v7.EZSPv7,
        v8.EZSP_VERSION: v8.EZSPv8,
    }

    def __init__(self, device_config: Dict):
        self._config = device_config
        self._callbacks = {}
        self._ezsp_event = asyncio.Event()
        self._ezsp_version = v4.EZSP_VERSION
        self._gw = None
        self._protocol = None

    @classmethod
    async def probe(cls, device_config: Dict) -> bool:
        """Probe port for the device presence."""
        ezsp = cls(SCHEMA_DEVICE(device_config))
        try:
            await asyncio.wait_for(ezsp._probe(), timeout=PROBE_TIMEOUT)
            return True
        except (asyncio.TimeoutError, serial.SerialException, APIException) as exc:
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
        await self.reset()
        self.close()

    @classmethod
    async def initialize(cls, zigpy_config: Dict) -> "EZSP":
        """Return initialized EZSP instance. """
        ezsp = cls(zigpy_config[CONF_DEVICE])
        await ezsp.connect()
        await ezsp.reset()
        await ezsp.version()
        await ezsp._protocol.initialize(zigpy_config[CONF_EZSP_CONFIG])
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
            "EZSP Stack Type: %s, Stack Version: %s, Protocol version: %s",
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

    def connection_lost(self, exc):
        """Lost serial connection."""
        LOGGER.debug(
            "%s connection lost unexpectedly: %s", self._config[CONF_DEVICE_PATH], exc
        )
        self.enter_failed_state("Serial connection loss: {}".format(exc))

    def enter_failed_state(self, error):
        """UART received error frame."""
        LOGGER.error("NCP entered failed state. Requesting APP controller restart")
        self.close()
        self.handle_callback("_reset_controller_application", (error,))

    async def formNetwork(self, parameters):  # noqa: N802
        fut = asyncio.Future()

        def cb(frame_name, response):
            nonlocal fut
            if frame_name == "stackStatusHandler":
                fut.set_result(response)

        self.add_callback(cb)
        v = await self._command("formNetwork", parameters)
        if v[0] != t.EmberStatus.SUCCESS:
            raise Exception("Failure forming network: %s" % (v,))

        v = await fut
        if v[0] != t.EmberStatus.NETWORK_UP:
            raise Exception("Failure forming network: %s" % (v,))

        return v

    def __getattr__(self, name: str) -> Callable:
        if name not in self._protocol.COMMANDS:
            raise AttributeError(f"{name} not found in COMMANDS")

        return functools.partial(self._command, name)

    def frame_received(self, data: bytes) -> None:
        """Handle a received EZSP frame

        The protocol has taken care of UART specific framing etc, so we should
        just have EZSP application stuff here, with all escaping/stuffing and
        data randomization removed.
        """
        self._protocol(data)

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

    def update_policies(self, zigpy_config: dict) -> Coroutine:
        """Set up the policies for what the NCP should do."""
        return self._protocol.update_policies(zigpy_config)

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
