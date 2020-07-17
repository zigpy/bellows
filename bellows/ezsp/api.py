import abc
import asyncio
import functools
import logging
from typing import Any, Callable, Dict, Tuple

from bellows.typing import GatewayType

LOGGER = logging.getLogger(__name__)

EZSP_CMD_TIMEOUT = 10


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

    def get_sequence(self) -> int:
        """Return next sequence id."""
        self._seq = (self._seq + 1) % 256
        return self._seq

    @abc.abstractmethod
    def __call__(self, data: bytes) -> None:
        """Handler for received data frame."""

    async def _cfg(self, config_id: int, value: Any, optional=False) -> None:
        v = await self._ezsp.setConfigurationValue(config_id, value)
        if not optional:
            assert v[0] == self.types.EmberStatus.SUCCESS  # TODO: Better check

    @abc.abstractmethod
    def _ezsp_frame(self, name: str, *args: Tuple[Any, ...]) -> bytes:
        """Serialize the named frame and data."""

    @abc.abstractmethod
    async def initialize(self, ezsp_config: Dict) -> None:
        """Initialize EmberZNet Stack."""

    def command(self, name, *args) -> asyncio.Future:
        """Serialize command and send it."""
        data = self._ezsp_frame(name, *args)
        self._gw.data(data)
        c = self.COMMANDS[name]
        future = asyncio.Future()
        self._awaiting[self.get_sequence()] = (c[0], c[2], future)
        return asyncio.wait_for(future, timeout=EZSP_CMD_TIMEOUT)

    def __getattr__(self, name):
        if name not in self.COMMANDS:
            raise AttributeError("%s not found in COMMANDS" % (name,))

        return functools.partial(self._command, name)
