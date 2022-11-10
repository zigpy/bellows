import asyncio
import logging
import time

import click
import pure_pcapy

from . import util
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
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(_dump(ctx, channel, outfile))
    except KeyboardInterrupt:
        captured = ctx.obj.get("captured", 0)
        start_time = ctx.obj.get("start_time", None)
        if start_time:
            duration = time.time() - start_time
            click.echo(
                "\nCaptured %s frames in %0.2fs" % (captured, duration), err=True
            )
    finally:
        if "ezsp" in ctx.obj:
            loop.run_until_complete(ctx.obj["ezsp"].mfglibEnd())
            ctx.obj["ezsp"].close()


def ieee_15_4_fcs(data: bytes) -> bytes:
    # Modified from the implementation in `scapy.layers.dot15d4:Dot15d4FCS.compute_fcs`
    crc = 0x0000

    for c in data:
        q = (crc ^ c) & 15  # Do low-order 4 bits
        crc = (crc // 16) ^ (q * 0x1081)

        q = (crc ^ (c // 16)) & 15  # And high 4 bits
        crc = (crc // 16) ^ (q * 0x1081)

    return crc.to_bytes(2, "little")


async def _dump(ctx, channel, outfile):
    s = await util.setup(ctx.obj["device"], ctx.obj["baudrate"])
    ctx.obj["ezsp"] = s

    v = await s.mfglibStart(True)
    util.check(v[0], "Unable to start mfglib")

    v = await s.mfglibSetChannel(channel)
    util.check(v[0], "Unable to set channel")

    pcap = pure_pcapy.Dumper(outfile, 128, 195)  # DLT_IEEE_15_4

    click.echo("Capture started", err=True)
    ctx.obj["start_time"] = time.time()
    ctx.obj["captured"] = 0

    done_event = asyncio.Event()

    def cb(frame_name, response):
        if frame_name == "mfglibRxHandler":
            data = response[2]

            # Later releases of EmberZNet incorrectly use a static FCS
            fcs = data[-2:]
            if s.ezsp_version >= 8:
                computed_fcs = ieee_15_4_fcs(data[0:-2])
                LOGGER.debug("Fixing FCS (expected %s, got %s)", computed_fcs, fcs)
                data = data[0:-2] + computed_fcs

            ts = time.time()
            ts_sec = int(ts)
            ts_usec = int((ts - ts_sec) * 1000000)
            hdr = pure_pcapy.Pkthdr(ts_sec, ts_usec, len(data), len(data))

            try:
                pcap.dump(hdr, data)
            except BrokenPipeError:
                done_event.set()

            ctx.obj["captured"] += 1

    s.add_callback(cb)

    await done_event.wait()
