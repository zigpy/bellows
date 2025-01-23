import asyncio
import functools
import logging

import click
from zigpy.config import SCHEMA_NETWORK

import bellows.types as t
import bellows.zigbee.util as zutil

from . import opts, util
from .main import main

LOGGER = logging.getLogger(__name__)


@main.command()
@opts.channels
@opts.extended_pan
@opts.pan
@click.pass_context
@util.background
async def join(ctx, channels, pan_id, extended_pan_id):
    """Join an existing ZigBee network as an end device"""

    def cb(fut, frame_name, response):
        if frame_name == "stackStatusHandler":
            fut.set_result(response)

    s = await util.setup(ctx.obj["device"], ctx.obj["baudrate"])

    channel = None

    if len(channels) != 1:
        if pan_id or extended_pan_id:
            raise click.BadOptionUsage(
                "--channels", "Specify exactly one channel to join a specific network"
            )
    else:
        channel = t.uint8_t(channels[0])

    if not (pan_id or extended_pan_id):
        scan_type = t.EzspNetworkScanType.ACTIVE_SCAN
        channel_mask = util.channel_mask(channels)
        click.echo(
            "PAN not provided, scanning channels %s..."
            % (" ".join(map(str, channels)),)
        )
        v = await s.startScan(scan_type, channel_mask, 3)

        networks = [n[0] for n in v if n[0].allowingJoin]
        if len(networks) == 0:
            click.echo("No joinable networks found")
            return 1
        if len(networks) > 1:
            click.echo("Multiple joinable networks found. Refusing to pick.")
            return 1

        network = networks[0]

        pan_id = network.panId
        extended_pan_id = network.extendedPanId
        channel = network.channel

        click.echo(f"Found network {pan_id} {extended_pan_id} on channel {channel}")

    if pan_id is None:
        pan_id = t.uint16_t(0)
    else:
        pan_id = t.uint16_t(pan_id)
    if isinstance(extended_pan_id, str):
        extended_pan_id = util.parse_epan(extended_pan_id)
    if extended_pan_id is None:
        extended_pan_id = t.FixedList[t.uint8_t, 8]([t.uint8_t(0)] * 8)

    v = await util.network_init(s)

    if v[0] == t.EmberStatus.SUCCESS:
        LOGGER.debug("Network was up, leaving...")
        v = await s.leaveNetwork()
        util.check(v[0], f"Failure leaving network: {v[0]}")
        await asyncio.sleep(1)  # TODO

    initial_security_state = zutil.zha_security(SCHEMA_NETWORK({}))
    v = await s.setInitialSecurityState(initial_security_state)
    util.check(v[0], f"Setting security state failed: {v[0]}")

    parameters = t.EmberNetworkParameters()
    parameters.extendedPanId = extended_pan_id
    parameters.panId = pan_id
    parameters.radioTxPower = t.uint8_t(8)
    parameters.radioChannel = t.uint8_t(channel)
    parameters.joinMethod = t.EmberJoinMethod.USE_MAC_ASSOCIATION
    parameters.nwkManagerId = t.EmberNodeId(0)
    parameters.nwkUpdateId = t.uint8_t(0)
    parameters.channels = t.uint32_t(0)
    click.echo(parameters)

    fut = asyncio.Future()
    cbid = s.add_callback(functools.partial(cb, fut))
    v = await s.joinNetwork(t.EmberNodeType.END_DEVICE, parameters)
    util.check(v[0], f"Joining network failed: {v[0]}")
    v = await fut
    click.echo(v)

    s.remove_callback(cbid)

    await s.disconnect()


@main.command()
@click.pass_context
@util.background
async def leave(ctx):
    """Leave the ZigBee network"""
    s = await util.setup(ctx.obj["device"], ctx.obj["baudrate"])
    v = await util.network_init(s)
    if v[0] == t.EmberStatus.NOT_JOINED:
        click.echo("Not joined, not leaving")
    else:
        v = await s.leaveNetwork()
        util.check(
            v[0],
            f"Failure leaving network: {v[0]}",
            expected=t.EmberStatus.NETWORK_DOWN,
        )

    await s.disconnect()


@main.command()
@opts.channels
@opts.duration_ms
@click.option("-e", "--energy", "energy_scan", is_flag=True)
@click.pass_context
@util.background
async def scan(ctx, channels, duration_ms, energy_scan):
    """Scan for networks or radio interference"""
    click.echo(
        "`bellows scan` has been deprecated. Please use the `energy-scan` and `network-scan` commands from zigpy-cli.",
        err=True,
    )
    ctx.exit(1)
