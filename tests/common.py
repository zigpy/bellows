from __future__ import annotations

from unittest.mock import AsyncMock

from bellows.ezsp.protocol import ProtocolHandler


def mock_ezsp_commands(ezsp: ProtocolHandler) -> ProtocolHandler:
    for command_name, (_command_id, tx_schema, _rx_schema) in ezsp.COMMANDS.items():
        # TODO: make this end-to-end instead of relying on this serialization hack
        async def fake_sender(*args, _command_name=command_name, _ezsp=ezsp, **kwargs):
            # Trigger an exception early
            _ezsp._ezsp_frame(_command_name, *args, **kwargs)

        setattr(ezsp, command_name, AsyncMock(wraps=fake_sender))
