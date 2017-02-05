import asyncio
import functools
import logging
import math
import os

import click

import bellows.types as t
from . import opts
from . import util
from .main import main


LOGGER = logging.getLogger(__name__)


@main.command()
@opts.channel
@opts.extended_pan
@opts.pan
@click.pass_context
@util.async
def form(ctx, channel, pan_id, extended_pan_id):
    """Create a new ZigBee network"""
    s = yield from util.setup(ctx.obj['device'], util.print_cb)

    v = yield from util.networkInit(s)
    if v[0] == t.EmberStatus.EMBER_SUCCESS:
        LOGGER.debug("Network was up, leaving...")
        v = yield from s.leaveNetwork()
        util.check(v[0], "Failure leaving network: %s" % (v[0], ))
        yield from asyncio.sleep(1)  # TODO

    initial_security_state = util.zha_security(controller=True)
    v = yield from s.setInitialSecurityState(initial_security_state)
    util.check(v[0], "Setting security state failed: %s" % (v[0], ))

    yield from util.basic_tc_permits(s)

    if channel:
        channel = t.uint8_t(channel)
    else:
        channel = t.uint8_t(17)

    if extended_pan_id:
        extended_pan_id = util.parse_epan(extended_pan_id)
    else:
        extended_pan_id = t.fixed_list(8, t.uint8_t)([t.uint8_t(0)] * 8)

    if pan_id:
        pan_id = t.uint16_t(pan_id)
    else:
        pan_id = t.uint16_t.from_bytes(os.urandom(2), 'little')

    parameters = t.EmberNetworkParameters()
    parameters.panId = pan_id
    parameters.extendedPanId = extended_pan_id
    parameters.radioTxPower = t.uint8_t(8)
    parameters.radioChannel = channel
    parameters.joinMethod = t.EmberJoinMethod.EMBER_USE_MAC_ASSOCIATION
    parameters.nwkManagerId = t.EmberNodeId(0)
    parameters.nwkUpdateId = t.uint8_t(0)
    parameters.channels = t.uint32_t(0)
    click.echo(parameters)

    LOGGER.info("Forming network ...")
    fut = asyncio.Future()

    def cb(fut, frame_name, response):
        if frame_name == 'stackStatusHandler':
            fut.set_result(response)

    s.add_callback(functools.partial(cb, fut))
    v = yield from s.formNetwork(parameters)
    util.check(v[0], "Failed to form network: %s" % (v[0], ))

    v = yield from fut
    util.check(
        v[0],
        "Network didn't come up after form",
        t.EmberStatus.EMBER_NETWORK_UP,
    )

    yield from s.setValue(t.EzspValueId.EZSP_VALUE_STACK_TOKEN_WRITING, 1)
    yield from asyncio.sleep(0.1)

    s.close()


@main.command()
@opts.channels
@opts.extended_pan
@opts.pan
@click.pass_context
@util.async
def join(ctx, channels, pan_id, extended_pan_id):
    """Join an existing ZigBee network as an end device"""
    def cb(fut, frame_name, response):
        if frame_name == 'stackStatusHandler':
            fut.set_result(response)

    s = yield from util.setup(ctx.obj['device'])

    channel = None

    if len(channels) != 1:
        if pan_id or extended_pan_id:
            raise click.BadOptionUsage(
                "Specify exactly one channel to join a specific network"
            )
    else:
        channel = t.uint8_t(channels[0])

    if not (pan_id or extended_pan_id):
        scan_type = t.EzspNetworkScanType.EZSP_ACTIVE_SCAN
        channel_mask = util.channel_mask(channels)
        click.echo("PAN not provided, scanning channels %s..." % (
            ' '.join(map(str, channels)),
        ))
        v = yield from s.startScan(scan_type, channel_mask, 3)

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

        click.echo("Found network %s %s on channel %s" % (
            pan_id, extended_pan_id, channel,
        ))

    if pan_id is None:
        pan_id = t.uint16_t(0)
    else:
        pan_id = t.uint16_t(pan_id)
    if isinstance(extended_pan_id, str):
        extended_pan_id = util.parse_epan(extended_pan_id)
    if extended_pan_id is None:
        extended_pan_id = t.fixed_list(8, t.uint8_t)([t.uint8_t(0)] * 8)

    v = yield from util.networkInit(s)

    if v[0] == t.EmberStatus.EMBER_SUCCESS:
        LOGGER.debug("Network was up, leaving...")
        v = yield from s.leaveNetwork()
        util.check(v[0], "Failure leaving network: %s" % (v[0], ))
        yield from asyncio.sleep(1)  # TODO

    initial_security_state = util.zha_security()
    v = yield from s.setInitialSecurityState(initial_security_state)
    util.check(v[0], "Setting security state failed: %s" % (v[0], ))

    parameters = t.EmberNetworkParameters()
    parameters.extendedPanId = extended_pan_id
    parameters.panId = pan_id
    parameters.radioTxPower = t.uint8_t(8)
    parameters.radioChannel = t.uint8_t(channel)
    parameters.joinMethod = t.EmberJoinMethod.EMBER_USE_MAC_ASSOCIATION
    parameters.nwkManagerId = t.EmberNodeId(0)
    parameters.nwkUpdateId = t.uint8_t(0)
    parameters.channels = t.uint32_t(0)
    click.echo(parameters)

    fut = asyncio.Future()
    cbid = s.add_callback(functools.partial(cb, fut))
    v = yield from s.joinNetwork(t.EmberNodeType.EMBER_END_DEVICE, parameters)
    util.check(v[0], "Joining network failed: %s" % (v[0], ))
    v = yield from fut
    click.echo(v)

    s.remove_callback(cbid)

    s.close()


@main.command()
@click.pass_context
@util.async
def leave(ctx):
    """Leave the ZigBee network"""
    s = yield from util.setup(ctx.obj['device'])
    v = yield from util.networkInit(s)
    if v[0] == t.EmberStatus.EMBER_NOT_JOINED:
        click.echo("Not joined, not leaving")
        return

    v = yield from s.leaveNetwork()
    util.check(v[0], "Failure leaving network: %s" % (v[0], ))


@main.command()
@opts.channels
@opts.duration_ms
@click.option('-e', '--energy', 'energy_scan', is_flag=True)
@click.pass_context
@util.async
def scan(ctx, channels, duration_ms, energy_scan):
    """Scan for networks or radio interference"""
    s = yield from util.setup(ctx.obj['device'])

    channel_mask = util.channel_mask(channels)
    click.echo("Scanning channels %s" % (' '.join(map(str, channels)), ))

    # TFM says:
    #   Sets the exponent of the number of scan periods, where a scan period is
    #   960 symbols. The scan will occur for ((2^duration) + 1) scan periods.
    # 1 symbol is 16us
    duration_symbols = duration_ms / (960 * 0.016)
    duration_symbol_exp = max(
        0,
        math.ceil(math.log(duration_symbols - 1, 2)),
    )

    scan_type = t.EzspNetworkScanType.EZSP_ACTIVE_SCAN
    if energy_scan:
        scan_type = t.EzspNetworkScanType.EZSP_ENERGY_SCAN

    v = yield from s.startScan(scan_type, channel_mask, duration_symbol_exp)
    for network in v:
        click.echo(network)

    s.close()
