import string

from bellows import commands


def test_names():
    """Test that names of commands seem valid"""
    anum = string.ascii_letters + string.digits
    for command in commands.COMMANDS.keys():
        assert all([c in anum for c in command]), command


def test_ids():
    """Test that frame IDs seem valid"""
    for command, parms in commands.COMMANDS.items():
        assert 0 <= parms[0] <= 255, command


def test_parms():
    """Test that parameter descriptions seem valid"""
    for command, parms in commands.COMMANDS.items():
        assert isinstance(parms[1], tuple), command
        assert isinstance(parms[2], tuple), command


def test_handlers():
    """Test that handler methods only have responses"""
    for command, parms in commands.COMMANDS.items():
        if not command.endswith('Handler'):
            continue
        assert len(parms[1]) == 0, command
        assert len(parms[2]) > 0, command
