import importlib.metadata

import pytest
import zigpy.exceptions
import zigpy.state
import zigpy.types as zigpy_t
import zigpy.zdo.types as zdo_t

from bellows.exception import EzspError
from bellows.ezsp import EZSP
import bellows.types as t

from tests.async_mock import AsyncMock, PropertyMock
from tests.test_application import app, ezsp_mock, ieee, make_app


@pytest.fixture
def node_info():
    return zigpy.state.NodeInfo(
        nwk=zigpy_t.NWK(0x0000),
        ieee=zigpy_t.EUI64.convert("00:12:4b:00:1c:a1:b8:46"),
        logical_type=zdo_t.LogicalType.Coordinator,
        model="Mock board",
        manufacturer="Mock Manufacturer",
        version="Mock version",
    )


@pytest.fixture
def network_info(node_info):
    return zigpy.state.NetworkInfo(
        extended_pan_id=zigpy_t.ExtendedPanId.convert("bd:27:0b:38:37:95:dc:87"),
        pan_id=zigpy_t.PanId(0x9BB0),
        nwk_update_id=18,
        nwk_manager_id=zigpy_t.NWK(0x0000),
        channel=zigpy_t.uint8_t(15),
        channel_mask=zigpy_t.Channels.ALL_CHANNELS,
        security_level=zigpy_t.uint8_t(5),
        network_key=zigpy.state.Key(
            key=zigpy_t.KeyData.convert("2ccade06b3090c310315b3d574d3c85a"),
            seq=108,
            tx_counter=118785,
        ),
        tc_link_key=zigpy.state.Key(
            key=zigpy_t.KeyData(b"ZigBeeAlliance09"),
            partner_ieee=node_info.ieee,
            tx_counter=8712428,
        ),
        key_table=[
            zigpy.state.Key(
                key=zigpy_t.KeyData.convert(
                    "85:7C:05:00:3E:76:1A:F9:68:9A:49:41:6A:60:5C:76"
                ),
                tx_counter=3792973670,
                rx_counter=1083290572,
                seq=147,
                partner_ieee=zigpy_t.EUI64.convert("CC:CC:CC:FF:FE:E6:8E:CA"),
            ),
            zigpy.state.Key(
                key=zigpy_t.KeyData.convert(
                    "CA:02:E8:BB:75:7C:94:F8:93:39:D3:9C:B3:CD:A7:BE"
                ),
                tx_counter=2597245184,
                rx_counter=824424412,
                seq=19,
                partner_ieee=zigpy_t.EUI64.convert("EC:1B:BD:FF:FE:2F:41:A4"),
            ),
        ],
        children=[
            zigpy_t.EUI64.convert("00:0B:57:FF:FE:2B:D4:57"),
        ],
        # If exposed by the stack, NWK addresses of other connected devices on the network
        nwk_addresses={
            # Two routers
            zigpy_t.EUI64.convert("CC:CC:CC:FF:FE:E6:8E:CA"): zigpy_t.NWK(0x44CB),
            zigpy_t.EUI64.convert("EC:1B:BD:FF:FE:2F:41:A4"): zigpy_t.NWK(0x0702),
            # Child device
            zigpy_t.EUI64.convert("00:0b:57:ff:fe:2b:d4:57"): zigpy_t.NWK(0xC06B),
        },
        stack_specific={"ezsp": {"hashed_tclk": "abcdabcdabcdabcdabcdabcdabcdabcd"}},
        source=f"bellows@{importlib.metadata.version('bellows')}",
    )


def _mock_app_for_load(app, ezsp_ver=7):
    """Mock methods on the application and EZSP objects to run network state code."""
    ezsp = app._ezsp
    ezsp.ezsp_version = ezsp_ver
    type(ezsp).types = EZSP._BY_VERSION[ezsp_ver].types

    app._ensure_network_running = AsyncMock()
    ezsp.getNetworkParameters = AsyncMock(
        return_value=[
            t.EmberStatus.SUCCESS,
            t.EmberNodeType.COORDINATOR,
            t.EmberNetworkParameters(
                extendedPanId=t.ExtendedPanId.convert("bd:27:0b:38:37:95:dc:87"),
                panId=t.EmberPanId(0x9BB0),
                radioTxPower=8,
                radioChannel=15,
                joinMethod=t.EmberJoinMethod.USE_MAC_ASSOCIATION,
                nwkManagerId=t.EmberNodeId(0x0000),
                nwkUpdateId=18,
                channels=t.Channels.ALL_CHANNELS,
            ),
        ]
    )

    ezsp.getNodeId = AsyncMock(return_value=[t.EmberNodeId(0x0000)])
    ezsp.getEui64 = AsyncMock(return_value=[t.EUI64.convert("00:12:4b:00:1c:a1:b8:46")])

    def get_configuration_value(config_id):
        size = {
            app._ezsp.types.EzspConfigId.CONFIG_ADDRESS_TABLE_SIZE: t.uint8_t(20),
            app._ezsp.types.EzspConfigId.CONFIG_KEY_TABLE_SIZE: t.uint8_t(13),
            app._ezsp.types.EzspConfigId.CONFIG_SECURITY_LEVEL: t.uint8_t(5),
        }[config_id]

        return [app._ezsp.types.EmberStatus.SUCCESS, size]

    ezsp.getConfigurationValue = AsyncMock(side_effect=get_configuration_value)

    ezsp.getCurrentSecurityState = AsyncMock(
        return_value=(
            t.EmberStatus.SUCCESS,
            ezsp.types.EmberCurrentSecurityState(
                bitmask=(
                    t.EmberCurrentSecurityBitmask.TRUST_CENTER_USES_HASHED_LINK_KEY
                    | 64
                    | 32
                    | t.EmberCurrentSecurityBitmask.HAVE_TRUST_CENTER_LINK_KEY
                    | t.EmberCurrentSecurityBitmask.GLOBAL_LINK_KEY
                ),
                trustCenterLongAddress=t.EUI64.convert("00:12:4b:00:1c:a1:b8:46"),
            ),
        )
    )

    def get_key(key_type):
        key = {
            ezsp.types.EmberKeyType.CURRENT_NETWORK_KEY: ezsp.types.EmberKeyStruct(
                bitmask=(
                    t.EmberKeyStructBitmask.KEY_HAS_OUTGOING_FRAME_COUNTER
                    | t.EmberKeyStructBitmask.KEY_HAS_SEQUENCE_NUMBER
                ),
                type=ezsp.types.EmberKeyType.CURRENT_NETWORK_KEY,
                key=t.KeyData.convert("2ccade06b3090c310315b3d574d3c85a"),
                outgoingFrameCounter=118785,
                incomingFrameCounter=0,
                sequenceNumber=108,
                partnerEUI64=t.EUI64.convert("00:00:00:00:00:00:00:00"),
            ),
            ezsp.types.EmberKeyType.TRUST_CENTER_LINK_KEY: ezsp.types.EmberKeyStruct(
                bitmask=(
                    t.EmberKeyStructBitmask.KEY_IS_AUTHORIZED
                    | t.EmberKeyStructBitmask.KEY_HAS_PARTNER_EUI64
                    | t.EmberKeyStructBitmask.KEY_HAS_OUTGOING_FRAME_COUNTER
                ),
                type=ezsp.types.EmberKeyType.TRUST_CENTER_LINK_KEY,
                key=t.KeyData.convert("abcdabcdabcdabcdabcdabcdabcdabcd"),
                outgoingFrameCounter=8712428,
                incomingFrameCounter=0,
                sequenceNumber=0,
                partnerEUI64=t.EUI64.convert("00:12:4b:00:1c:a1:b8:46"),
            ),
        }[key_type]

        return (t.EmberStatus.SUCCESS, key)

    ezsp.getKey = AsyncMock(side_effect=get_key)

    if ezsp_ver >= 13:

        def export_key(security_context):
            key = {
                ezsp.types.sl_zb_sec_man_key_type_t.NETWORK: t.KeyData.convert(
                    "2ccade06b3090c310315b3d574d3c85a"
                ),
                ezsp.types.sl_zb_sec_man_key_type_t.TC_LINK: t.KeyData.convert(
                    "abcdabcdabcdabcdabcdabcdabcdabcd"
                ),
            }[security_context.core_key_type]

            return (key, t.EmberStatus.SUCCESS)

        ezsp.exportKey = AsyncMock(side_effect=export_key)
        ezsp.getNetworkKeyInfo = AsyncMock(
            return_value=[
                ezsp.types.sl_Status.SL_STATUS_OK,
                0x1234,
                ezsp.types.sl_zb_sec_man_network_key_info_t(
                    network_key_set=True,
                    alternate_network_key_set=False,
                    network_key_sequence_number=108,
                    alt_network_key_sequence_number=0,
                    network_key_frame_counter=118785,
                ),
            ]
        )


async def test_load_network_info_no_devices(app, network_info, node_info):
    """Test `load_network_info(load_devices=False)`"""
    _mock_app_for_load(app)

    await app.load_network_info(load_devices=False)

    assert app.state.node_info == node_info
    assert app.state.network_info == network_info.replace(
        key_table=[],
        children=[],
        nwk_addresses={},
        metadata=app.state.network_info.metadata,
    )


async def test_load_network_info_no_key_set(app, network_info, node_info):
    """Test loading network info in v13+ when no network key is set."""
    _mock_app_for_load(app, ezsp_ver=13)

    app._ezsp.getNetworkKeyInfo = AsyncMock(
        return_value=[
            app._ezsp.types.sl_Status.SL_STATUS_OK,
            0x1234,
            app._ezsp.types.sl_zb_sec_man_network_key_info_t(
                network_key_set=False,  # Not set
                alternate_network_key_set=False,
                network_key_sequence_number=108,
                alt_network_key_sequence_number=0,
                network_key_frame_counter=118785,
            ),
        ]
    )

    with pytest.raises(zigpy.exceptions.NetworkNotFormed):
        await app.load_network_info(load_devices=False)


@pytest.mark.parametrize("ezsp_ver", [4, 6, 7, 13])
async def test_load_network_info_with_devices(app, network_info, node_info, ezsp_ver):
    """Test `load_network_info(load_devices=True)`"""
    _mock_app_for_load(app, ezsp_ver)

    def get_child_data_v6(index):
        if index == 0:
            status = t.EmberStatus.SUCCESS
        else:
            status = t.EmberStatus.NOT_JOINED

        return (
            status,
            t.EmberNodeId(0xC06B),
            t.EUI64.convert("00:0b:57:ff:fe:2b:d4:57"),
            t.EmberNodeType.SLEEPY_END_DEVICE,
        )

    def get_child_data_v7(index):
        if index == 0:
            status = t.EmberStatus.SUCCESS
        else:
            status = t.EmberStatus.NOT_JOINED

        return (
            status,
            app._ezsp.types.EmberChildData(
                eui64=t.EUI64.convert("00:0b:57:ff:fe:2b:d4:57"),
                type=t.EmberNodeType.SLEEPY_END_DEVICE,
                id=t.EmberNodeId(0xC06B),
                phy=0,
                power=128,
                timeout=3,
            ),
        )

    app._ezsp.ezsp_version = ezsp_ver
    app._ezsp.getChildData = AsyncMock(
        side_effect={
            13: get_child_data_v7,
            7: get_child_data_v7,
            6: get_child_data_v6,
            4: get_child_data_v6,
        }[ezsp_ver]
    )

    if ezsp_ver < 13:

        def get_key_table_entry(index):
            if index == 0:
                return (
                    t.EmberStatus.SUCCESS,
                    app._ezsp.types.EmberKeyStruct(
                        bitmask=(
                            t.EmberKeyStructBitmask.KEY_IS_AUTHORIZED
                            | t.EmberKeyStructBitmask.KEY_HAS_PARTNER_EUI64
                            | t.EmberKeyStructBitmask.KEY_HAS_INCOMING_FRAME_COUNTER
                            | t.EmberKeyStructBitmask.KEY_HAS_OUTGOING_FRAME_COUNTER
                        ),
                        type=app._ezsp.types.EmberKeyType.APPLICATION_LINK_KEY,
                        key=t.KeyData.convert("857C05003E761AF9689A49416A605C76"),
                        outgoingFrameCounter=3792973670,
                        incomingFrameCounter=1083290572,
                        sequenceNumber=147,
                        partnerEUI64=t.EUI64.convert("CC:CC:CC:FF:FE:E6:8E:CA"),
                    ),
                )
            elif index == 1:
                return (
                    t.EmberStatus.SUCCESS,
                    app._ezsp.types.EmberKeyStruct(
                        bitmask=(
                            t.EmberKeyStructBitmask.KEY_IS_AUTHORIZED
                            | t.EmberKeyStructBitmask.KEY_HAS_PARTNER_EUI64
                            | t.EmberKeyStructBitmask.KEY_HAS_INCOMING_FRAME_COUNTER
                            | t.EmberKeyStructBitmask.KEY_HAS_OUTGOING_FRAME_COUNTER
                        ),
                        type=app._ezsp.types.EmberKeyType.APPLICATION_LINK_KEY,
                        key=t.KeyData.convert("CA02E8BB757C94F89339D39CB3CDA7BE"),
                        outgoingFrameCounter=2597245184,
                        incomingFrameCounter=824424412,
                        sequenceNumber=19,
                        partnerEUI64=t.EUI64.convert("EC:1B:BD:FF:FE:2F:41:A4"),
                    ),
                )
            elif index >= 12:
                status = t.EmberStatus.INDEX_OUT_OF_RANGE
            else:
                status = t.EmberStatus.TABLE_ENTRY_ERASED

            return (
                status,
                app._ezsp.types.EmberKeyStruct(
                    bitmask=t.EmberKeyStructBitmask(244),
                    type=app._ezsp.types.EmberKeyType(0x46),
                    key=t.KeyData.convert("b8a11c004b1200cdabcdabcdabcdabcd"),
                    outgoingFrameCounter=8192,
                    incomingFrameCounter=0,
                    sequenceNumber=0,
                    partnerEUI64=t.EUI64.convert("00:12:4b:00:1c:a1:b8:46"),
                ),
            )

        app._ezsp.getKeyTableEntry = AsyncMock(side_effect=get_key_table_entry)
    else:

        def export_link_key_by_index(index):
            if index == 0:
                return (
                    t.EUI64.convert("CC:CC:CC:FF:FE:E6:8E:CA"),
                    t.KeyData.convert("857C05003E761AF9689A49416A605C76"),
                    app._ezsp.types.sl_zb_sec_man_aps_key_metadata_t(
                        bitmask=(
                            t.EmberKeyStructBitmask.KEY_IS_AUTHORIZED
                            | t.EmberKeyStructBitmask.KEY_HAS_PARTNER_EUI64
                            | t.EmberKeyStructBitmask.KEY_HAS_INCOMING_FRAME_COUNTER
                            | t.EmberKeyStructBitmask.KEY_HAS_OUTGOING_FRAME_COUNTER
                        ),
                        outgoing_frame_counter=3792973670,
                        incoming_frame_counter=1083290572,
                        ttl_in_seconds=0,
                    ),
                    app._ezsp.types.sl_Status.SL_STATUS_OK,
                )
            elif index == 1:
                return (
                    t.EUI64.convert("EC:1B:BD:FF:FE:2F:41:A4"),
                    t.KeyData.convert("CA02E8BB757C94F89339D39CB3CDA7BE"),
                    app._ezsp.types.sl_zb_sec_man_aps_key_metadata_t(
                        bitmask=(
                            t.EmberKeyStructBitmask.KEY_IS_AUTHORIZED
                            | t.EmberKeyStructBitmask.KEY_HAS_PARTNER_EUI64
                            | t.EmberKeyStructBitmask.KEY_HAS_INCOMING_FRAME_COUNTER
                            | t.EmberKeyStructBitmask.KEY_HAS_OUTGOING_FRAME_COUNTER
                        ),
                        outgoing_frame_counter=2597245184,
                        incoming_frame_counter=824424412,
                        ttl_in_seconds=0,
                    ),
                    app._ezsp.types.sl_Status.SL_STATUS_OK,
                )

            return (
                t.EUI64.convert("7f:c9:35:e1:b0:00:00:00"),
                t.KeyData.convert("80:45:38:73:55:00:00:00:08:e4:35:c9:7f:00:00:00"),
                app._ezsp.types.sl_zb_sec_man_aps_key_metadata_t(
                    bitmask=t.EmberKeyStructBitmask(43976),
                    outgoing_frame_counter=85,
                    incoming_frame_counter=0,
                    ttl_in_seconds=0,
                ),
                app._ezsp.types.sl_Status.SL_STATUS_NOT_FOUND,
            )

        app._ezsp.exportLinkKeyByIndex = AsyncMock(side_effect=export_link_key_by_index)

    def get_addr_table_node_id(index):
        return (
            {
                16: t.EmberNodeId(0x44CB),
                17: t.EmberNodeId(0x0702),
                18: t.EmberNodeId(0x0000),  # bogus entry
            }.get(index, t.EmberNodeId(0xFFFF)),
        )

    app._ezsp.getAddressTableRemoteNodeId = AsyncMock(
        side_effect=get_addr_table_node_id
    )

    def get_addr_table_eui64(index):
        if index < 16:
            return (t.EUI64.convert("ff:ff:ff:ff:ff:ff:ff:ff"),)
        elif 16 <= index <= 18:
            return (
                {
                    16: t.EUI64.convert("cc:cc:cc:ff:fe:e6:8e:ca"),
                    17: t.EUI64.convert("ec:1b:bd:ff:fe:2f:41:a4"),
                    18: t.EUI64.convert("00:00:00:00:00:00:00:00"),
                }[index],
            )
        else:
            return (t.EUI64.convert("00:00:00:00:00:00:00:00"),)

    app._ezsp.getAddressTableRemoteEui64 = AsyncMock(side_effect=get_addr_table_eui64)

    await app.load_network_info(load_devices=True)

    nwk_addresses = network_info.nwk_addresses

    # v4 doesn't support address table reads so the only known addresses are from the
    # `getChildData` call
    if ezsp_ver == 4:
        nwk_addresses = {
            ieee: addr
            for ieee, addr in network_info.nwk_addresses.items()
            if ieee in network_info.children
        }
    else:
        nwk_addresses = network_info.nwk_addresses

    # EZSP doesn't provide a command to set the key sequence number
    assert app.state.network_info == network_info.replace(
        key_table=[key.replace(seq=0) for key in network_info.key_table],
        nwk_addresses=nwk_addresses,
        metadata=app.state.network_info.metadata,
        # TC link key does not have a TX counter
        tc_link_key=network_info.tc_link_key.replace(
            tx_counter=app.state.network_info.tc_link_key.tx_counter
        ),
    )
    assert app.state.node_info == node_info

    # No crash-prone calls were made
    if ezsp_ver == 4:
        app._ezsp.getAddressTableRemoteNodeId.assert_not_called()
        app._ezsp.getAddressTableRemoteEui64.assert_not_called()


def _mock_app_for_write(app, network_info, node_info, ezsp_ver=7):
    ezsp = app._ezsp
    ezsp.ezsp_version = ezsp_ver
    type(ezsp).types = EZSP._BY_VERSION[ezsp_ver].types

    network_state = ezsp.types.EmberNetworkStatus.JOINED_NETWORK
    ezsp.networkState = AsyncMock(side_effect=lambda: [network_state])

    def leave_network():
        nonlocal network_state
        network_state = ezsp.types.EmberNetworkStatus.NO_NETWORK

        return [t.EmberStatus.NETWORK_DOWN]

    def form_network(params):
        nonlocal network_state
        network_state = ezsp.types.EmberNetworkStatus.JOINED_NETWORK

        return [t.EmberStatus.SUCCESS]

    ezsp.leaveNetwork = AsyncMock(side_effect=leave_network)
    ezsp.formNetwork = AsyncMock(side_effect=form_network)

    ezsp.getEui64 = AsyncMock(return_value=[t.EUI64.convert("00:12:4b:00:1c:a1:b8:46")])

    ezsp.setInitialSecurityState = AsyncMock(return_value=[t.EmberStatus.SUCCESS])
    ezsp.clearKeyTable = AsyncMock(return_value=[t.EmberStatus.SUCCESS])
    ezsp.getConfigurationValue = AsyncMock(
        return_value=[t.EmberStatus.SUCCESS, t.uint8_t(200)]
    )

    if ezsp_ver >= 13:
        ezsp.importLinkKey = AsyncMock(
            side_effect=[
                # Only the first one succeeds
                (t.EmberStatus.SUCCESS,),
            ]
            + [
                # The rest will fail
                (t.EmberStatus.TABLE_FULL,),
            ]
            * 20
        )
    else:
        ezsp.addOrUpdateKeyTableEntry = AsyncMock(
            side_effect=[
                # Only the first one succeeds
                (t.EmberStatus.SUCCESS,),
            ]
            + [
                # The rest will fail
                (t.EmberStatus.TABLE_FULL,),
            ]
            * 20
        )

    if ezsp_ver == 4:
        ezsp.setValue = AsyncMock(return_value=[t.EmberStatus.BAD_ARGUMENT])
    else:
        ezsp.setValue = AsyncMock(return_value=[t.EmberStatus.SUCCESS])

    if ezsp_ver >= 9:
        ezsp.setChildData = AsyncMock(return_value=[t.EmberStatus.SUCCESS])

    ezsp.setValue = AsyncMock(return_value=[t.EmberStatus.SUCCESS])
    ezsp.setMfgToken = AsyncMock(return_value=[t.EmberStatus.SUCCESS])
    ezsp.getTokenData = AsyncMock(return_value=[t.EmberStatus.LIBRARY_NOT_PRESENT, b""])


@pytest.mark.parametrize("ezsp_ver", [4, 7, 13])
async def test_write_network_info(app, network_info, node_info, ezsp_ver):
    _mock_app_for_write(app, network_info, node_info, ezsp_ver)

    await app.write_network_info(
        network_info=network_info.replace(
            children=network_info.children
            + [
                # Bogus child that can't be restored
                zigpy_t.EUI64.convert("FF:FF:57:FF:FE:2B:D4:57")
            ]
        ),
        node_info=node_info,
    )


@pytest.mark.parametrize("can_burn", [True, False])
@pytest.mark.parametrize("can_rewrite", [True, False])
@pytest.mark.parametrize("force_write", [True, False])
async def test_write_network_info_write_eui64(
    caplog, app, network_info, node_info, can_burn, can_rewrite, force_write
):
    _mock_app_for_write(app, network_info, node_info)

    # Differs from what is in `node_info`
    app._ezsp.getEui64.return_value = [t.EUI64.convert("AA:AA:AA:AA:AA:AA:AA:AA")]
    app._ezsp.can_burn_userdata_custom_eui64 = AsyncMock(return_value=can_burn)
    app._ezsp.can_rewrite_custom_eui64 = AsyncMock(return_value=can_rewrite)

    await app.write_network_info(
        network_info=network_info.replace(
            stack_specific={
                "ezsp": {
                    "i_understand_i_can_update_eui64_only_once_and_i_still_want_to_do_it": force_write,
                    **network_info.stack_specific["ezsp"],
                }
            }
        ),
        node_info=node_info,
    )

    if can_rewrite:
        # Everything else is always ignored
        app._ezsp.write_custom_eui64.assert_called_once_with(node_info.ieee)
    elif can_burn and force_write:
        # Can only be forced
        app._ezsp.write_custom_eui64.assert_called_once_with(
            node_info.ieee, burn_into_userdata=True
        )
    else:
        # It is not written otherwise
        app._ezsp.write_custom_eui64.assert_not_called()

        if can_burn and not force_write:
            assert "does not match" in caplog.text
        elif not can_burn and force_write:
            assert "has already been written" in caplog.text
        elif not can_burn and not force_write:
            assert "does not match" in caplog.text
        else:
            assert False


async def test_write_network_info_generate_hashed_tclk(app, network_info, node_info):
    _mock_app_for_write(app, network_info, node_info)

    seen_keys = set()

    for i in range(10):
        app._ezsp.setInitialSecurityState.reset_mock()

        await app.write_network_info(
            network_info=network_info.replace(stack_specific={}),
            node_info=node_info,
        )

        call = app._ezsp.setInitialSecurityState.mock_calls[0]
        seen_keys.add(tuple(call[1][0].preconfiguredKey))

    # A new hashed key is randomly generated each time if none is provided
    assert len(seen_keys) == 10


async def test_reset_network_with_no_formed_network(app):
    _mock_app_for_write(app, network_info, node_info)

    app._ezsp.networkState = AsyncMock(
        return_value=[app._ezsp.types.EmberNetworkStatus.NO_NETWORK]
    )

    app._ezsp.networkInit = AsyncMock(return_value=[t.EmberStatus.NOT_JOINED])

    await app.reset_network_info()
