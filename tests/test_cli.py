import asyncio

import click
from click.testing import CliRunner
import pytest

import bellows.cli  # noqa: F401  # registers the commands on `main`
from bellows.cli import util
from bellows.cli.main import main


@pytest.fixture
def event_loop_for_cli():
    """The CLI runs its commands on the thread's current event loop."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    asyncio.set_event_loop(None)
    loop.close()


def test_channel_mask():
    assert util.channel_mask([11, 26]) == (1 << 11) | (1 << 26)


@pytest.mark.parametrize("channel", [10, 27])
def test_channel_mask_invalid_channel(channel):
    with pytest.raises(click.BadOptionUsage, match="channels must be from 11 to 26"):
        util.channel_mask([channel])


@pytest.mark.parametrize(
    ("args", "message"),
    [
        (["config"], "One of config or --all must be specified"),
        (["config", "CONFIG_STACK_PROFILE", "--all"], "Specify a config or --all"),
    ],
)
def test_ncp_config_bad_usage(event_loop_for_cli, args, message):
    result = CliRunner().invoke(main, ["--device", "/dev/null", *args])

    assert result.exit_code == 2
    assert message in result.output
