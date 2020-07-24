import abc
import asyncio
import binascii
import functools
import logging
from typing import Any, Callable, Dict, Tuple

from bellows.typing import GatewayType

LOGGER = logging.getLogger(__name__)

EZSP_CMD_TIMEOUT = 100


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

    async def _cfg(self, config_id: int, value: Any, optional=False) -> None:
        v = await self.setConfigurationValue(config_id, value)
        if not optional:
            assert v[0] == self.types.EmberStatus.SUCCESS  # TODO: Better check

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

    async def initialize(self, ezsp_config: Dict) -> None:
        """Initialize EmberZNet Stack."""

        ezsp_config = self.SCHEMA(ezsp_config)
        for config, value in ezsp_config.items():
            if config in (self.types.EzspConfigId.CONFIG_PACKET_BUFFER_COUNT.name,):
                # we want to set these last
                continue
            await self._cfg(self.types.EzspConfigId[config], value)

        c = self.types.EzspConfigId
        await self._cfg(
            self.types.EzspConfigId.CONFIG_PACKET_BUFFER_COUNT,
            ezsp_config[c.CONFIG_PACKET_BUFFER_COUNT.name],
        )

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

    async def update_policies(self, zigpy_config: dict) -> None:
        """Set up the policies for what the NCP should do."""

        v = await self.setPolicy(
            self.types.EzspPolicyId.TC_KEY_REQUEST_POLICY,
            self.types.EzspDecisionId.GENERATE_NEW_TC_LINK_KEY,
        )
        assert v[0] == self.types.EmberStatus.SUCCESS  # TODO: Better check
        v = await self.setPolicy(
            self.types.EzspPolicyId.APP_KEY_REQUEST_POLICY,
            self.types.EzspDecisionId.DENY_APP_KEY_REQUESTS,
        )
        assert v[0] == self.types.EmberStatus.SUCCESS  # TODO: Better check
        v = await self.setPolicy(
            self.types.EzspPolicyId.TRUST_CENTER_POLICY,
            self.types.EzspDecisionId.ALLOW_PRECONFIGURED_KEY_JOINS,
        )
        assert v[0] == self.types.EmberStatus.SUCCESS  # TODO: Better check

    def __call__(self, data: bytes) -> None:
        """Handler for received data frame."""
        sequence, frame_id, data = self._ezsp_frame_rx(data)
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
            result, data = self.types.deserialize(data, schema)
            try:
                future.set_result(result)
            except asyncio.InvalidStateError:
                LOGGER.debug(
                    "Error processing %s response. %s command timed out?",
                    sequence,
                    self.COMMANDS_BY_ID.get(expected_id, [expected_id])[0],
                )
        else:
            schema = self.COMMANDS_BY_ID[frame_id][2]
            frame_name = self.COMMANDS_BY_ID[frame_id][0]
            result, data = self.types.deserialize(data, schema)
            self._handle_callback(frame_name, result)

    def __getattr__(self, name: str) -> Callable:
        if name not in self.COMMANDS:
            raise AttributeError(f"{name} not found in COMMANDS")

        return functools.partial(self.command, name)