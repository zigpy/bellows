import asyncio
import time

import click
import pure_pcapy

from . import util
from .main import main


@main.command()
@click.option(
    '-c', '--channel',
    type=click.IntRange(11, 26),
    metavar="CHANNEL",
    required=True,
)
@click.option(
    '-w', 'outfile',
    type=click.Path(writable=True, dir_okay=False),
    metavar="FILE",
    required=True,
)
@click.pass_context
def dump(ctx, channel, outfile):
    """Capture frames on CHANNEL and write to FILE in tcpdump format"""
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(_dump(ctx, channel, outfile))
    except KeyboardInterrupt:
        captured = ctx.obj.get('captured', 0)
        start_time = ctx.obj.get('start_time', None)
        if start_time:
            duration = time.time() - start_time
            click.echo("\nCaptured %s frames in %0.2fs" % (captured, duration))
    finally:
        if 'ezsp' in ctx.obj:
            loop.run_until_complete(ctx.obj['ezsp'].mfglibEnd())
            ctx.obj['ezsp'].close()


@asyncio.coroutine
def _dump(ctx, channel, outfile):
    s = yield from util.setup(ctx.obj['device'])
    ctx.obj['ezsp'] = s

    v = yield from s.mfglibStart(True)
    util.check(v[0], "Unable to start mfglib")

    v = yield from s.mfglibSetChannel(channel)
    util.check(v[0], "Unable to set channel")

    DLT_IEEE802_15_4 = 195
    pcap = pure_pcapy.Dumper(outfile, 128, DLT_IEEE802_15_4)

    click.echo("Capture started")
    ctx.obj['start_time'] = time.time()
    ctx.obj['captured'] = 0

    def cb(frame_name, response):
        if frame_name == 'mfglibRxHandler':
            data = response[2]
            ts = time.time()
            ts_sec = int(ts)
            ts_usec = int((ts - ts_sec) * 1000000)
            hdr = pure_pcapy.Pkthdr(ts_sec, ts_usec, len(data), len(data))
            pcap.dump(hdr, data)
            ctx.obj['captured'] += 1

    s.add_callback(cb)

    while True:
        yield from asyncio.sleep(1)
