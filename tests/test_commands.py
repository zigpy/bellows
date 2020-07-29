import string

import bellows.ezsp.v4.commands
import bellows.ezsp.v5.commands
import pytest


@pytest.fixture(
    params=[bellows.ezsp.v4.commands.COMMANDS, bellows.ezsp.v5.commands.COMMANDS]
)
def commands(request):
    """Return commands for all EZSP protocol versions."""
    yield request.param


def test_names(commands):
    """Test that names of commands seem valid"""
    anum = string.ascii_letters + string.digits
    for command in commands.keys():
        assert all([c in anum for c in command]), command


def test_ids(commands):
    """Test that frame IDs seem valid"""
    for command, parms in commands.items():
        assert 0 <= parms[0] <= 255, command


def test_parms(commands):
    """Test that parameter descriptions seem valid"""
    for command, parms in commands.items():
        assert isinstance(parms[1], tuple), command
        assert isinstance(parms[2], tuple), command


def test_handlers(commands):
    """Test that handler methods only have responses"""
    for command, parms in commands.items():
        if not command.endswith("Handler"):
            continue
        assert len(parms[1]) == 0, command
        assert len(parms[2]) > 0, command
