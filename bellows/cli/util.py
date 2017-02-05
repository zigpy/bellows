import asyncio
import functools
import logging
import os

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


def app(f):
    loaded = False

    @asyncio.coroutine
    def async_inner(ctx, *args, **kwargs):
        global loaded
        app = yield from setup_application(ctx.obj['device'])
        app.load('zigbee.db')
        loaded = True
        ctx.obj['app'] = app
        yield from f(ctx, *args, **kwargs)
        yield from asyncio.sleep(0.5)

    def shutdown():
        if loaded:
            # Don't save the DB if we didn't fully load it
            app.save('zigbee.db')
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
    yield from s.version(4)

    @asyncio.coroutine
    def cfg(config_id, value):
        v = yield from s.setConfigurationValue(config_id, value)
        check(v[0], 'Setting config %s to %s: %s' % (config_id, value, v[0]))
    c = t.EzspConfigId

    if configure:
        LOGGER.debug("Configuring...")
        yield from cfg(c.EZSP_CONFIG_STACK_PROFILE, 2)
        yield from cfg(c.EZSP_CONFIG_SECURITY_LEVEL, 5)
        yield from cfg(c.EZSP_CONFIG_SUPPORTED_NETWORKS, 1)
        yield from cfg(c.EZSP_CONFIG_PACKET_BUFFER_COUNT, 0xff)

    return s


@asyncio.coroutine
def setup_application(dev):
    s = bellows.ezsp.EZSP()
    yield from s.connect(dev)
    app = bellows.zigbee.application.ControllerApplication(s)
    yield from app.startup()
    return app


def zha_security(controller=False):
    empty_key_data = t.EmberKeyData()
    empty_key_data.contents = t.fixed_list(16, t.uint8_t)([t.uint8_t(0)] * 16)
    zha_key = t.EmberKeyData()
    zha_key.contents = t.fixed_list(16, t.uint8_t)(
        [t.uint8_t(c) for c in b'ZigBeeAlliance09']
    )

    isc = t.EmberInitialSecurityState()
    isc.bitmask = t.uint16_t(
        t.EmberInitialSecurityBitmask.EMBER_HAVE_PRECONFIGURED_KEY |
        t.EmberInitialSecurityBitmask.EMBER_REQUIRE_ENCRYPTED_KEY
    )
    isc.preconfiguredKey = zha_key
    isc.networkKey = empty_key_data
    isc.networkKeySequenceNumber = t.uint8_t(0)
    isc.preconfiguredTrustCenterEui64 = t.EmberEUI64(
        [t.uint8_t(0)] * 8
    )

    if controller:
        isc.bitmask |= (
            t.EmberInitialSecurityBitmask.EMBER_TRUST_CENTER_GLOBAL_LINK_KEY |
            t.EmberInitialSecurityBitmask.EMBER_HAVE_NETWORK_KEY
        )
        isc.bitmask = t.uint16_t(isc.bitmask)
        random_key = t.fixed_list(16, t.uint8_t)(
            [t.uint8_t(x) for x in os.urandom(16)]
        )
        isc.networkKey = random_key
    return isc


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
        [0, t.EmberStatus.EMBER_NOT_JOINED],
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
        t.EzspPolicyId.EZSP_TC_KEY_REQUEST_POLICY,
        t.EzspDecisionId.EZSP_DENY_TC_KEY_REQUESTS,
    )
    yield from setPolicy(
        t.EzspPolicyId.EZSP_APP_KEY_REQUEST_POLICY,
        t.EzspDecisionId.EZSP_ALLOW_APP_KEY_REQUESTS,
    )
    yield from setPolicy(
        t.EzspPolicyId.EZSP_TRUST_CENTER_POLICY,
        t.EzspDecisionId.EZSP_ALLOW_PRECONFIGURED_KEY_JOINS,
    )
