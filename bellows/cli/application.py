"""CLI commands which use the application framework"""

import asyncio

import click

import bellows.ezsp
import bellows.types as t
import bellows.zigbee.application
import bellows.zigbee.endpoint
from . import opts
from . import util
from .main import main


@main.command()
@opts.database_file
@opts.channel
@opts.extended_pan
@opts.pan
@click.pass_context
def form(ctx, database, channel, pan_id, extended_pan_id):
    """Form a new ZigBee network"""
    ctx.obj['database_file'] = database
    def inner(ctx):
        app = ctx.obj['app']
        yield from app.form_network(channel, pan_id, extended_pan_id)

    return util.app(inner)(ctx)

@main.command()
@opts.database_file
@opts.duration_s
@click.pass_context
def permit(ctx, database, duration_s):
    """Allow devices to join this ZigBee network"""
    ctx.obj['database_file'] = database
    def inner(ctx):
        app = ctx.obj['app']
        yield from app.permit(duration_s)

        click.echo("Joins are permitted for the next %ss..." % (duration_s, ))
        yield from asyncio.sleep(duration_s + 1)
        click.echo("Done")

    return util.app(inner)(ctx)


@main.command()
@opts.database_file
@click.pass_context
def devices(ctx, database):
    """Show device database"""
    ezsp = bellows.ezsp.EZSP()
    app = bellows.zigbee.application.ControllerApplication(ezsp, database)
    for ieee, dev in app.devices.items():
        click.echo("Device:")
        click.echo("  NWK: 0x%04x" % (dev._nwk, ))
        click.echo("  IEEE: %s" % (ieee, ))
        click.echo("  Endpoints:")
        for epid, ep in dev.endpoints.items():
            if epid == 0:
                continue
            if ep.status == bellows.zigbee.endpoint.Status.NEW:
                click.echo("    %s: Uninitialized")
            else:
                click.echo(
                    "    %s: profile=0x%02x, device_type=%s" % (
                        epid,
                        ep.profile_id,
                        ep.device_type,
                    )
                )
                clusters = sorted(list(ep.clusters.keys()))
                if clusters:
                    click.echo("      Clusters:")
                for cluster in clusters:
                    click.echo("        %s (%s)" % (
                        ep.clusters[cluster].name, cluster
                    ))


@main.group()
@click.pass_context
@opts.database_file
@click.argument('node')
def zdo(ctx, node, database):
    """Perform ZDO operations against a device"""
    node = t.EmberEUI64([int(p, base=16) for p in node.split(':')])
    ctx.obj['node'] = node
    ctx.obj['database_file'] = database


@zdo.command()
@click.pass_context
@util.app
def endpoints(ctx):
    """List endpoints on a device"""
    app = ctx.obj['app']
    dev = app.devices[ctx.obj['node']]

    v = yield from dev.zdo.request(0x0005, dev._nwk)
    if v[0] != 0:
        click.echo("Non-success response: %s" % (v, ))
    click.echo(v[2])


@zdo.command()
@click.pass_context
@util.app
@click.argument('endpoint', type=click.IntRange(1, 255))
def get_endpoint(ctx, endpoint):
    """Show an endpoint's simple descriptor"""
    app = ctx.obj['app']
    dev = app.devices[ctx.obj['node']]

    v = yield from dev.zdo.request(0x0004, dev._nwk, endpoint)
    if v[0] != 0:
        click.echo("Non-success response: %s" % (v, ))
    click.echo(v[2])


@zdo.command()
@click.pass_context
@click.argument('endpoint', type=click.IntRange(1, 255))
@click.argument('cluster', type=click.IntRange(0, 65535))
@util.app
def bind(ctx, endpoint, cluster):
    """Bind to a cluster on a node"""
    app = ctx.obj['app']
    dev = app.devices[ctx.obj['node']]

    v = yield from dev.zdo.bind(endpoint, cluster)
    click.echo(v)


@zdo.command()
@click.pass_context
@click.argument('endpoint', type=click.IntRange(1, 255))
@click.argument('cluster', type=click.IntRange(0, 65535))
@util.app
def unbind(ctx, endpoint, cluster):
    """Unbind a cluster on a node"""
    app = ctx.obj['app']
    dev = app.devices[ctx.obj['node']]

    v = yield from dev.zdo.unbind(endpoint, cluster)
    click.echo(v)


@main.group()
@click.pass_context
@opts.database_file
@click.argument('node')
@click.argument('endpoint', type=click.IntRange(1, 255))
@click.argument('cluster', type=click.IntRange(0, 65535))
def zcl(ctx, database, node, cluster, endpoint):
    """Peform ZCL operations against a device"""
    node = t.EmberEUI64([int(p, base=16) for p in node.split(':')])
    ctx.obj['database_file'] = database
    ctx.obj['node'] = node
    ctx.obj['endpoint'] = endpoint
    ctx.obj['cluster'] = cluster


@zcl.command()
@click.pass_context
@click.argument('attribute', type=click.IntRange(0, 65535))
@util.app
def read_attribute(ctx, attribute):
    app = ctx.obj['app']
    dev = app.devices[ctx.obj['node']]
    endpoint = ctx.obj['endpoint']
    cluster_id = ctx.obj['cluster']

    cluster = dev.endpoints[endpoint].clusters[cluster_id]

    v = yield from cluster.read_attributes([attribute])
    if not v[0]:
        click.echo("Received empty response")
    for record in v[0]:
        if record.status == 0:
            click.echo("%s=%s" % (record.attrid, record.value.value))
        else:
            click.echo("Attribute %s not successful. Status=%s" % (
                record.attrid, record.status
            ))


@zcl.command()
@click.pass_context
@click.argument('attribute', type=click.IntRange(0, 65535))
@click.argument('min_interval', type=click.IntRange(0, 65535))
@click.argument('max_interval', type=click.IntRange(0, 65535))
@click.argument('reportable_change', type=click.INT)
@util.app
def configure_reporting(ctx,
                        attribute,
                        min_interval,
                        max_interval,
                        reportable_change):
    app = ctx.obj['app']
    dev = app.devices[ctx.obj['node']]
    endpoint = ctx.obj['endpoint']
    cluster_id = ctx.obj['cluster']

    cluster = dev.endpoints[endpoint].clusters[cluster_id]

    v = yield from cluster.configure_reporting(
        attribute,
        min_interval,
        max_interval,
        reportable_change,
    )
    click.echo(v)
