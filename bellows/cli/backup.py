import json
import logging

import bellows.types as t
import click

from . import util
from .main import main

LOGGER = logging.getLogger(__name__)

ATTR_CHANNEL = "channel"
ATTR_EXT_PAN_ID = "extended_pan_id"
ATTR_KEY = "key"
ATTR_KEY_FRAME_COUNTER = "frame_counter"
ATTR_KEY_GLOBAL = "tc_link_key"
ATTR_KEY_NWK = "network_key"
ATTR_KEY_SEQ = "sequence_number"
ATTR_KEY_TYPE = "key_type"
ATTR_NODE_EUI64 = "node_ieee"
ATTR_NODE_ID = "node_id"
ATTR_NODE_TYPE = "node_type"
ATTR_PAN_ID = "pan_id"


def _print_cb(frame_name, response):
    LOGGER.debug("%s callback: %s", frame_name, response)


@main.command()
@click.pass_context
@util.background
async def backup(ctx):
    """Backup NCP config to stdio."""
    click.echo("Backing up NCP")
    ezsp = await util.setup(ctx.obj["device"], ctx.obj["baudrate"], _print_cb)

    try:
        await _backup(ezsp)
    finally:
        ezsp.close()


def _dump_key(key):
    """Return a dict with key data."""
    return {
        ATTR_KEY_TYPE: key.type,
        ATTR_KEY: key.key,
        ATTR_KEY_FRAME_COUNTER: key.outgoingFrameCounter,
        ATTR_KEY_SEQ: key.sequenceNumber,
    }


async def _backup(ezsp):
    (status,) = await ezsp.networkInit()
    LOGGER.debug("Network init status: %s", status)
    assert status == t.EmberStatus.SUCCESS

    (status, node_type, network) = await ezsp.getNetworkParameters()
    assert status == t.EmberStatus.SUCCESS
    assert node_type == ezsp.types.EmberNodeType.COORDINATOR
    LOGGER.debug("Network params: %s", network)

    (node_id,) = await ezsp.getNodeId()
    (ieee,) = await ezsp.getEui64()

    result = {
        ATTR_NODE_TYPE: node_type.value,
        ATTR_NODE_ID: node_id,
        ATTR_NODE_EUI64: str(ieee),
        ATTR_PAN_ID: network.panId,
        ATTR_EXT_PAN_ID: str(network.extendedPanId),
    }

    for key_name, key_type in (
        (ATTR_KEY_GLOBAL, ezsp.types.EmberKeyType.TRUST_CENTER_LINK_KEY),
        (ATTR_KEY_NWK, ezsp.types.EmberKeyType.CURRENT_NETWORK_KEY),
    ):
        (status, key) = await ezsp.getKey(key_type)
        assert status == t.EmberStatus.SUCCESS
        LOGGER.debug("%s key: %s", key_name, key)
        result[key_name] = _dump_key(key)

    click.echo(json.dumps(result))
