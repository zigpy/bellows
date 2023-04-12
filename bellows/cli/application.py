"""CLI commands which use the application framework"""

import asyncio
import binascii

import click
import zigpy.config
import zigpy.endpoint
import zigpy.exceptions

import bellows.config
import bellows.ezsp
import bellows.types as t
import bellows.zigbee.application

from . import opts, util
from .main import main


@main.command()
@opts.database_file
@opts.channel
@opts.extended_pan
@opts.pan
@opts.network_key
@opts.network_key_seq
@click.pass_context
def form(ctx, database, channel, pan_id, extended_pan_id, network_key, network_key_seq):
    """Form a new ZigBee network"""
    ctx.obj["database_file"] = database
    extra_config = {
        zigpy.config.CONF_NWK: {
            zigpy.config.CONF_NWK_CHANNEL: channel,
            zigpy.config.CONF_NWK_EXTENDED_PAN_ID: extended_pan_id,
            zigpy.config.CONF_NWK_PAN_ID: pan_id,
            zigpy.config.CONF_NWK_KEY: network_key,
            zigpy.config.CONF_NWK_KEY_SEQ: network_key_seq,
        }
    }

    async def inner(ctx):
        app = ctx.obj["app"]
        await app.startup(auto_form=True)

    return util.app(inner, app_startup=False, extra_config=extra_config)(ctx)


@main.command()
@opts.database_file
@opts.duration_s
@click.pass_context
def permit(ctx, database, duration_s):
    """Allow devices to join this ZigBee network"""
    ctx.obj["database_file"] = database

    async def inner(ctx):
        app = ctx.obj["app"]
        await app.permit(duration_s)

        click.echo(f"Joins are permitted for the next {duration_s}s...")
        await asyncio.sleep(duration_s + 1)
        click.echo("Done")

    return util.app(inner)(ctx)


@main.command()
@click.argument("node", type=util.ZigbeeNodeParamType())
@click.argument("code")
@opts.database_file
@opts.duration_s
@click.pass_context
def permit_with_key(ctx, database, duration_s, node, code):
    """Allow devices to join this ZigBee network using an install code"""
    ctx.obj["database_file"] = database
    code = binascii.unhexlify(code)

    async def inner(ctx):
        app = ctx.obj["app"]
        try:
            await app.permit_with_key(node, code, duration_s)

            click.echo(f"Joins are permitted for the next {duration_s}s...")
            await asyncio.sleep(duration_s + 1)
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
        clusters = sorted(clusters.items())
        if clusters:
            click.echo(f"      {title}:")
        for cluster_id, cluster in clusters:
            click.echo(f"        {cluster.name} ({cluster_id})")

    loop = asyncio.get_event_loop()
    config = {
        zigpy.config.CONF_DATABASE: database,
        bellows.config.CONF_DEVICE: {bellows.config.CONF_DEVICE_PATH: "/dev/null"},
    }
    config = bellows.config.CONFIG_SCHEMA(config)
    app = loop.run_until_complete(
        bellows.zigbee.application.ControllerApplication.new(config, start_radio=False)
    )
    for ieee, dev in app.devices.items():
        click.echo("Device:")
        click.echo(f"  NWK: 0x{dev.nwk:04x}")
        click.echo(f"  IEEE: {ieee}")
        click.echo("  Endpoints:")
        for epid, ep in dev.endpoints.items():
            if epid == 0:
                continue
            if ep.status == zigpy.endpoint.Status.NEW:
                click.echo("    %s: Uninitialized")
            else:
                click.echo(
                    "    %s: profile=0x%02x, device_type=%s"
                    % (epid, ep.profile_id, ep.device_type)
                )
                print_clusters("Input Clusters", ep.in_clusters)
                print_clusters("Output Clusters", ep.out_clusters)


@main.group()
@click.pass_context
@opts.database_file
@click.argument("node", type=util.ZigbeeNodeParamType())
def zdo(ctx, node, database):
    """Perform ZDO operations against a device"""
    ctx.obj["node"] = node
    ctx.obj["database_file"] = database


@zdo.command()
@click.pass_context
@util.app
async def endpoints(ctx):
    """List endpoints on a device"""
    app = ctx.obj["app"]
    node = ctx.obj["node"]

    dev = util.get_device(app, node)
    if dev is None:
        return

    try:
        v = await dev.zdo.request(0x0005, dev.nwk)
        if v[0] != t.EmberStatus.SUCCESS:
            click.echo(f"Non-success response: {v}")
        else:
            click.echo(v[2])
    except zigpy.exceptions.ZigbeeException as e:
        click.echo(e)


@zdo.command()
@click.pass_context
@util.app
@click.argument("endpoint", type=click.IntRange(1, 255))
async def get_endpoint(ctx, endpoint):
    """Show an endpoint's simple descriptor"""
    app = ctx.obj["app"]
    node = ctx.obj["node"]

    dev, endp = util.get_endpoint(app, node, endpoint)
    if endp is None:
        return

    try:
        v = await dev.zdo.request(0x0004, dev.nwk, endpoint)
        if v[0] != t.EmberStatus.SUCCESS:
            click.echo(f"Non-success response: {v}")
        else:
            click.echo(v[2])
    except zigpy.exceptions.ZigbeeException as e:
        click.echo(e)


@zdo.command()
@click.pass_context
@click.argument("endpoint", type=click.IntRange(1, 255))
@click.argument("cluster", type=click.IntRange(0, 65535))
@util.app
async def bind(ctx, endpoint, cluster):
    """Bind to a cluster on a node"""
    app = ctx.obj["app"]
    node = ctx.obj["node"]

    dev, endp, clust = util.get_in_cluster(app, node, endpoint, cluster)
    if clust is None:
        return

    try:
        v = await dev.zdo.bind(clust)
        click.echo(v)
    except zigpy.exceptions.ZigbeeException as e:
        click.echo(e)


@zdo.command()
@click.pass_context
@click.argument("endpoint", type=click.IntRange(1, 255))
@click.argument("cluster", type=click.IntRange(0, 65535))
@util.app
async def unbind(ctx, endpoint, cluster):
    """Unbind a cluster on a node"""
    app = ctx.obj["app"]
    node = ctx.obj["node"]

    dev, endp, clust = util.get_in_cluster(app, node, endpoint, cluster)
    if clust is None:
        return

    try:
        v = await dev.zdo.unbind(endpoint, cluster)
        click.echo(v)
    except zigpy.exceptions.ZigbeeException as e:
        click.echo(e)


@zdo.command()
@click.pass_context
@util.app
async def leave(ctx):
    """Tell a node to leave the network"""
    app = ctx.obj["app"]

    try:
        v = await app.remove(ctx.obj["node"])
        click.echo(v)
    except zigpy.exceptions.ZigbeeException as e:
        click.echo(e)


@main.group()
@click.pass_context
@opts.database_file
@click.argument("node", type=util.ZigbeeNodeParamType())
@click.argument("endpoint", type=click.IntRange(1, 255))
@click.argument("cluster", type=click.IntRange(0, 65535))
def zcl(ctx, database, node, cluster, endpoint):
    """Perform ZCL operations against a device"""
    ctx.obj["database_file"] = database
    ctx.obj["node"] = node
    ctx.obj["endpoint"] = endpoint
    ctx.obj["cluster"] = cluster


@zcl.command()
@click.pass_context
@click.argument("attribute", type=click.IntRange(0, 65535))
@opts.manufacturer
@util.app
async def read_attribute(ctx, attribute, manufacturer):
    app = ctx.obj["app"]
    node = ctx.obj["node"]
    endpoint_id = ctx.obj["endpoint"]
    cluster_id = ctx.obj["cluster"]

    dev, endpoint, cluster = util.get_in_cluster(app, node, endpoint_id, cluster_id)
    if cluster is None:
        return

    try:
        v = await cluster.read_attributes(
            [attribute], allow_cache=False, manufacturer=manufacturer
        )
        if not v:
            click.echo("Received empty response")
        elif attribute not in v[0]:
            click.echo(
                "Attribute {} not successful. Status={}".format(
                    attribute, v[1][attribute]
                )
            )
        else:
            click.echo(f"{attribute}={v[0][attribute]}")
    except zigpy.exceptions.ZigbeeException as e:
        click.echo(e)


@zcl.command()
@click.pass_context
@click.argument("attribute", type=click.IntRange(0, 65535))
@click.argument("value", type=click.IntRange(0, 65535))
@opts.manufacturer
@util.app
async def write_attribute(ctx, attribute, value, manufacturer):
    app = ctx.obj["app"]
    node = ctx.obj["node"]
    endpoint_id = ctx.obj["endpoint"]
    cluster_id = ctx.obj["cluster"]

    dev, endpoint, cluster = util.get_in_cluster(app, node, endpoint_id, cluster_id)
    if cluster is None:
        return

    try:
        v = await cluster.write_attributes(
            {attribute: value}, manufacturer=manufacturer
        )
        click.echo(v)
    except zigpy.exceptions.ZigbeeException as e:
        click.echo(e)


@zcl.command()
@click.pass_context
@util.app
async def commands(ctx):
    app = ctx.obj["app"]
    node = ctx.obj["node"]
    endpoint_id = ctx.obj["endpoint"]
    cluster_id = ctx.obj["cluster"]

    dev, endpoint, cluster = util.get_in_cluster(app, node, endpoint_id, cluster_id)
    if cluster is None:
        return

    for c in cluster.commands:
        click.echo(c)


@zcl.command()
@click.pass_context
@click.argument("command")
@click.argument("parameters", nargs=-1)
@opts.manufacturer
@util.app
async def command(ctx, command, parameters, manufacturer):
    app = ctx.obj["app"]
    node = ctx.obj["node"]
    endpoint_id = ctx.obj["endpoint"]
    cluster_id = ctx.obj["cluster"]

    dev, endpoint, cluster = util.get_in_cluster(app, node, endpoint_id, cluster_id)
    if cluster is None:
        return

    try:
        v = await getattr(cluster, command)(*parameters, manufacturer=manufacturer)
        click.echo(v)
    except ValueError as e:
        click.echo(e)
    except zigpy.exceptions.ZigbeeException as e:
        click.echo(e)


@zcl.command()
@click.pass_context
@click.argument("attribute", type=click.IntRange(0, 65535))
@click.argument("min_interval", type=click.IntRange(0, 65535))
@click.argument("max_interval", type=click.IntRange(0, 65535))
@click.argument("reportable_change", type=click.INT)
@util.app
async def configure_reporting(
    ctx, attribute, min_interval, max_interval, reportable_change
):
    app = ctx.obj["app"]
    node = ctx.obj["node"]
    endpoint_id = ctx.obj["endpoint"]
    cluster_id = ctx.obj["cluster"]

    dev, endpoint, cluster = util.get_in_cluster(app, node, endpoint_id, cluster_id)
    if cluster is None:
        return

    try:
        v = await cluster.configure_reporting(
            attribute, min_interval, max_interval, reportable_change
        )
        click.echo(v)
    except zigpy.exceptions.ZigbeeException as e:
        click.echo(e)
