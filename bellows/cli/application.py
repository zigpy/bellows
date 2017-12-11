"""CLI commands which use the application framework"""

import asyncio
import binascii

import click

import bellows.ezsp
import bellows.zigbee.application
import bellows.zigbee.endpoint
import bellows.types as t
from bellows.zigbee.zdo.types import CLUSTER_ID as ZDO_CLUSTER_ID
from . import opts
from . import util
from .main import main


@main.command()
@opts.database_file
@opts.channel
@opts.pan
@opts.extended_pan
@click.pass_context
def form(ctx, database, channel, pan_id, extended_pan_id):
    """Form a new ZigBee network"""
    ctx.obj['database_file'] = database

    def inner(ctx):
        app = ctx.obj['app']
        yield from app.initialize()
        yield from app.form_network(channel, pan_id, extended_pan_id)

    return util.app(inner, app_startup=False)(ctx)

@main.command()
@opts.database_file
@opts.wshost
@opts.wsport
@opts.resthost
@opts.restport
@opts.restapikey
@click.pass_context
def standalone(ctx, database, wshost, wsport, resthost, restport, rest_api_key):
    """Run a standalone server."""
    import bellows.standalone
    ctx.obj['database_file'] = database
    ctx.obj['wshost'] = wshost
    ctx.obj['wsport'] = wsport
    ctx.obj['resthost'] = resthost
    ctx.obj['restport'] = restport
    ctx.obj['rest_api_key'] = rest_api_key

    return util.app(bellows.standalone.start, app_startup=False, run_forever=True)(ctx)

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
@click.argument('node', type=util.ZigbeeNodeParamType())
@click.argument('code')
@opts.database_file
@opts.duration_s
@click.pass_context
def permit_with_key(ctx, database, duration_s, node, code):
    """Allow devices to join this ZigBee network using an install code"""
    ctx.obj['database_file'] = database
    code = binascii.unhexlify(code)

    def inner(ctx):
        app = ctx.obj['app']
        try:
            yield from app.permit_with_key(node, code, duration_s)

            click.echo("Joins are permitted for the next %ss..." % (duration_s, ))
            yield from asyncio.sleep(duration_s + 1)
            click.echo("Done")
        except Exception as e:
            click.echo(e)

    return util.app(inner)(ctx)


@main.command()
@opts.database_file
@click.pass_context
def devices(ctx, database):
    """Show device database"""

    def print_clusters(title, clusters):
        clusters = sorted(list(clusters.items()))
        if clusters:
            click.echo("      %s:" % (title, ))
        for cluster_id, cluster in clusters:
            click.echo("        %s (%s)" % (
                cluster.name, cluster_id
            ))

    ezsp = bellows.ezsp.EZSP()
    app = bellows.zigbee.application.ControllerApplication(ezsp, database)
    for ieee, dev in app.devices.items():
        click.echo("Device:")
        click.echo("  NWK: 0x%04x" % (dev.nwk, ))
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
                print_clusters("Input Clusters", ep.in_clusters)
                print_clusters("Output Clusters", ep.out_clusters)


@main.group()
@click.pass_context
@opts.database_file
@click.argument('node', type=util.ZigbeeNodeParamType())
def zdo(ctx, node, database):
    """Perform ZDO operations against a device"""
    ctx.obj['node'] = node
    ctx.obj['database_file'] = database


@zdo.command()
@click.pass_context
@util.app
def endpoints(ctx):
    """List endpoints on a device"""
    app = ctx.obj['app']
    node = ctx.obj['node']

    dev = util.get_device(app, node)
    if dev is None:
        return

    v = yield from dev.zdo.request(ZDO_CLUSTER_ID.Active_EP_req, dev.nwk)
    if v[0] != 0:
        click.echo("Non-success response: %s" % (v, ))
    else:
        click.echo(v[2])


@zdo.command()
@click.pass_context
@util.app
@click.argument('endpoint', type=click.IntRange(1, 255))
def get_endpoint(ctx, endpoint):
    """Show an endpoint's simple descriptor"""
    app = ctx.obj['app']
    node = ctx.obj['node']

    dev, endp = util.get_endpoint(app, node, endpoint)
    if endp is None:
        return

    v = yield from dev.zdo.request(0x0004, dev.nwk, endpoint)
    if v[0] != 0:
        click.echo("Non-success response: %s" % (v, ))
    else:
        click.echo(v[2])


@zdo.command()
@click.pass_context
@click.argument('endpoint', type=click.IntRange(1, 255))
@click.argument('cluster', type=click.IntRange(0, 65535))
@util.app
def bind(ctx, endpoint, cluster):
    """Bind to a cluster on a node"""
    app = ctx.obj['app']
    node = ctx.obj['node']

    dev, endp, clust = util.get_in_cluster(app, node, endpoint, cluster)
    if clust is None:
        return

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
    node = ctx.obj['node']

    dev, endp, clust = util.get_in_cluster(app, node, endpoint, cluster)
    if clust is None:
        return

    v = yield from dev.zdo.unbind(endpoint, cluster)
    click.echo(v)


@zdo.command()
@click.pass_context
@util.app
def leave(ctx):
    """Tell a node to leave the network"""
    app = ctx.obj['app']

    v = yield from app.remove(ctx.obj['node'])
    click.echo(v)


@main.group()
@click.pass_context
@opts.database_file
@opts.arg_node
@opts.arg_endpoint
@opts.arg_cluster
def zcl(ctx, database, node, cluster, endpoint):
    """Peform ZCL operations against a device"""
    ctx.obj['database_file'] = database
    ctx.obj['node'] = node
    ctx.obj['endpoint'] = endpoint
    ctx.obj['cluster'] = cluster


@zcl.command()
@click.pass_context
@opts.arg_attribute
@util.app
def read_attribute(ctx, attribute):
    app = ctx.obj['app']
    node = ctx.obj['node']
    endpoint_id = ctx.obj['endpoint']
    cluster_id = ctx.obj['cluster']

    dev, endpoint, cluster = util.get_in_cluster(app, node, endpoint_id, cluster_id)
    if cluster is None:
        return

    v = yield from cluster.read_attributes([attribute], allow_cache=False)
    if not v:
        click.echo("Received empty response")
    elif attribute not in v[0]:
        click.echo("Attribute %s not successful. Status=%s" % (
            attribute, v[1][attribute]
        ))
    else:
        click.echo("%s=%s" % (attribute, v[0][attribute]))


@zcl.command()
@click.pass_context
@opts.arg_attribute
@opts.arg_attribute_value
@util.app
def write_attribute(ctx, attribute, value):
    app = ctx.obj['app']
    node = ctx.obj['node']
    endpoint_id = ctx.obj['endpoint']
    cluster_id = ctx.obj['cluster']

    dev, endpoint, cluster = util.get_in_cluster(app, node, endpoint_id, cluster_id)
    if cluster is None:
        return

    v = yield from cluster.write_attributes({attribute: value})
    click.echo(v)


@zcl.command()
@click.pass_context
def commands(ctx):
    database = ctx.obj['database_file']
    node = ctx.obj['node']
    endpoint_id = ctx.obj['endpoint']
    cluster_id = ctx.obj['cluster']

    ezsp = bellows.ezsp.EZSP()
    app = bellows.zigbee.application.ControllerApplication(ezsp, database)

    dev, endpoint, cluster = util.get_in_cluster(app, node, endpoint_id, cluster_id)
    if cluster is None:
        return

    for c in cluster.commands:
        click.echo(c)


@zcl.command()
@click.pass_context
@click.argument('command')
@click.argument('parameters', nargs=-1)
@util.app
def command(ctx, command, parameters):
    app = ctx.obj['app']
    node = ctx.obj['node']
    endpoint_id = ctx.obj['endpoint']
    cluster_id = ctx.obj['cluster']

    dev, endpoint, cluster = util.get_in_cluster(app, node, endpoint_id, cluster_id)
    if cluster is None:
        return

    try:
        v = yield from getattr(cluster, command)(*parameters)
        click.echo(v)
    except ValueError as e:
        click.echo(e)


@zcl.command()
@click.pass_context
@opts.arg_attribute
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
    node = ctx.obj['node']
    endpoint_id = ctx.obj['endpoint']
    cluster_id = ctx.obj['cluster']

    dev, endpoint, cluster = util.get_in_cluster(app, node, endpoint_id, cluster_id)
    if cluster is None:
        return

    v = yield from cluster.configure_reporting(
        attribute,
        min_interval,
        max_interval,
        reportable_change,
    )
    click.echo(v)
