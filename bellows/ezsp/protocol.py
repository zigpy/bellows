import abc
import asyncio
import binascii
import dataclasses
import functools
import logging
import sys
from typing import Any, Callable, Dict, Optional, Tuple

if sys.version_info[:2] < (3, 11):
    from async_timeout import timeout as asyncio_timeout  # pragma: no cover
else:
    from asyncio import timeout as asyncio_timeout  # pragma: no cover

from bellows.config import CONF_EZSP_CONFIG, CONF_EZSP_POLICIES
from bellows.exception import InvalidCommandError
from bellows.typing import GatewayType

LOGGER = logging.getLogger(__name__)
EZSP_CMD_TIMEOUT = 5


class ProtocolHandler(abc.ABC):
    """EZSP protocol specific handler."""

    COMMANDS = {}
    VERSION = None

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

        # Prevent circular import
        from bellows.ezsp.config import DEFAULT_CONFIG, RuntimeConfig, ValueConfig

        # Not all config will be present in every EZSP version so only use valid keys
        ezsp_config = {}
        ezsp_values = {}

        for cfg in DEFAULT_CONFIG[self.VERSION]:
            if isinstance(cfg, RuntimeConfig):
                ezsp_config[cfg.config_id.name] = dataclasses.replace(
                    cfg, config_id=self.types.EzspConfigId[cfg.config_id.name]
                )
            elif isinstance(cfg, ValueConfig):
                ezsp_values[cfg.value_id.name] = dataclasses.replace(
                    cfg, value_id=self.types.EzspValueId[cfg.value_id.name]
                )

        # Override the defaults with user-specified values (or `None` for deletions)
        for name, value in self.SCHEMAS[CONF_EZSP_CONFIG](
            zigpy_config[CONF_EZSP_CONFIG]
        ).items():
            if value is None:
                ezsp_config.pop(name)
                continue

            ezsp_config[name] = RuntimeConfig(
                config_id=self.types.EzspConfigId[name],
                value=value,
            )

        # Make sure CONFIG_PACKET_BUFFER_COUNT is always set last
        if self.types.EzspConfigId.CONFIG_PACKET_BUFFER_COUNT.name in ezsp_config:
            ezsp_config = {
                **ezsp_config,
                self.types.EzspConfigId.CONFIG_PACKET_BUFFER_COUNT.name: ezsp_config[
                    self.types.EzspConfigId.CONFIG_PACKET_BUFFER_COUNT.name
                ],
            }

        # First, set the values
        for cfg in ezsp_values.values():
            # XXX: A read failure does not mean the value is not writeable!
            status, current_value = await self.getValue(cfg.value_id)

            if status == self.types.EmberStatus.SUCCESS:
                current_value, _ = type(cfg.value).deserialize(current_value)
            else:
                current_value = None

            LOGGER.debug(
                "Setting value %s = %s (old value %s)",
                cfg.value_id.name,
                cfg.value,
                current_value,
            )

            (status,) = await self.setValue(cfg.value_id, cfg.value.serialize())

            if status != self.types.EmberStatus.SUCCESS:
                LOGGER.debug(
                    "Could not set value %s = %s: %s",
                    cfg.value_id.name,
                    cfg.value,
                    status,
                )
                continue

        # Finally, set the config
        for cfg in ezsp_config.values():
            (status, current_value) = await self.getConfigurationValue(cfg.config_id)

            # Only grow some config entries, all others should be set
            if (
                status == self.types.EmberStatus.SUCCESS
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

            (status,) = await self.setConfigurationValue(cfg.config_id, cfg.value)
            if status != self.types.EmberStatus.SUCCESS:
                LOGGER.debug(
                    "Could not set config %s = %s: %s",
                    cfg.config_id,
                    cfg.value,
                    status,
                )
                continue

    async def get_free_buffers(self) -> Optional[int]:
        status, value = await self.getValue(self.types.EzspValueId.VALUE_FREE_BUFFERS)

        if status != self.types.EzspStatus.SUCCESS:
            LOGGER.debug("Couldn't get free buffers: %s", status)
            return None

        return int.from_bytes(value, byteorder="little")

    async def command(self, name, *args) -> Any:
        """Serialize command and send it."""
        LOGGER.debug("Send command %s: %s", name, args)
        data = self._ezsp_frame(name, *args)
        self._gw.data(data)
        c = self.COMMANDS[name]
        future = asyncio.Future()
        self._awaiting[self._seq] = (c[0], c[2], future)
        self._seq = (self._seq + 1) % 256

        async with asyncio_timeout(EZSP_CMD_TIMEOUT):
            return await future

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
            frame_name, _, schema = self.COMMANDS_BY_ID[frame_id]
        except KeyError:
            LOGGER.warning(
                "Unknown application frame 0x%04X received: %s (%s).  This is a bug!",
                frame_id,
                binascii.hexlify(data),
                binascii.hexlify(orig_data),
            )
            return

        try:
            result, data = self.types.deserialize(data, schema)
        except Exception:
            LOGGER.warning(
                "Failed to parse frame %s: %s", frame_name, binascii.hexlify(data)
            )
            raise

        LOGGER.debug("Application frame received %s: %s", frame_name, result)

        if sequence in self._awaiting:
            expected_id, schema, future = self._awaiting.pop(sequence)
            try:
                if frame_name == "invalidCommand":
                    sent_cmd_name = self.COMMANDS_BY_ID[expected_id][0]
                    future.set_exception(
                        InvalidCommandError(
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
