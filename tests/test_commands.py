import string

import pytest

import bellows.ezsp.v4.commands
import bellows.ezsp.v5.commands
import bellows.ezsp.v6.commands
import bellows.ezsp.v7.commands
import bellows.ezsp.v8.commands


@pytest.fixture(
    params=[
        bellows.ezsp.v4.commands,
        bellows.ezsp.v5.commands,
        bellows.ezsp.v6.commands,
        bellows.ezsp.v7.commands,
        bellows.ezsp.v8.commands,
    ]
)
def commands(request):
    """Return commands for all EZSP protocol versions."""
    yield request.param.COMMANDS


def test_names(commands):
    """Test that names of commands seem valid"""
    anum = string.ascii_letters + string.digits
    for command in commands.keys():
        assert all([c in anum for c in command]), command


def test_ids(commands):
    """Test that frame IDs seem valid"""
    seen = set()
    for command, (cmd_id, _, _) in commands.items():
        assert 0 <= cmd_id <= 255, command
        assert cmd_id not in seen
        seen.add(cmd_id)


def test_parms(commands):
    """Test that parameter descriptions seem valid"""
    for command, params in commands.items():
        assert isinstance(params[1], (tuple, dict)), command
        assert isinstance(params[2], (tuple, dict)), command


def test_handlers(commands):
    """Test that handler methods only have responses"""
    for command, params in commands.items():
        if not command.endswith("Handler"):
            continue
        assert len(params[1]) == 0, command
        assert len(params[2]) > 0, command
