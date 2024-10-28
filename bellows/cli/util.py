import asyncio
import contextlib
import functools
import logging

import click
import zigpy.config as zigpy_conf

import bellows.ezsp
import bellows.types as t

LOGGER = logging.getLogger(__name__)


class CSVParamType(click.ParamType):
    name = "comma separated integers"

    def __init__(self, min=None, max=None):
        self.intrange = click.IntRange(min, max)

    def convert(self, value, param, ctx):
        values = [self.intrange.convert(v, param, ctx) for v in value.split(",")]
        return values


class ZigbeeNodeParamType(click.ParamType):
    name = "colon separated hex bytes"

    def convert(self, value, param, ctx):
        if ":" not in value or len(value) != 23:
            self.fail("Node format should be a 8 byte hex string separated by ':'")
        return t.EUI64.convert(value)


def background(f):
    @functools.wraps(f)
    def inner(*args, **kwargs):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(f(*args, **kwargs))

    return inner


def app(f, app_startup=True, extra_config=None):
    database_file = None
    application = None

    async def async_inner(ctx, *args, **kwargs):
        nonlocal database_file
        nonlocal application
        app_config = {
            zigpy_conf.CONF_DEVICE: {
                zigpy_conf.CONF_DEVICE_PATH: ctx.obj["device"],
                zigpy_conf.CONF_DEVICE_BAUDRATE: ctx.obj["baudrate"],
                zigpy_conf.CONF_DEVICE_FLOW_CONTROL: ctx.obj["flow_control"],
            },
            zigpy_conf.CONF_DATABASE: ctx.obj["database_file"],
        }
        if extra_config:
            app_config.update(extra_config)
        application = await setup_application(app_config, startup=app_startup)
        try:
            ctx.obj["app"] = application
            await f(ctx, *args, **kwargs)
        finally:
            with contextlib.suppress(Exception):
                await application.shutdown()

    @functools.wraps(f)
    def inner(*args, **kwargs):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(async_inner(*args, **kwargs))

    return inner


def print_cb(frame_name, response):
    click.echo(f"Callback: {frame_name} {response}")


def channel_mask(channels):
    mask = 0
    for channel in channels:
        if not (11 <= channel <= 26):
            raise click.BadOptionUsage("channels must be from 11 to 26")
        mask |= 1 << channel
    return mask


async def setup(dev, baudrate, cbh=None, configure=True):
    app_config = {
        zigpy_conf.CONF_DEVICE: {
            zigpy_conf.CONF_DEVICE_PATH: dev,
            zigpy_conf.CONF_DEVICE_BAUDRATE: baudrate,
            zigpy_conf.CONF_DEVICE_FLOW_CONTROL: zigpy_conf.CONF_DEVICE_FLOW_CONTROL_DEFAULT,
        }
    }

    app = bellows.zigbee.application.ControllerApplication(app_config)
    await app.connect()

    if cbh:
        app._ezsp.add_callback(cbh)

    return app._ezsp


async def setup_application(app_config, startup=True):
    app = await bellows.zigbee.application.ControllerApplication.new(
        app_config, start_radio=startup
    )
    return app


def check(ret, message, expected=0):
    if ret == expected:
        return
    if isinstance(expected, list) and ret in expected:
        return
    raise click.ClickException(message)


async def network_init(s):
    v = await s.initialize_network()
    check(
        v,
        f"Failure initializing network: {v}",
        t.sl_Status.OK,
    )
    return v


def parse_epan(epan):
    """Parse a user specified extended PAN ID"""
    epan_list = [t.uint8_t(x, 16) for x in epan.split(":")]
    return t.FixedList[t.uint8_t, 8](epan_list)


async def basic_tc_permits(s):
    async def set_policy(policy, decision):
        v = await s.setPolicy(policy, decision)
        check(v[0], f"Failed to set policy {policy} to {decision}: {v[0]}")

    await set_policy(
        t.EzspPolicyId.TC_KEY_REQUEST_POLICY,
        t.EzspDecisionId.DENY_TC_KEY_REQUESTS,
    )
    await set_policy(
        t.EzspPolicyId.APP_KEY_REQUEST_POLICY,
        t.EzspDecisionId.ALLOW_APP_KEY_REQUESTS,
    )
    await set_policy(
        t.EzspPolicyId.TRUST_CENTER_POLICY,
        t.EzspDecisionId.ALLOW_PRECONFIGURED_KEY_JOINS,
    )


def get_device(app, node):
    if node not in app.devices:
        click.echo(f"Device {node} is not in the device database")
        return None

    return app.devices[node]


def get_endpoint(app, node, endpoint_id):
    dev = get_device(app, node)
    if dev is None:
        return (dev, None)

    if endpoint_id not in dev.endpoints:
        click.echo("Device %s has no endpoint %d" % (node, endpoint_id))
        return (dev, None)

    return (dev, dev.endpoints[endpoint_id])


def get_in_cluster(app, node, endpoint_id, cluster_id):
    dev, endpoint = get_endpoint(app, node, endpoint_id)
    if endpoint is None:
        return (dev, endpoint, None)

    if cluster_id not in endpoint.in_clusters:
        click.echo(
            "Device %s has no cluster %d on endpoint %d"
            % (node, cluster_id, endpoint_id)
        )
        return (dev, endpoint, None)

    return (dev, endpoint, endpoint.in_clusters[cluster_id])
