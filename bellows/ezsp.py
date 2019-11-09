import asyncio
import binascii
import functools
import logging

import bellows.types as t
import bellows.uart as uart
from bellows.commands import COMMANDS
from bellows.exception import EzspError

EZSP_CMD_TIMEOUT = 10
LOGGER = logging.getLogger(__name__)


class EZSP:

    COMMANDS = COMMANDS
    EZSP_VERSION = 4

    def __init__(self):
        self._awaiting = {}
        self._baudrate = None
        self._callbacks = {}
        self._device = None
        self._ezsp_event = asyncio.Event()
        self._seq = 0
        self._gw = None
        self._ezsp_version = self.EZSP_VERSION
        self._awaiting = {}
        self.COMMANDS_BY_ID = {}
        for name, details in self.COMMANDS.items():
            self.COMMANDS_BY_ID[details[0]] = (name, details[1], details[2])

    async def connect(self, device, baudrate):
        assert self._gw is None
        self._baudrate = baudrate
        self._device = device
        self._gw = await uart.connect(device, baudrate, self)

    def reconnect(self):
        """Reconnect using saved parameters."""
        LOGGER.debug(
            "Reconnecting %s serial port on %s bauds", self._device, self._baudrate
        )
        return self.connect(self._device, self._baudrate)

    async def reset(self):
        LOGGER.debug("Resetting EZSP")
        self.stop_ezsp()
        for seq in self._awaiting:
            future = self._awaiting[seq][2]
            if not future.done():
                future.cancel()
        self._awaiting = {}
        self._callbacks = {}
        self._seq = 0
        await self._gw.reset()
        self.start_ezsp()

    async def version(self):
        ver, stack_type, stack_version = await self._command(
            "version", self.ezsp_version
        )
        if ver != self.version:
            self._ezsp_version = ver
            await self._command("version", ver)
            LOGGER.debug("Switched to EZSP protocol version %d", self.ezsp_version)
        LOGGER.info("EZSP Stack Type: %s, Stack Version: %s", stack_type, stack_version)

    def close(self):
        self.stop_ezsp()
        if self._gw:
            self._gw.close()
            self._gw = None

    def _ezsp_frame(self, name, *args):
        c = self.COMMANDS[name]
        data = t.serialize(args, c[1])
        frame = [self._seq & 0xFF, 0, c[0]]  # Frame control. TODO.  # Frame ID
        if self.ezsp_version >= 5:
            frame.insert(1, 0xFF)  # Legacy Frame ID
            frame.insert(1, 0x00)  # Ext frame control. TODO.

        return bytes(frame) + data

    def _command(self, name, *args):
        LOGGER.debug("Send command %s: %s", name, args)
        if not self.is_ezsp_running:
            raise EzspError("EZSP is not running")

        data = self._ezsp_frame(name, *args)
        self._gw.data(data)
        c = self.COMMANDS[name]
        future = asyncio.Future()
        self._awaiting[self._seq] = (c[0], c[2], future)
        self._seq = (self._seq + 1) % 256
        return asyncio.wait_for(future, timeout=EZSP_CMD_TIMEOUT)

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
        LOGGER.debug("%s connection lost unexpectedly: %s", self._device, exc)
        self.enter_failed_state("Serial connection loss: {}".format(exc))

    def enter_failed_state(self, error):
        """UART received error frame."""
        LOGGER.error("NCP entered failed state. Requesting APP controller restart")
        self.stop_ezsp()
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

    def __getattr__(self, name):
        if name not in self.COMMANDS:
            raise AttributeError("%s not found in COMMANDS" % (name,))

        return functools.partial(self._command, name)

    def frame_received(self, data):
        """Handle a received EZSP frame

        The protocol has taken care of UART specific framing etc, so we should
        just have EZSP application stuff here, with all escaping/stuffing and
        data randomization removed.
        """
        sequence, frame_id, data = data[0], data[2], data[3:]
        if frame_id == 0xFF:
            frame_id = 0
            if len(data) > 1:
                frame_id = data[1]
                data = data[2:]

        frame_name = self.COMMANDS_BY_ID[frame_id][0]
        LOGGER.debug(
            "Application frame %s (%s) received: %s",
            frame_id,
            frame_name,
            binascii.hexlify(data),
        )

        if sequence in self._awaiting:
            expected_id, schema, future = self._awaiting.pop(sequence)
            assert expected_id == frame_id
            result, data = t.deserialize(data, schema)
            try:
                future.set_result(result)
            except asyncio.InvalidStateError as exc:
                LOGGER.debug(
                    "Error processing %s response. %s command timed out?",
                    sequence,
                    self.COMMANDS_BY_ID.get(expected_id, [expected_id])[0],
                )
        else:
            schema = self.COMMANDS_BY_ID[frame_id][2]
            frame_name = self.COMMANDS_BY_ID[frame_id][0]
            result, data = t.deserialize(data, schema)
            self.handle_callback(frame_name, result)

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
