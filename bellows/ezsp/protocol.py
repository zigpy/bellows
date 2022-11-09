import abc
import asyncio
import binascii
import functools
import logging
from typing import Any, Callable, Dict, Optional, Tuple

from bellows.config import CONF_EZSP_CONFIG, CONF_EZSP_POLICIES
from bellows.exception import EzspError
from bellows.typing import GatewayType

LOGGER = logging.getLogger(__name__)

EZSP_CMD_TIMEOUT = 5


class ProtocolHandler(abc.ABC):
    """EZSP protocol specific handler."""

    COMMANDS = {}
    EZSP_VERSION = 4

    def __init__(self, cb_handler: Callable, gateway: GatewayType) -> None:
        self._handle_callback = cb_handler
        self._awaiting = {}
        self._gw = gateway
        self._seq = 0
        self.COMMANDS_BY_ID = {
            cmd_id: (name, tx_schema, rx_schema)
            for name, (cmd_id, tx_schema, rx_schema) in self.COMMANDS.items()
        }
        self.tc_policy = 0

    async def _cfg(self, config_id: int, value: Any) -> None:
        if value is None:
            return

        (status,) = await self.setConfigurationValue(config_id, value)
        if status != self.types.EmberStatus.SUCCESS:
            LOGGER.warning(
                "Couldn't set %s=%s configuration value: %s", config_id, value, status
            )

    def _ezsp_frame(self, name: str, *args: Tuple[Any, ...]) -> bytes:
        """Serialize the named frame and data."""
        c = self.COMMANDS[name]
        frame = self._ezsp_frame_tx(name)
        data = self.types.serialize(args, c[1])
        return frame + data

    @abc.abstractmethod
    def _ezsp_frame_rx(self, data: bytes) -> Tuple[int, int, bytes]:
        """Handler for received data frame."""

    @abc.abstractmethod
    def _ezsp_frame_tx(self, name: str) -> bytes:
        """Serialize the named frame."""

    async def pre_permit(self, time_s: int) -> None:
        """Schedule task before allowing new joins."""

    async def initialize(self, zigpy_config: Dict) -> None:
        """Initialize EmberZNet Stack."""

        buffers = await self.get_free_buffers()
        _, conf_buffers = await self.getConfigurationValue(
            self.types.EzspConfigId.CONFIG_PACKET_BUFFER_COUNT
        )
        LOGGER.debug(
            "Free/configured buffers before any configurations: %s/%s",
            buffers,
            conf_buffers,
        )
        ezsp_config = self.SCHEMAS[CONF_EZSP_CONFIG](zigpy_config[CONF_EZSP_CONFIG])
        for config, value in ezsp_config.items():
            if config in (self.types.EzspConfigId.CONFIG_PACKET_BUFFER_COUNT.name,):
                # we want to set these last
                continue
            await self._cfg(self.types.EzspConfigId[config], value)

        buffers = await self.get_free_buffers()
        _, conf_buffers = await self.getConfigurationValue(
            self.types.EzspConfigId.CONFIG_PACKET_BUFFER_COUNT
        )
        LOGGER.debug(
            "Free/configured buffers before all memory allocation: %s/%s",
            buffers,
            conf_buffers,
        )
        c = self.types.EzspConfigId
        await self._cfg(
            self.types.EzspConfigId.CONFIG_PACKET_BUFFER_COUNT,
            ezsp_config[c.CONFIG_PACKET_BUFFER_COUNT.name],
        )
        buffers = await self.get_free_buffers()
        _, conf_buffers = await self.getConfigurationValue(
            self.types.EzspConfigId.CONFIG_PACKET_BUFFER_COUNT
        )
        LOGGER.debug(
            "Free/configured buffers after all memory allocation: %s/%s",
            buffers,
            conf_buffers,
        )

    async def get_free_buffers(self) -> Optional[int]:
        status, value = await self.getValue(self.types.EzspValueId.VALUE_FREE_BUFFERS)

        if status != self.types.EzspStatus.SUCCESS:
            LOGGER.debug("Couldn't get free buffers: %s", status)
            return None

        return int.from_bytes(value, byteorder="little")

    def command(self, name, *args) -> asyncio.Future:
        """Serialize command and send it."""
        LOGGER.debug("Send command %s: %s", name, args)
        data = self._ezsp_frame(name, *args)
        self._gw.data(data)
        c = self.COMMANDS[name]
        future = asyncio.Future()
        self._awaiting[self._seq] = (c[0], c[2], future)
        self._seq = (self._seq + 1) % 256
        return asyncio.wait_for(future, timeout=EZSP_CMD_TIMEOUT)

    async def set_source_routing(self) -> None:
        """Enable source routing on NCP."""

    async def update_policies(self, zigpy_config: dict) -> None:
        """Set up the policies for what the NCP should do."""

        policies = self.SCHEMAS[CONF_EZSP_POLICIES](zigpy_config[CONF_EZSP_POLICIES])
        self.tc_policy = policies[self.types.EzspPolicyId.TRUST_CENTER_POLICY.name]

        for policy, value in policies.items():
            (status,) = await self.setPolicy(self.types.EzspPolicyId[policy], value)
            assert status == self.types.EmberStatus.SUCCESS  # TODO: Better check

    def __call__(self, data: bytes) -> None:
        """Handler for received data frame."""
        orig_data = data
        sequence, frame_id, data = self._ezsp_frame_rx(data)

        try:
            frame_name = self.COMMANDS_BY_ID[frame_id][0]
        except KeyError:
            LOGGER.warning(
                "Unknown application frame 0x%04X received: %s (%s).  This is a bug!",
                frame_id,
                binascii.hexlify(data),
                binascii.hexlify(orig_data),
            )
            return

        LOGGER.debug(
            "Application frame %s (%s) received: %s",
            frame_id,
            frame_name,
            binascii.hexlify(data),
        )
        schema = self.COMMANDS_BY_ID[frame_id][2]
        result, data = self.types.deserialize(data, schema)

        if sequence in self._awaiting:
            expected_id, schema, future = self._awaiting.pop(sequence)
            try:
                if frame_name == "invalidCommand":
                    sent_cmd_name = self.COMMANDS_BY_ID[expected_id][0]
                    future.set_exception(
                        EzspError(
                            f"{sent_cmd_name} command is an {frame_name}, was sent "
                            f"under {sequence} sequence number: {result[0].name}"
                        )
                    )
                    return

                assert expected_id == frame_id
                future.set_result(result)
            except asyncio.InvalidStateError:
                LOGGER.debug(
                    "Error processing %s response. %s command timed out?",
                    sequence,
                    self.COMMANDS_BY_ID.get(expected_id, [expected_id])[0],
                )
        else:
            self._handle_callback(frame_name, result)

    def __getattr__(self, name: str) -> Callable:
        if name not in self.COMMANDS:
            raise AttributeError(f"{name} not found in COMMANDS")

        return functools.partial(self.command, name)
