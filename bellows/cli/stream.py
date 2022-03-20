import asyncio
import logging
import time

import click

from . import util
from .main import main

LOGGER = logging.getLogger(__name__)


@main.command()
@click.option(
    "-c", "--channel", type=click.IntRange(11, 26), metavar="CHANNEL", required=True
)
@click.option(
    "-p", "--power", type=click.IntRange(-100, 20), metavar="POWER", required=True
)
@click.pass_context
def stream(ctx, channel, power):
    """Transmit random stream of characters on CHANNEL with POWER (in dBm)."""
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(_stream(ctx, channel, power))
    except KeyboardInterrupt:
        start_time = ctx.obj.get("start_time", None)
        if start_time:
            duration = time.time() - start_time
            click.echo(
                "\nStreamed on channel %d for %0.2fs" % (channel, duration), err=True
            )
    finally:
        if "ezsp" in ctx.obj:
            s = ctx.obj["ezsp"]
            loop.run_until_complete(s.mfglibStopStream())
            loop.run_until_complete(s.mfglibEnd())
            s.close()


async def _stream(ctx, channel, power):
    s = await util.setup(ctx.obj["device"], ctx.obj["baudrate"])
    ctx.obj["ezsp"] = s

    v = await s.mfglibStart(False)
    util.check(v[0], "Unable to start mfglib")

    v = await s.mfglibSetChannel(channel)
    util.check(v[0], "Unable to set channel")

    v = await s.mfglibSetPower(0, power)
    util.check(v[0], "Unable to set power")

    v = await s.mfglibStartStream()
    util.check(v[0], "Unable to start stream")
    click.echo("Started transmitting random stream of characters", err=True)
    ctx.obj["start_time"] = time.time()
    while True:
        await asyncio.sleep(3600)
