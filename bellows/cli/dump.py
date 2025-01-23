import logging

import click

from .main import main

LOGGER = logging.getLogger(__name__)


@main.command()
@click.option(
    "-c", "--channel", type=click.IntRange(11, 26), metavar="CHANNEL", required=True
)
@click.option(
    "-w",
    "outfile",
    type=click.Path(writable=True, dir_okay=False),
    metavar="FILE",
    required=True,
)
@click.pass_context
def dump(ctx, channel, outfile):
    """Capture frames on CHANNEL and write to FILE in tcpdump format"""
    click.echo(
        "`bellows dump` has been deprecated. Please use the `packet-capture` command from zigpy-cli.",
        err=True,
    )
    ctx.exit(1)
