import asyncio
import json
import logging

import bellows.types as t
import click
import voluptuous as vol
from zigpy.config.validators import cv_hex, cv_key

from . import util
from .main import main

LOGGER = logging.getLogger(__name__)

ATTR_CHANNELS = "channels"
ATTR_EXT_PAN_ID = "extendedPanId"
ATTR_KEY = "key"
ATTR_KEY_BITMASK = "bitmask"
ATTR_KEY_FRAME_COUNTER_IN = "incomingFrameCounter"
ATTR_KEY_FRAME_COUNTER_OUT = "outgoingFrameCounter"
ATTR_KEY_GLOBAL = "tc_link_key"
ATTR_KEY_NWK = "network_key"
ATTR_KEY_PARTNER = "partnerEUI64"
ATTR_KEY_SEQ = "sequenceNumber"
ATTR_KEY_TABLE = "key_table"
ATTR_KEY_TYPE = "type"
ATTR_NODE_EUI64 = "node_ieee"
ATTR_NODE_ID = "node_id"
ATTR_NODE_TYPE = "node_type"
ATTR_NWK_UPDATE_ID = "nwkUpdateId"
ATTR_PAN_ID = "panId"
ATTR_RADIO_CHANNEL = "radioChannel"
ATTR_RADIO_TX_PWR = "radioTxPower"

SCHEMA_KEY = vol.Schema(
    {
        ATTR_KEY_BITMASK: cv_hex,
        ATTR_KEY_TYPE: cv_hex,
        ATTR_KEY: cv_key,
        ATTR_KEY_FRAME_COUNTER_OUT: cv_hex,
        ATTR_KEY_FRAME_COUNTER_IN: cv_hex,
        ATTR_KEY_SEQ: cv_hex,
        ATTR_KEY_PARTNER: vol.All(str, t.EmberEUI64.convert),
    }
)
SCHEMA_BAK = vol.Schema(
    {
        ATTR_CHANNELS: cv_hex,
        ATTR_NODE_TYPE: cv_hex,
        ATTR_NODE_ID: cv_hex,
        ATTR_NODE_EUI64: vol.All(str, t.EmberEUI64.convert),
        ATTR_NWK_UPDATE_ID: cv_hex,
        ATTR_PAN_ID: cv_hex,
        ATTR_RADIO_CHANNEL: cv_hex,
        ATTR_RADIO_TX_PWR: cv_hex,
        ATTR_EXT_PAN_ID: vol.All(str, t.ExtendedPanId.convert),
        ATTR_KEY_GLOBAL: SCHEMA_KEY,
        ATTR_KEY_NWK: SCHEMA_KEY,
        ATTR_KEY_TABLE: vol.Any([], vol.Schema([SCHEMA_KEY])),
    }
)


def _print_cb(frame_name, response):
    LOGGER.debug("%s callback: %s", frame_name, response)


@main.command()
@click.pass_context
@util.background
async def backup(ctx):
    """Backup NCP config to stdio."""
    ezsp = await util.setup(ctx.obj["device"], ctx.obj["baudrate"], _print_cb)

    try:
        await _backup(ezsp)
    finally:
        ezsp.close()


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
        ATTR_RADIO_CHANNEL: network.radioChannel,
        ATTR_RADIO_TX_PWR: network.radioTxPower,
        ATTR_NWK_UPDATE_ID: network.nwkUpdateId,
        ATTR_CHANNELS: network.channels,
    }

    for key_name, key_type in (
        (ATTR_KEY_GLOBAL, ezsp.types.EmberKeyType.TRUST_CENTER_LINK_KEY),
        (ATTR_KEY_NWK, ezsp.types.EmberKeyType.CURRENT_NETWORK_KEY),
    ):
        (status, key) = await ezsp.getKey(key_type)
        assert status == t.EmberStatus.SUCCESS
        LOGGER.debug("%s key: %s", key_name, key)
        result[key_name] = key.as_dict()
        result[key_name][ATTR_KEY_PARTNER] = str(key.partnerEUI64)

    keys = await _backup_keys(ezsp)
    result[ATTR_KEY_TABLE] = keys

    click.echo(json.dumps(result))


async def _backup_keys(ezsp):
    """Backup keys."""

    keys = []
    for idx in range(0, 192):
        LOGGER.debug("Getting key index %s", idx)
        (status, key_struct) = await ezsp.getKeyTableEntry(idx)
        if status == t.EmberStatus.SUCCESS:
            key_dict = key_struct.as_dict()
            key_dict[ATTR_KEY_PARTNER] = str(key_struct.partnerEUI64)
            keys.append(key_dict)
        elif status == t.EmberStatus.INDEX_OUT_OF_RANGE:
            break
    return keys


@main.command()
@click.option("-f", "--force", is_flag=True, required=False, default=False)
@click.option("-B", "--backup-file", type=str, required=True)
@click.pass_context
@util.background
async def restore(ctx, backup_file, force):
    """Backup NCP config to stdio."""
    click.echo("Restoring NCP")
    try:
        with open(backup_file, "r") as file:
            backup_data = json.load(file)
            LOGGER.debug("loaded: %s", backup_data)
            backup_data = SCHEMA_BAK(backup_data)
            LOGGER.debug("schame pass: %s", backup_data)
    except OSError as exc:
        LOGGER.error(f"Couldn't import backup file: %s", exc)
        return
    except vol.Error as exc:
        LOGGER.error("backup file does not pass schema validation: %s", exc)
        return

    LOGGER.info("backup file: %s", backup_data)

    ezsp = await util.setup(ctx.obj["device"], ctx.obj["baudrate"], _print_cb)
    try:
        await _restore(ezsp, backup_data, force)
    finally:
        ezsp.close()


async def _restore(ezsp, backup_data, force):
    """Restore backup."""

    stack_up = asyncio.Future()
    stack_dwn = asyncio.Future()

    def _stack_handler(frame, args):
        if frame != "stackStatusHandler":
            return
        if args[0] == t.EmberStatus.NETWORK_UP:
            stack_up.set_result(True)
        else:
            stack_dwn.set_result(True)

    cb_id = ezsp.add_callback(_stack_handler)

    (status,) = await ezsp.networkInit()
    LOGGER.debug("Network init status: %s", status)
    assert status in (t.EmberStatus.SUCCESS, t.EmberStatus.NOT_JOINED)

    if status == t.EmberStatus.SUCCESS:
        if not force:
            click.echo("Network is up, not forcing restore")
            return
        try:
            await asyncio.wait_for(stack_up, timeout=5)
            await ezsp.leaveNetwork()
            await asyncio.wait_for(stack_dwn, timeout=15)
        except asyncio.TimeoutError:
            LOGGER.error("Didn't not receive stack changed status callback")
            return

    ezsp.remove_callback(cb_id)

    sec_bitmask = (
        t.EmberInitialSecurityBitmask.HAVE_PRECONFIGURED_KEY
        | t.EmberInitialSecurityBitmask.REQUIRE_ENCRYPTED_KEY
        | t.EmberInitialSecurityBitmask.TRUST_CENTER_GLOBAL_LINK_KEY
        | t.EmberInitialSecurityBitmask.HAVE_NETWORK_KEY
        | t.EmberInitialSecurityBitmask.NO_FRAME_COUNTER_RESET
    )
    init_sec_state = t.EmberInitialSecurityState(
        bitmask=sec_bitmask,
        preconfiguredKey=backup_data[ATTR_KEY_GLOBAL][ATTR_KEY],
        networkKey=backup_data[ATTR_KEY_NWK][ATTR_KEY],
        networkKeySequenceNumber=backup_data[ATTR_KEY_NWK][ATTR_KEY_SEQ],
        preconfiguredTrustCenterEui64=[0x00] * 8,
    )
    (status,) = await ezsp.setInitialSecurityState(init_sec_state)
    LOGGER.debug("Set initial security state: %s", status)
    assert status == t.EmberStatus.SUCCESS

    if backup_data[ATTR_KEY_TABLE]:
        await _restore_keys(ezsp, backup_data[ATTR_KEY_TABLE])

    network_key = backup_data[ATTR_KEY_NWK]
    (status,) = await ezsp.setValue(
        ezsp.types.EzspValueId.VALUE_NWK_FRAME_COUNTER,
        t.uint32_t(network_key[ATTR_KEY_FRAME_COUNTER_OUT]).serialize(),
    )
    LOGGER.debug("Set network frame counter: %s", status)
    assert status == t.EmberStatus.SUCCESS

    tc_key = backup_data[ATTR_KEY_GLOBAL]
    (status,) = await ezsp.setValue(
        ezsp.types.EzspValueId.VALUE_APS_FRAME_COUNTER,
        t.uint32_t(tc_key[ATTR_KEY_FRAME_COUNTER_OUT]).serialize(),
    )
    LOGGER.debug("Set network frame counter: %s", status)
    assert status == t.EmberStatus.SUCCESS

    await _form_network(ezsp, backup_data)


async def _restore_keys(ezsp, key_table):
    """Restore keys."""

    (status,) = await ezsp.setConfigurationValue(
        ezsp.types.EzspConfigId.CONFIG_KEY_TABLE_SIZE, len(key_table)
    )
    assert status == t.EmberStatus.SUCCESS

    for key in key_table:
        is_link_key = key[ATTR_KEY_TYPE] in (
            ezsp.types.EmberKeyType.APPLICATION_LINK_KEY,
            ezsp.types.EmberKeyType.TRUST_CENTER_LINK_KEY,
        )
        (status,) = await ezsp.addOrUpdateKeyTableEntry(
            key[ATTR_KEY_PARTNER], is_link_key, key[ATTR_KEY]
        )
        if status != t.EmberStatus.SUCCESS:
            LOGGER.warning("Couldn't add %s key: %s", key, status)
        await asyncio.sleep(0.2)


async def _form_network(ezsp, backup_data):
    """Form network."""
    network = t.EmberNetworkParameters(
        panId=backup_data[ATTR_PAN_ID],
        extendedPanId=backup_data[ATTR_EXT_PAN_ID],
        radioTxPower=backup_data[ATTR_RADIO_TX_PWR],
        radioChannel=backup_data[ATTR_RADIO_CHANNEL],
        joinMethod=t.EmberJoinMethod.USE_MAC_ASSOCIATION,
        nwkManagerId=0x0000,
        nwkUpdateId=backup_data[ATTR_NWK_UPDATE_ID],
        channels=backup_data[ATTR_CHANNELS],
    )
    (status,) = await ezsp.formNetwork(network)
    LOGGER.debug("Form network: %s", status)
    assert status == t.EmberStatus.NETWORK_UP

    (status,) = await ezsp.setValue(ezsp.types.EzspValueId.VALUE_STACK_TOKEN_WRITING, 1)
    LOGGER.debug("Set token writing: %s", status)
    assert status == t.EmberStatus.SUCCESS
