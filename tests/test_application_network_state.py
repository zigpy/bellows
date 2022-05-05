import pytest
import zigpy.state
import zigpy.types as zigpy_t
import zigpy.zdo.types as zdo_t

import bellows.types as t

from tests.async_mock import AsyncMock
from tests.test_application import app, ezsp_mock  # noqa: F401


@pytest.fixture
def node_info():
    return zigpy.state.NodeInfo(
        nwk=zigpy_t.NWK(0x0000),
        ieee=zigpy_t.EUI64.convert("00:12:4b:00:1c:a1:b8:46"),
        logical_type=zdo_t.LogicalType.Coordinator,
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
        children=[zigpy_t.EUI64.convert("00:0B:57:FF:FE:2B:D4:57")],
        # If exposed by the stack, NWK addresses of other connected devices on the network
        nwk_addresses={
            # Two routers
            zigpy_t.EUI64.convert("CC:CC:CC:FF:FE:E6:8E:CA"): zigpy_t.NWK(0x44CB),
            zigpy_t.EUI64.convert("EC:1B:BD:FF:FE:2F:41:A4"): zigpy_t.NWK(0x0702),
            # Child device
            zigpy_t.EUI64.convert("00:0b:57:ff:fe:2b:d4:57"): zigpy_t.NWK(0xC06B),
        },
        stack_specific={"ezsp": {"hashed_tclk": "abcdabcdabcdabcdabcdabcdabcdabcd"}},
    )


def _mock_app_for_load(app):  # noqa: F811
    """Mock methods on the application and EZSP objects to run network state code."""
    ezsp = app._ezsp

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
    ezsp.getEui64 = AsyncMock(
        return_value=[t.EmberEUI64.convert("00:12:4b:00:1c:a1:b8:46")]
    )
    ezsp.getConfigurationValue = AsyncMock(return_value=[t.EmberStatus.SUCCESS, 5])

    def get_key(key_type):
        key = {
            ezsp.types.EmberKeyType.CURRENT_NETWORK_KEY: ezsp.types.EmberKeyStruct(
                bitmask=(
                    t.EmberKeyStructBitmask.KEY_HAS_OUTGOING_FRAME_COUNTER
                    | t.EmberKeyStructBitmask.KEY_HAS_SEQUENCE_NUMBER
                ),
                type=ezsp.types.EmberKeyType.CURRENT_NETWORK_KEY,
                key=t.EmberKeyData(bytes.fromhex("2ccade06b3090c310315b3d574d3c85a")),
                outgoingFrameCounter=118785,
                incomingFrameCounter=0,
                sequenceNumber=108,
                partnerEUI64=t.EmberEUI64.convert("00:00:00:00:00:00:00:00"),
            ),
            ezsp.types.EmberKeyType.TRUST_CENTER_LINK_KEY: ezsp.types.EmberKeyStruct(
                bitmask=(
                    t.EmberKeyStructBitmask.KEY_IS_AUTHORIZED
                    | t.EmberKeyStructBitmask.KEY_HAS_PARTNER_EUI64
                    | t.EmberKeyStructBitmask.KEY_HAS_OUTGOING_FRAME_COUNTER
                ),
                type=ezsp.types.EmberKeyType.TRUST_CENTER_LINK_KEY,
                key=t.EmberKeyData(bytes.fromhex("abcdabcdabcdabcdabcdabcdabcdabcd")),
                outgoingFrameCounter=8712428,
                incomingFrameCounter=0,
                sequenceNumber=0,
                partnerEUI64=t.EmberEUI64.convert("00:12:4b:00:1c:a1:b8:46"),
            ),
        }[key_type]

        return (t.EmberStatus.SUCCESS, key)

    ezsp.getKey = AsyncMock(side_effect=get_key)
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
                trustCenterLongAddress=t.EmberEUI64.convert("00:12:4b:00:1c:a1:b8:46"),
            ),
        )
    )


async def test_load_network_info_no_devices(app, network_info, node_info):  # noqa: F811
    """Test `load_network_info(load_devices=False)`"""
    _mock_app_for_load(app)

    await app.load_network_info(load_devices=False)

    assert app.state.node_info == node_info
    assert app.state.network_info == network_info.replace(
        key_table=[], children=[], nwk_addresses={}
    )


async def test_load_network_info_with_devices(
    app, network_info, node_info  # noqa: F811
):
    """Test `load_network_info(load_devices=True)`"""
    _mock_app_for_load(app)

    def get_child_data(index):
        if index == 0:
            status = t.EmberStatus.SUCCESS
        else:
            status = t.EmberStatus.NOT_JOINED

        return (
            status,
            app._ezsp.types.EmberChildData(
                eui64=t.EmberEUI64.convert("00:0b:57:ff:fe:2b:d4:57"),
                type=t.EmberNodeType.SLEEPY_END_DEVICE,
                id=t.EmberNodeId(0xC06B),
                phy=0,
                power=128,
                timeout=3,
            ),
        )

    app._ezsp.getChildData = AsyncMock(side_effect=get_child_data)

    def get_key_table_entry(index):
        if index < 14:
            status = t.EmberStatus.TABLE_ENTRY_ERASED
        else:
            status = t.EmberStatus.INDEX_OUT_OF_RANGE

        return (
            status,
            app._ezsp.types.EmberKeyStruct(
                bitmask=t.EmberKeyStructBitmask(244),
                type=app._ezsp.types.EmberKeyType(0x46),
                key=t.EmberKeyData(bytes.fromhex("b8a11c004b1200cdabcdabcdabcdabcd")),
                outgoingFrameCounter=8192,
                incomingFrameCounter=0,
                sequenceNumber=0,
                partnerEUI64=t.EmberEUI64.convert("00:12:4b:00:1c:a1:b8:46"),
            ),
        )

    app._ezsp.getKeyTableEntry = AsyncMock(side_effect=get_key_table_entry)

    def get_addr_table_node_id(index):
        return (
            {
                16: t.EmberNodeId(0x44CB),
                17: t.EmberNodeId(0x0702),
            }.get(index, t.EmberNodeId(0xFFFF)),
        )

    app._ezsp.getAddressTableRemoteNodeId = AsyncMock(
        side_effect=get_addr_table_node_id
    )

    def get_addr_table_eui64(index):
        if index < 16:
            return (t.EmberEUI64.convert("ff:ff:ff:ff:ff:ff:ff:ff"),)
        elif 16 <= index <= 17:
            return (
                {
                    16: t.EmberEUI64.convert("cc:cc:cc:ff:fe:e6:8e:ca"),
                    17: t.EmberEUI64.convert("ec:1b:bd:ff:fe:2f:41:a4"),
                }[index],
            )
        else:
            return (t.EmberEUI64.convert("00:00:00:00:00:00:00:00"),)

    app._ezsp.getAddressTableRemoteEui64 = AsyncMock(side_effect=get_addr_table_eui64)

    await app.load_network_info(load_devices=True)

    assert app.state.node_info == node_info
    assert app.state.network_info == network_info.replace(key_table=[])


def _mock_app_for_write(app, network_info, node_info):
    ezsp = app._ezsp

    ezsp.leaveNetwork = AsyncMock(return_value=[t.EmberStatus.NETWORK_DOWN])
    ezsp.getEui64 = AsyncMock(
        return_value=[t.EmberEUI64.convert("00:12:4b:00:1c:a1:b8:46")]
    )

    ezsp.setInitialSecurityState = AsyncMock(return_value=[t.EmberStatus.SUCCESS])
    ezsp.clearKeyTable = AsyncMock(return_value=[t.EmberStatus.SUCCESS])
    ezsp.getConfigurationValue = AsyncMock(
        return_value=[t.EmberStatus.SUCCESS, t.uint8_t(200)]
    )
    ezsp.addOrUpdateKeyTableEntry = AsyncMock(return_value=[t.EmberStatus.SUCCESS])
    ezsp.setValue = AsyncMock(return_value=[t.EmberStatus.SUCCESS])
    ezsp.formNetwork = AsyncMock(return_value=[t.EmberStatus.SUCCESS])
    ezsp.setValue = AsyncMock(return_value=[t.EmberStatus.SUCCESS])
    ezsp.setMfgToken = AsyncMock(return_value=[t.EmberStatus.SUCCESS])


async def test_write_network_info_failed_leave(app, network_info, node_info):
    _mock_app_for_write(app, network_info, node_info)

    app._ezsp.leaveNetwork.return_value = [t.EmberStatus.BAD_ARGUMENT]

    with pytest.raises(zigpy.exceptions.FormationFailure):
        await app.write_network_info(network_info=network_info, node_info=node_info)


async def test_write_network_info(app, network_info, node_info):
    _mock_app_for_write(app, network_info, node_info)

    await app.write_network_info(network_info=network_info, node_info=node_info)


async def test_write_network_info_write_new_eui64(app, network_info, node_info):
    _mock_app_for_write(app, network_info, node_info)

    # Differs from what is in `node_info`
    app._ezsp.getEui64.return_value = [t.EmberEUI64.convert("AA:AA:AA:AA:AA:AA:AA:AA")]

    await app.write_network_info(
        network_info=network_info.replace(
            stack_specific={
                "ezsp": {
                    "i_understand_i_can_update_eui64_only_once_and_i_still_want_to_do_it": True,
                    **network_info.stack_specific["ezsp"],
                }
            }
        ),
        node_info=node_info,
    )

    # The EUI64 is written
    expected_eui64 = t.EmberEUI64(node_info.ieee).serialize()
    app._ezsp.setMfgToken.assert_called_once_with(
        t.EzspMfgTokenId.MFG_CUSTOM_EUI_64, expected_eui64
    )


async def test_write_network_info_dont_write_new_eui64(app, network_info, node_info):
    _mock_app_for_write(app, network_info, node_info)

    # Differs from what is in `node_info`
    app._ezsp.getEui64.return_value = [t.EmberEUI64.convert("AA:AA:AA:AA:AA:AA:AA:AA")]

    await app.write_network_info(
        # We don't provide the magic key so nothing is written
        network_info=network_info,
        node_info=node_info,
    )

    # The EUI64 is *not* written
    app._ezsp.setMfgToken.assert_not_called()


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
        seen_keys.add(tuple(call.args[0].preconfiguredKey))

    # A new hashed key is randomly generated each time if none is provided
    assert len(seen_keys) == 10
