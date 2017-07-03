import asyncio
import functools
import logging

import click

import bellows.ezsp
import bellows.types as t


LOGGER = logging.getLogger(__name__)


class CSVParamType(click.ParamType):
    name = 'comma separated integers'

    def __init__(self, min=None, max=None):
        self.intrange = click.IntRange(min, max)

    def convert(self, value, param, ctx):
        values = [
            self.intrange.convert(v, param, ctx) for v in value.split(',')
        ]
        return values


def async(f):
    @functools.wraps(f)
    def inner(*args, **kwargs):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(f(*args, **kwargs))

    return inner


def app(f, app_startup=True):
    database_file = None

    @asyncio.coroutine
    def async_inner(ctx, *args, **kwargs):
        nonlocal database_file
        database_file = ctx.obj['database_file']
        app = yield from setup_application(
            ctx.obj['device'],
            database_file,
            startup=app_startup,
        )
        ctx.obj['app'] = app
        yield from f(ctx, *args, **kwargs)
        yield from asyncio.sleep(0.5)

    def shutdown():
        try:
            app._ezsp.close()
        except:
            pass

    @functools.wraps(f)
    def inner(*args, **kwargs):
        loop = asyncio.get_event_loop()
        try:
            loop.run_until_complete(async_inner(*args, **kwargs))
        except:
            # It seems that often errors like a message send will try to send
            # two messages, and not reading all of them will leave the NCP in
            # a bad state. This seems to mitigate this somewhat. Better way?
            loop.run_until_complete(asyncio.sleep(0.5))
            raise
        finally:
            shutdown()

    return inner


def print_cb(frame_name, response):
    click.echo("Callback: %s %s" % (frame_name, response))


def channel_mask(channels):
    mask = 0
    for channel in channels:
        if not (11 <= channel <= 26):
            raise click.BadOptionUsage("channels must be from 11 to 26")
        mask |= 1 << channel
    return mask


@asyncio.coroutine
def setup(dev, cbh=None, configure=True):
    s = bellows.ezsp.EZSP()
    if cbh:
        s.add_callback(cbh)
    yield from s.connect(dev)
    LOGGER.debug("Connected. Resetting.")
    yield from s.reset()
    yield from s.version()

    @asyncio.coroutine
    def cfg(config_id, value):
        v = yield from s.setConfigurationValue(config_id, value)
        check(v[0], 'Setting config %s to %s: %s' % (config_id, value, v[0]))
    c = t.EzspConfigId

    if configure:
        LOGGER.debug("Configuring...")
        yield from cfg(c.CONFIG_STACK_PROFILE, 2)
        yield from cfg(c.CONFIG_SECURITY_LEVEL, 5)
        yield from cfg(c.CONFIG_SUPPORTED_NETWORKS, 1)
        yield from cfg(c.CONFIG_PACKET_BUFFER_COUNT, 0xff)

    return s


@asyncio.coroutine
def setup_application(dev, database_file, startup=True):
    s = bellows.ezsp.EZSP()
    yield from s.connect(dev)
    app = bellows.zigbee.application.ControllerApplication(s, database_file)
    if startup:
        yield from app.startup()
    return app


def check(ret, message, expected=0):
    if ret == expected:
        return
    if isinstance(expected, list) and ret in expected:
        return
    raise click.ClickException(message)


@asyncio.coroutine
def networkInit(s):
    v = yield from s.networkInit()
    check(
        v[0],
        "Failure initializing network: %s" % (v[0], ),
        [0, t.EmberStatus.NOT_JOINED],
    )
    return v


def parse_epan(epan):
    """Parse a user specified extended PAN ID"""
    l = [t.uint8_t(x, 16) for x in epan.split(":")]
    return t.fixed_list(8, t.uint8_t)(l)


@asyncio.coroutine
def basic_tc_permits(s):
    @asyncio.coroutine
    def setPolicy(policy, decision):
        v = yield from s.setPolicy(policy, decision)
        check(v[0], "Failed to set policy %s to %s: %s" % (
            policy, decision, v[0],
        ))

    yield from setPolicy(
        t.EzspPolicyId.TC_KEY_REQUEST_POLICY,
        t.EzspDecisionId.DENY_TC_KEY_REQUESTS,
    )
    yield from setPolicy(
        t.EzspPolicyId.APP_KEY_REQUEST_POLICY,
        t.EzspDecisionId.ALLOW_APP_KEY_REQUESTS,
    )
    yield from setPolicy(
        t.EzspPolicyId.TRUST_CENTER_POLICY,
        t.EzspDecisionId.ALLOW_PRECONFIGURED_KEY_JOINS,
    )


def get_device(app, node):
    if node not in app.devices:
        click.echo("Device %s is not in the device database" % (node, ))
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
        return(dev, endpoint, None)

    if cluster_id not in endpoint.in_clusters:
        click.echo("Device %s has no cluster %d on endpoint %d" % (node, cluster_id, endpoint_id))
        return(dev, endpoint, None)

    return (dev, endpoint, endpoint.in_clusters[cluster_id])
