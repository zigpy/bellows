import asyncio
import contextlib
import importlib.metadata
import logging
from unittest.mock import AsyncMock, MagicMock, PropertyMock, call, patch, sentinel

import pytest
import zigpy.backups
import zigpy.config
import zigpy.device
import zigpy.exceptions
import zigpy.types as zigpy_t
import zigpy.zdo.types as zdo_t

from bellows.ash import NcpFailure
import bellows.config as config
from bellows.exception import ControllerError, EzspError
import bellows.ezsp as ezsp
from bellows.ezsp.v9.commands import GetTokenDataRsp
from bellows.ezsp.xncp import FirmwareFeatures, FlowControlType
import bellows.types
import bellows.types as t
import bellows.types.struct
import bellows.uart as uart
import bellows.zigbee.application
from bellows.zigbee.application import ControllerApplication
import bellows.zigbee.device
from bellows.zigbee.device import EZSPEndpoint, EZSPGroupEndpoint
from bellows.zigbee.util import map_rssi_to_energy

from tests.common import mock_ezsp_commands

APP_CONFIG = {
    config.CONF_DEVICE: {
        zigpy.config.CONF_DEVICE_PATH: "/dev/null",
        zigpy.config.CONF_DEVICE_BAUDRATE: 115200,
    },
    zigpy.config.CONF_DATABASE: None,
    zigpy.config.CONF_STARTUP_ENERGY_SCAN: False,
}


@pytest.fixture
def ieee(init=0):
    return t.EUI64(map(t.uint8_t, range(init, init + 8)))


@pytest.fixture
def make_app(monkeypatch, ieee):
    def inner(config, send_timeout: float = 0.05, **kwargs):
        app_cfg = {**APP_CONFIG, **config}
        app = ControllerApplication(app_cfg)

        app._ezsp = _create_app_for_startup(
            app, nwk_type=t.EmberNodeType.COORDINATOR, ieee=ieee, **kwargs
        )
        monkeypatch.setattr(
            bellows.zigbee.application, "MESSAGE_SEND_TIMEOUT_MAINS", send_timeout
        )
        monkeypatch.setattr(
            bellows.zigbee.application, "MESSAGE_SEND_TIMEOUT_BATTERY", send_timeout
        )
        app._ctrl_event.set()
        app._in_flight_msg = asyncio.Semaphore()
        app.handle_message = MagicMock()
        app.packet_received = MagicMock()

        return app

    return inner


@pytest.fixture
def app(make_app):
    return make_app({})


@pytest.fixture
def aps():
    f = t.EmberApsFrame()
    f.profileId = 99
    f.sourceEndpoint = 8
    f.clusterId = 6
    f.destinationEndpoint = 8
    f.sequence = 100
    return f


def _create_app_for_startup(
    app,
    nwk_type,
    ieee,
    auto_form=False,
    init=bellows.types.sl_Status.OK,
    ezsp_version=8,
    board_info=True,
    network_state=t.EmberNetworkStatus.JOINED_NETWORK,
):
    nwk_params = bellows.types.struct.EmberNetworkParameters(
        extendedPanId=t.ExtendedPanId.convert("aa:bb:cc:dd:ee:ff:aa:bb"),
        panId=t.EmberPanId(0x55AA),
        radioTxPower=0,
        radioChannel=25,
        joinMethod=t.EmberJoinMethod.USE_MAC_ASSOCIATION,
        nwkManagerId=t.EmberNodeId(0x0000),
        nwkUpdateId=1,
        channels=t.Channels.ALL_CHANNELS,
    )

    app._in_flight_msg = None

    gateway = AsyncMock()
    ezsp_mock = ezsp.EZSP(device_config={})
    ezsp_mock._gw = gateway
    ezsp_mock._ezsp_version = ezsp_version
    ezsp_mock._protocol = ezsp.EZSP._BY_VERSION[ezsp_version](
        cb_handler=ezsp_mock.handle_callback,
        gateway=ezsp_mock._gw,
    )
    ezsp_mock.start_ezsp()

    ezsp_mock.connect = AsyncMock()
    ezsp_mock.disconnect = AsyncMock()
    ezsp_mock.startup_reset = AsyncMock()
    ezsp_mock.can_burn_userdata_custom_eui64 = AsyncMock(return_value=True)
    ezsp_mock.can_rewrite_custom_eui64 = AsyncMock(return_value=True)
    ezsp_mock.update_policies = AsyncMock()
    ezsp_mock.wait_for_stack_status = MagicMock()
    ezsp_mock.wait_for_stack_status.return_value.__enter__ = AsyncMock(
        return_value=t.EmberStatus.NETWORK_UP
    )
    ezsp_mock.customFrame = AsyncMock(
        return_value=[t.EmberStatus.LIBRARY_NOT_PRESENT, b""]
    )
    ezsp_mock.xncp_get_supported_firmware_features = AsyncMock(
        return_value=FirmwareFeatures.NONE
    )
    ezsp_mock._xncp_features = FirmwareFeatures.NONE

    if board_info:
        ezsp_mock.get_board_info = AsyncMock(
            return_value=("Mock Manufacturer", "Mock board", "Mock version")
        )
    else:
        ezsp_mock.get_board_info = AsyncMock(side_effect=EzspError("Not supported"))

    proto = ezsp_mock._protocol
    mock_ezsp_commands(proto)

    def form_network():
        proto.getNetworkParameters.return_value = [
            t.EmberStatus.SUCCESS,
            t.EmberNodeType.COORDINATOR,
            nwk_params,
        ]

    app.form_network = AsyncMock(side_effect=form_network)

    proto.initialize_network = AsyncMock(
        return_value=init, spec=proto.initialize_network
    )
    proto.write_nwk_frame_counter = AsyncMock(spec=proto.write_nwk_frame_counter)
    proto.write_aps_frame_counter = AsyncMock(spec=proto.write_aps_frame_counter)
    proto.send_broadcast = AsyncMock(
        spec=proto.send_broadcast, return_value=[t.sl_Status.OK, 0x12]
    )
    proto.write_link_keys = AsyncMock(spec=proto.write_link_keys)
    proto.write_child_data = AsyncMock(spec=proto.write_child_data)
    proto.add_transient_link_key = AsyncMock(
        return_value=t.sl_Status.OK, spec=proto.add_transient_link_key
    )

    proto.get_network_key = AsyncMock(
        return_value=zigpy.state.Key(
            key=t.KeyData(b"ActualNetworkKey"),
            tx_counter=t.uint32_t(0x12345678),
            rx_counter=t.uint32_t(0x00000000),
            seq=t.uint8_t(1),
            partner_ieee=t.EUI64.convert("ff:ff:ff:ff:ff:ff:ff:ff"),
        ),
        proto=proto.get_network_key,
    )

    proto.get_tc_link_key = AsyncMock(
        return_value=zigpy.state.Key(
            key=t.KeyData(b"thehashedlinkkey"),
            tx_counter=t.uint32_t(0x87654321),
            rx_counter=t.uint32_t(0x00000000),
            seq=t.uint8_t(0),
            partner_ieee=t.EUI64.convert("ff:ff:ff:ff:ff:ff:ff:ff"),
        ),
        proto=proto.get_tc_link_key,
    )

    proto.factory_reset = AsyncMock(proto=proto.factory_reset)
    proto.set_extended_timeout = AsyncMock(proto=proto.set_extended_timeout)

    proto.read_link_keys = MagicMock()
    proto.read_link_keys.return_value.__aiter__.return_value = [
        zigpy.state.Key(
            key=t.KeyData(b"test_link_key_01"),
            tx_counter=12345,
            rx_counter=67890,
            seq=1,
            partner_ieee=t.EUI64.convert("aa:bb:cc:dd:ee:ff:00:11"),
        ),
        zigpy.state.Key(
            key=t.KeyData(b"test_link_key_02"),
            tx_counter=54321,
            rx_counter=98765,
            seq=2,
            partner_ieee=t.EUI64.convert("11:22:33:44:55:66:77:88"),
        ),
    ]

    proto.read_child_data = MagicMock()
    proto.read_child_data.return_value.__aiter__.return_value = [
        (
            0x1234,
            t.EUI64.convert("aa:bb:cc:dd:ee:ff:00:11"),
            t.EmberNodeType.END_DEVICE,
        ),
        (
            0x5678,
            t.EUI64.convert("11:22:33:44:55:66:77:88"),
            t.EmberNodeType.END_DEVICE,
        ),
    ]

    proto.read_address_table = MagicMock()
    proto.read_address_table.return_value.__aiter__.return_value = [
        (0xABCD, t.EUI64.convert("ab:cd:00:11:22:33:44:55")),
        (0xDCBA, t.EUI64.convert("dc:ba:00:11:22:33:44:55")),
    ]

    if "getTokenData" in proto.COMMANDS:
        proto.getTokenData.return_value = GetTokenDataRsp(
            status=t.EmberStatus.ERR_FATAL
        )

    proto.addEndpoint.return_value = [t.EmberStatus.SUCCESS]
    proto.setManufacturerCode.return_value = [t.EmberStatus.SUCCESS]
    proto.setConfigurationValue.return_value = [t.EmberStatus.SUCCESS]
    proto.getNetworkParameters.return_value = [
        t.EmberStatus.SUCCESS,
        nwk_type,
        nwk_params,
    ]
    proto.startScan.return_value = [[c, 1] for c in range(11, 26 + 1)]
    proto.setPolicy.return_value = [t.EmberStatus.SUCCESS]
    proto.getMfgToken.return_value = (b"Some token\xff",)
    proto.getNodeId.return_value = [t.EmberNodeId(0x0000)]
    proto.getEui64.return_value = [ieee]
    proto.getValue.return_value = (0, b"\x01" * 6)
    proto.setValue.return_value = (t.EmberStatus.SUCCESS,)
    proto.readCounters.return_value = ([0x0000] * len(t.EmberCounterType),)

    async def mock_leave(*args, **kwargs):
        app._ezsp.handle_callback("stackStatusHandler", [t.EmberStatus.NETWORK_DOWN])
        return [t.EmberStatus.SUCCESS]

    proto.leaveNetwork.side_effect = mock_leave
    proto.getConfigurationValue.return_value = [t.EmberStatus.SUCCESS, 1]
    proto.networkState.return_value = [network_state]
    proto.setInitialSecurityState.return_value = [t.EmberStatus.SUCCESS]
    proto.formNetwork.return_value = [t.EmberStatus.SUCCESS]
    proto.getCurrentSecurityState.return_value = (
        t.EmberStatus.SUCCESS,
        t.EmberCurrentSecurityState(
            bitmask=(
                t.EmberCurrentSecurityBitmask.GLOBAL_LINK_KEY
                | t.EmberCurrentSecurityBitmask.HAVE_TRUST_CENTER_LINK_KEY
                | 224
            ),
            trustCenterLongAddress=ieee,
        ),
    )
    proto.getMulticastTableEntry.return_value = (
        t.EmberStatus.SUCCESS,
        t.EmberMulticastTableEntry(multicastId=0x0000, endpoint=0, networkIndex=0),
    )
    proto.setMulticastTableEntry.return_value = [t.EmberStatus.SUCCESS]
    proto.setConcentrator.return_value = [t.EmberStatus.SUCCESS]

    if ezsp_version >= 8:
        proto.setSourceRouteDiscoveryMode.return_value = [12345]

    return ezsp_mock


@contextlib.contextmanager
def mock_for_startup(
    app,
    ieee,
    nwk_type=t.EmberNodeType.COORDINATOR,
    auto_form=False,
    init=0,
    ezsp_version=4,
    board_info=True,
    network_state=t.EmberNetworkStatus.JOINED_NETWORK,
):
    ezsp_mock = _create_app_for_startup(
        app, nwk_type, ieee, auto_form, init, ezsp_version, board_info, network_state
    )

    with patch("bellows.ezsp.EZSP", return_value=ezsp_mock), patch(
        "zigpy.device.Device._initialize", new=AsyncMock()
    ):
        yield ezsp_mock


async def _test_startup(
    app,
    nwk_type,
    ieee,
    auto_form=False,
    init=0,
    ezsp_version=4,
    board_info=True,
    network_state=t.EmberNetworkStatus.JOINED_NETWORK,
):
    with mock_for_startup(
        app, ieee, nwk_type, auto_form, init, ezsp_version, board_info, network_state
    ) as ezsp_mock:
        await app.startup(auto_form=auto_form)

    assert ezsp_mock._protocol.addEndpoint.call_count >= 2


async def test_startup(app, ieee):
    await _test_startup(app, t.EmberNodeType.COORDINATOR, ieee)


async def test_startup_ezsp_ver7(app, ieee):
    app.state.counters["ezsp_counters"] = MagicMock()
    await _test_startup(app, t.EmberNodeType.COORDINATOR, ieee, ezsp_version=7)
    assert app.state.counters["ezsp_counters"].reset.call_count == 1


async def test_startup_ezsp_ver8(app, ieee):
    app.state.counters["ezsp_counters"] = MagicMock()
    ieee_1 = t.EUI64.convert("11:22:33:44:55:66:77:88")
    dev_1 = app.add_device(ieee_1, 0x1234)
    dev_1.relays = [
        t.EmberNodeId(0x2222),
    ]

    await _test_startup(app, t.EmberNodeType.COORDINATOR, ieee, ezsp_version=8)
    assert app.state.counters["ezsp_counters"].reset.call_count == 1


async def test_startup_no_status(app, ieee):
    """Test when NCP is not a coordinator and not auto forming."""
    with pytest.raises(zigpy.exceptions.NetworkNotFormed):
        await _test_startup(
            app, t.EmberNodeType.UNKNOWN_DEVICE, ieee, auto_form=False, init=1
        )


async def test_startup_status_not_joined(app, ieee):
    """Test when NCP is a coordinator but isn't a part of a network."""
    with pytest.raises(zigpy.exceptions.NetworkNotFormed):
        await _test_startup(
            app,
            t.EmberNodeType.COORDINATOR,
            ieee,
            auto_form=False,
            init=bellows.types.sl_Status.NOT_JOINED,
            network_state=t.EmberNetworkStatus.NO_NETWORK,
        )


async def test_startup_status_unknown(app, ieee):
    """Test when NCP is a coordinator but stack init fails."""
    with pytest.raises(zigpy.exceptions.ControllerException):
        await _test_startup(
            app,
            t.EmberNodeType.COORDINATOR,
            ieee,
            auto_form=False,
            init=bellows.types.sl_Status.FAIL,
            network_state=t.EmberNetworkStatus.NO_NETWORK,
        )


async def test_startup_no_status_form(app, ieee):
    """Test when NCP is not a coordinator but allow auto forming."""
    await _test_startup(
        app, t.EmberNodeType.UNKNOWN_NODE_TYPE, ieee, auto_form=True, init=1
    )


async def test_startup_end(app, ieee):
    """Test when NCP is a End Device and not auto forming."""
    with pytest.raises(zigpy.exceptions.NetworkNotFormed):
        await _test_startup(
            app, t.EmberNodeType.SLEEPY_END_DEVICE, ieee, auto_form=False
        )


async def test_startup_end_form(app, ieee):
    """Test when NCP is a End Device but allow auto forming."""
    await _test_startup(app, t.EmberNodeType.SLEEPY_END_DEVICE, ieee, auto_form=True)


async def test_startup_no_board_info(app, ieee, caplog):
    """Test when NCP does not support `get_board_info`."""
    with caplog.at_level(logging.INFO):
        await _test_startup(app, t.EmberNodeType.COORDINATOR, ieee, board_info=False)

    assert "EZSP Radio does not support getMfgToken command" in caplog.text


@pytest.fixture
def aps_frame():
    return t.EmberApsFrame(
        profileId=0x1234,
        clusterId=0x5678,
        sourceEndpoint=0x9A,
        destinationEndpoint=0xBC,
        options=t.EmberApsOption.APS_OPTION_NONE,
        groupId=0x0000,
        sequence=0xDE,
    )


def _handle_incoming_aps_frame(app, aps_frame, type):
    app.ezsp_callback_handler(
        "incomingMessageHandler",
        list(
            dict(
                type=type,
                apsFrame=aps_frame,
                lastHopLqi=123,
                lastHopRssi=-45,
                sender=0xABCD,
                bindingIndex=56,
                addressIndex=78,
                message=b"test message",
            ).values()
        ),
    )


def test_frame_handler_unicast(app, aps_frame):
    _handle_incoming_aps_frame(
        app, aps_frame, type=t.EmberIncomingMessageType.INCOMING_UNICAST
    )
    assert app.packet_received.call_count == 1

    packet = app.packet_received.mock_calls[0].args[0]
    assert packet.profile_id == 0x1234
    assert packet.cluster_id == 0x5678
    assert packet.src_ep == 0x9A
    assert packet.dst_ep == 0xBC
    assert packet.tsn == 0xDE
    assert packet.src.addr_mode == zigpy_t.AddrMode.NWK
    assert packet.src.address == 0xABCD
    assert packet.dst.addr_mode == zigpy_t.AddrMode.NWK
    assert packet.dst.address == app.state.node_info.nwk
    assert packet.data.serialize() == b"test message"
    assert packet.lqi == 123
    assert packet.rssi == -45

    assert (
        app.state.counters[bellows.zigbee.application.COUNTERS_CTRL][
            bellows.zigbee.application.COUNTER_RX_UNICAST
        ]
        == 1
    )


def test_frame_handler_broadcast(app, aps_frame):
    _handle_incoming_aps_frame(
        app, aps_frame, type=t.EmberIncomingMessageType.INCOMING_BROADCAST
    )
    assert app.packet_received.call_count == 1

    packet = app.packet_received.mock_calls[0].args[0]
    assert packet.profile_id == 0x1234
    assert packet.cluster_id == 0x5678
    assert packet.src_ep == 0x9A
    assert packet.dst_ep == 0xBC
    assert packet.tsn == 0xDE
    assert packet.src.addr_mode == zigpy_t.AddrMode.NWK
    assert packet.src.address == 0xABCD
    assert packet.dst.addr_mode == zigpy_t.AddrMode.Broadcast
    assert packet.dst.address == zigpy_t.BroadcastAddress.ALL_ROUTERS_AND_COORDINATOR
    assert packet.data.serialize() == b"test message"
    assert packet.lqi == 123
    assert packet.rssi == -45

    assert (
        app.state.counters[bellows.zigbee.application.COUNTERS_CTRL][
            bellows.zigbee.application.COUNTER_RX_BCAST
        ]
        == 1
    )


def test_frame_handler_multicast(app, aps_frame):
    aps_frame.groupId = 0xEF12
    _handle_incoming_aps_frame(
        app, aps_frame, type=t.EmberIncomingMessageType.INCOMING_MULTICAST
    )

    assert app.packet_received.call_count == 1

    packet = app.packet_received.mock_calls[0].args[0]
    assert packet.profile_id == 0x1234
    assert packet.cluster_id == 0x5678
    assert packet.src_ep == 0x9A
    assert packet.dst_ep == 0xBC
    assert packet.tsn == 0xDE
    assert packet.src.addr_mode == zigpy_t.AddrMode.NWK
    assert packet.src.address == 0xABCD
    assert packet.dst.addr_mode == zigpy_t.AddrMode.Group
    assert packet.dst.address == 0xEF12
    assert packet.data.serialize() == b"test message"
    assert packet.lqi == 123
    assert packet.rssi == -45

    assert (
        app.state.counters[bellows.zigbee.application.COUNTERS_CTRL][
            bellows.zigbee.application.COUNTER_RX_MCAST
        ]
        == 1
    )


def test_frame_handler_ignored(app, aps_frame):
    _handle_incoming_aps_frame(
        app, aps_frame, type=t.EmberIncomingMessageType.INCOMING_BROADCAST_LOOPBACK
    )
    assert app.packet_received.call_count == 0


@pytest.mark.parametrize(
    "msg_type",
    (
        t.EmberIncomingMessageType.INCOMING_BROADCAST,
        t.EmberIncomingMessageType.INCOMING_MULTICAST,
        t.EmberIncomingMessageType.INCOMING_UNICAST,
        0xFF,
    ),
)
def test_send_failure(app, aps, ieee, msg_type):
    fut = app._pending_requests[(0xBEED, 254)] = asyncio.Future()
    app.ezsp_callback_handler(
        "messageSentHandler", [msg_type, 0xBEED, aps, 254, t.EmberStatus.SUCCESS, b""]
    )
    assert fut.result() == (t.sl_Status.OK, "message send success")


async def test_dup_send_failure(app, aps, ieee):
    fut = app._pending_requests[(0xBEED, 254)] = asyncio.Future()
    fut.set_result("Already set")

    app.ezsp_callback_handler(
        "messageSentHandler",
        [
            t.EmberIncomingMessageType.INCOMING_UNICAST,
            0xBEED,
            aps,
            254,
            sentinel.status,
            b"",
        ],
    )


def test_send_failure_unexpected(app, aps, ieee):
    app.ezsp_callback_handler(
        "messageSentHandler",
        [
            t.EmberIncomingMessageType.INCOMING_BROADCAST_LOOPBACK,
            0xBEED,
            aps,
            257,
            1,
            b"",
        ],
    )


def test_send_success(app, aps, ieee):
    fut = app._pending_requests[(0xBEED, 253)] = asyncio.Future()
    app.ezsp_callback_handler(
        "messageSentHandler",
        [
            t.EmberIncomingMessageType.INCOMING_MULTICAST_LOOPBACK,
            0xBEED,
            aps,
            253,
            t.EmberStatus.SUCCESS,
            b"",
        ],
    )

    assert fut.result() == (t.sl_Status.OK, "message send success")


def test_unexpected_send_success(app, aps, ieee):
    app.ezsp_callback_handler(
        "messageSentHandler",
        [t.EmberIncomingMessageType.INCOMING_MULTICAST, 0xBEED, aps, 253, 0, b""],
    )


async def test_join_handler(app, ieee):
    # Calls device.initialize, leaks a task
    app.handle_join = MagicMock()
    app.cleanup_tc_link_key = AsyncMock()
    app.ezsp_callback_handler(
        "trustCenterJoinHandler",
        [
            1,
            ieee,
            t.EmberDeviceUpdate.STANDARD_SECURITY_UNSECURED_JOIN,
            t.EmberJoinDecision.NO_ACTION,
            sentinel.parent,
        ],
    )
    await asyncio.sleep(0)
    assert ieee not in app.devices
    assert app.handle_join.call_count == 1
    assert app.handle_join.call_args[0][0] == 1
    assert app.handle_join.call_args[0][1] == ieee
    assert app.handle_join.call_args[0][2] is sentinel.parent
    assert app.cleanup_tc_link_key.await_count == 1
    assert app.cleanup_tc_link_key.call_args[0][0] is ieee

    # cleanup TCLK, but no join handling
    app.handle_join.reset_mock()
    app.cleanup_tc_link_key.reset_mock()
    app.ezsp_callback_handler(
        "trustCenterJoinHandler",
        [
            1,
            ieee,
            t.EmberDeviceUpdate.STANDARD_SECURITY_UNSECURED_JOIN,
            t.EmberJoinDecision.DENY_JOIN,
            sentinel.parent,
        ],
    )
    await asyncio.sleep(0)
    assert app.cleanup_tc_link_key.await_count == 1
    assert app.cleanup_tc_link_key.call_args[0][0] is ieee
    assert app.handle_join.call_count == 0


def test_leave_handler(app, ieee):
    app.handle_join = MagicMock()
    app.devices[ieee] = MagicMock()
    app.ezsp_callback_handler(
        "trustCenterJoinHandler", [1, ieee, t.EmberDeviceUpdate.DEVICE_LEFT, None, None]
    )
    assert ieee in app.devices
    assert app.handle_join.call_count == 0


async def test_force_remove(app, ieee):
    app._ezsp._protocol.removeDevice.return_value = [t.EmberStatus.SUCCESS]
    dev = MagicMock()
    await app.force_remove(dev)


def test_sequence(app):
    for i in range(1000):
        seq = app.get_sequence()
        assert seq >= 0
        assert seq < 256


async def test_permit_ncp(app):
    app._ezsp._protocol.permitJoining.return_value = [t.EmberStatus.SUCCESS]
    await app.permit_ncp(60)
    assert app._ezsp._protocol.permitJoining.mock_calls == [call(60)]


async def test_permit_with_link_key(app, ieee):
    with patch("zigpy.application.ControllerApplication.permit") as permit_mock:
        await app.permit_with_link_key(
            ieee,
            zigpy_t.KeyData.convert("11:22:33:44:55:66:77:88:11:22:33:44:55:66:77:88"),
            60,
        )

    assert permit_mock.await_count == 1
    assert app._ezsp._protocol.add_transient_link_key.mock_calls == [
        call(
            ieee,
            zigpy_t.KeyData.convert("11:22:33:44:55:66:77:88:11:22:33:44:55:66:77:88"),
        )
    ]


async def test_permit_with_link_key_failure(app, ieee):
    app._ezsp._protocol.add_transient_link_key.return_value = t.EmberStatus.ERR_FATAL

    with patch("zigpy.application.ControllerApplication.permit") as permit_mock:
        with pytest.raises(ControllerError):
            await app.permit_with_link_key(
                ieee,
                zigpy_t.KeyData.convert(
                    "11:22:33:44:55:66:77:88:11:22:33:44:55:66:77:88"
                ),
                60,
            )

    assert permit_mock.await_count == 0
    assert app._ezsp._protocol.add_transient_link_key.await_count == 1


@pytest.fixture
def packet():
    return zigpy_t.ZigbeePacket(
        src=zigpy_t.AddrModeAddress(addr_mode=zigpy_t.AddrMode.NWK, address=0x0000),
        src_ep=0x12,
        dst=zigpy_t.AddrModeAddress(addr_mode=zigpy_t.AddrMode.NWK, address=0x1234),
        dst_ep=0x34,
        tsn=0x56,
        profile_id=0x7890,
        cluster_id=0xABCD,
        data=zigpy_t.SerializableBytes(b"some data"),
        tx_options=zigpy_t.TransmitOptions.ACK,
        radius=0,
    )


async def test_request_concurrency_duplicate_failure(
    make_app, packet: zigpy_t.ZigbeePacket
) -> None:
    def send_unicast(aps_frame, data, message_tag, nwk):
        asyncio.get_running_loop().call_soon(
            app.ezsp_callback_handler,
            "messageSentHandler",
            list(
                dict(
                    type=t.EmberOutgoingMessageType.OUTGOING_DIRECT,
                    indexOrDestination=0x1234,
                    apsFrame=aps_frame,
                    messageTag=message_tag,
                    status=bellows.types.sl_Status.OK,
                    message=b"",
                ).values()
            ),
        )

        return [bellows.types.sl_Status.OK, 0x12]

    # Increase the send timeout, CI is inconsistent with the default
    app = make_app({}, send_timeout=0.5)
    app._ezsp.send_unicast = AsyncMock(
        side_effect=send_unicast, spec=app._ezsp.send_unicast
    )

    await app.send_packet(packet)
    app._concurrent_requests_semaphore.max_value = 10000
    results = await asyncio.gather(
        *(app.send_packet(packet) for _ in range(256 + 1)), return_exceptions=True
    )

    # The first 256 will work just fine
    assert results[:256] == [None] * 256

    # The 257th will fail, since the tag will wrap around back to 0
    assert isinstance(results[256], zigpy.exceptions.DeliveryError)
    assert "Packet with tag (0x1234, 2) is already pending, cannot send" in str(
        results[256]
    )


async def _test_send_packet_unicast(
    app,
    packet,
    *,
    status=bellows.types.sl_Status.OK,
    sent_handler_status=bellows.types.sl_Status.OK,
    options=(
        t.EmberApsOption.APS_OPTION_ENABLE_ROUTE_DISCOVERY
        | t.EmberApsOption.APS_OPTION_RETRY
    ),
):
    def send_unicast(*args, **kwargs):
        asyncio.get_running_loop().call_later(
            0.01,
            app.ezsp_callback_handler,
            "messageSentHandler",
            list(
                dict(
                    type=t.EmberOutgoingMessageType.OUTGOING_DIRECT,
                    indexOrDestination=0x1234,
                    apsFrame=sentinel.aps,
                    messageTag=sentinel.msg_tag,
                    status=sent_handler_status,
                    message=b"",
                ).values()
            ),
        )

        return [status, 0x12]

    app._ezsp.send_unicast = AsyncMock(
        side_effect=send_unicast, spec=app._ezsp.send_unicast
    )
    app.get_sequence = MagicMock(return_value=sentinel.msg_tag)

    await app.send_packet(packet)

    assert app._ezsp.send_unicast.mock_calls == [
        call(
            nwk=t.EmberNodeId(0x1234),
            aps_frame=t.EmberApsFrame(
                profileId=packet.profile_id,
                clusterId=packet.cluster_id,
                sourceEndpoint=packet.src_ep,
                destinationEndpoint=packet.dst_ep,
                options=options,
                groupId=0x0000,
                sequence=packet.tsn,
            ),
            message_tag=sentinel.msg_tag,
            data=b"some data",
        )
    ]

    assert len(app._pending_requests) == 0


async def test_send_packet_unicast(app, packet):
    await _test_send_packet_unicast(app, packet)


async def test_send_packet_unicast_not_running(app, packet):
    app.controller_event.clear()

    with pytest.raises(ControllerError):
        await _test_send_packet_unicast(app, packet)


async def test_send_packet_unicast_ieee_fallback(app, packet, caplog):
    ieee = zigpy_t.EUI64.convert("aa:bb:cc:dd:11:22:33:44")
    packet.dst = zigpy_t.AddrModeAddress(addr_mode=zigpy_t.AddrMode.IEEE, address=ieee)
    app.add_device(nwk=0x1234, ieee=ieee)

    with caplog.at_level(logging.WARNING):
        await _test_send_packet_unicast(app, packet)

    assert "IEEE addressing is not supported" in caplog.text


async def test_send_packet_unicast_ieee_no_fallback(app, packet, caplog):
    ieee = zigpy_t.EUI64.convert("aa:bb:cc:dd:11:22:33:44")
    packet.dst = zigpy_t.AddrModeAddress(addr_mode=zigpy_t.AddrMode.IEEE, address=ieee)

    with pytest.raises(ValueError):
        await _test_send_packet_unicast(app, packet)

    assert app._ezsp.send_unicast.call_count == 0


async def test_send_packet_unicast_source_route(make_app, packet):
    app = make_app({zigpy.config.CONF_SOURCE_ROUTING: True})
    app._ezsp._protocol.set_source_route = AsyncMock(
        return_value=t.sl_Status.OK, spec=app._ezsp._protocol.set_source_route
    )

    packet.source_route = [0x0001, 0x0002]
    await _test_send_packet_unicast(
        app,
        packet,
        options=(
            t.EmberApsOption.APS_OPTION_RETRY
            | t.EmberApsOption.APS_OPTION_ENABLE_ADDRESS_DISCOVERY
        ),
    )

    app._ezsp._protocol.set_source_route.assert_called_once_with(
        nwk=packet.dst.address,
        relays=[0x0001, 0x0002],
    )


async def test_send_packet_unicast_manual_source_route(make_app, packet):
    app = make_app(
        {
            zigpy.config.CONF_SOURCE_ROUTING: True,
            config.CONF_BELLOWS_CONFIG: {config.CONF_MANUAL_SOURCE_ROUTING: True},
        }
    )

    app._ezsp._xncp_features |= FirmwareFeatures.MANUAL_SOURCE_ROUTE

    app._ezsp.xncp_set_manual_source_route = AsyncMock(
        return_value=None, spec=app._ezsp._protocol.set_source_route
    )

    packet.source_route = [0x0001, 0x0002]
    await _test_send_packet_unicast(
        app,
        packet,
        options=(
            t.EmberApsOption.APS_OPTION_RETRY
            | t.EmberApsOption.APS_OPTION_ENABLE_ADDRESS_DISCOVERY
        ),
    )

    app._ezsp.xncp_set_manual_source_route.assert_called_once_with(
        nwk=packet.dst.address,
        relays=[0x0001, 0x0002],
    )


async def test_send_packet_unicast_extended_timeout_with_acks(app, ieee, packet):
    app.add_device(nwk=packet.dst.address, ieee=ieee)

    asyncio.get_running_loop().call_later(
        0.1,
        app.ezsp_callback_handler,
        "incomingRouteRecordHandler",
        {
            "source": packet.dst.address,
            "sourceEui": ieee,
            "lastHopLqi": 123,
            "lastHopRssi": -60,
            "relayList": [0x1234],
        }.values(),
    )

    await _test_send_packet_unicast(
        app,
        packet.replace(
            extended_timeout=True,
            tx_options=zigpy.types.TransmitOptions.ACK,
        ),
    )

    # With APS ACK, we do not use extended timeouts
    assert app._ezsp._protocol.set_extended_timeout.mock_calls == [
        call(nwk=packet.dst.address, ieee=ieee, extended_timeout=False)
    ]


async def test_send_packet_unicast_extended_timeout_without_acks(app, ieee, packet):
    app.add_device(nwk=packet.dst.address, ieee=ieee)

    asyncio.get_running_loop().call_later(
        0.1,
        app.ezsp_callback_handler,
        "incomingRouteRecordHandler",
        {
            "source": packet.dst.address,
            "sourceEui": ieee,
            "lastHopLqi": 123,
            "lastHopRssi": -60,
            "relayList": [0x1234],
        }.values(),
    )

    await _test_send_packet_unicast(
        app,
        packet.replace(
            extended_timeout=True,
            tx_options=zigpy.types.TransmitOptions.NONE,
        ),
        options=t.EmberApsOption.APS_OPTION_ENABLE_ROUTE_DISCOVERY,
    )

    # Without APS ACKs, we can
    assert app._ezsp._protocol.set_extended_timeout.mock_calls == [
        call(nwk=packet.dst.address, ieee=ieee, extended_timeout=True)
    ]


async def test_send_packet_unicast_force_route_discovery(app, packet):
    await _test_send_packet_unicast(
        app,
        packet.replace(tx_options=zigpy.types.TransmitOptions.FORCE_ROUTE_DISCOVERY),
        options=(
            t.EmberApsOption.APS_OPTION_RETRY
            | t.EmberApsOption.APS_OPTION_FORCE_ROUTE_DISCOVERY
        ),
    )


async def test_send_packet_unicast_unexpected_failure(app, packet):
    with pytest.raises(zigpy.exceptions.DeliveryError):
        await _test_send_packet_unicast(app, packet, status=t.EmberStatus.ERR_FATAL)


async def test_send_packet_unicast_retries_failure(app, packet):
    with pytest.raises(zigpy.exceptions.DeliveryError):
        await _test_send_packet_unicast(
            app, packet, status=bellows.types.sl_Status.ALLOCATION_FAILED
        )


async def test_send_packet_unicast_delivery_failure_sent_handler(
    app: ControllerApplication, packet
) -> None:
    with pytest.raises(zigpy.exceptions.DeliveryError):
        await _test_send_packet_unicast(
            app,
            packet,
            status=t.EmberStatus.SUCCESS,
            sent_handler_status=t.EmberStatus.DELIVERY_FAILED,
        )


async def test_send_packet_unicast_routing_error(
    app: ControllerApplication, packet
) -> None:
    with pytest.raises(zigpy.exceptions.DeliveryError):
        await _test_send_packet_unicast(
            app,
            packet,
            status=t.EmberStatus.SUCCESS,
            sent_handler_status=t.EmberStatus.DELIVERY_FAILED,
        )


async def test_send_packet_unicast_concurrency(app, packet, monkeypatch):
    monkeypatch.setattr(bellows.zigbee.application, "MESSAGE_SEND_TIMEOUT_MAINS", 0.5)
    monkeypatch.setattr(bellows.zigbee.application, "MESSAGE_SEND_TIMEOUT_BATTERY", 0.5)

    app._concurrent_requests_semaphore.max_value = 10

    max_concurrency = 0
    in_flight_requests = 0

    async def send_message_sent_reply(
        type, indexOrDestination, apsFrame, messageTag, message
    ):
        nonlocal max_concurrency, in_flight_requests

        max_concurrency = max(max_concurrency, in_flight_requests)
        in_flight_requests -= 1

        await asyncio.sleep(0.01)

        app.ezsp_callback_handler(
            "messageSentHandler",
            list(
                dict(
                    type=type,
                    indexOrDestination=indexOrDestination,
                    apsFrame=apsFrame,
                    messageTag=messageTag,
                    status=t.EmberStatus.SUCCESS,
                    message=b"",
                ).values()
            ),
        )

    async def send_unicast(nwk, aps_frame, message_tag, data):
        nonlocal max_concurrency, in_flight_requests

        in_flight_requests += 1
        max_concurrency = max(max_concurrency, in_flight_requests)

        asyncio.create_task(
            send_message_sent_reply(
                t.EmberOutgoingMessageType.OUTGOING_DIRECT,
                nwk,
                aps_frame,
                message_tag,
                data,
            )
        )

        return [bellows.types.sl_Status.OK, 0x12]

    app._ezsp.send_unicast = AsyncMock(side_effect=send_unicast)

    responses = await asyncio.gather(*[app.send_packet(packet) for _ in range(100)])
    assert len(responses) == 100
    assert max_concurrency == 10
    assert in_flight_requests == 0


async def test_send_packet_broadcast(app, packet):
    packet.dst = zigpy_t.AddrModeAddress(
        addr_mode=zigpy_t.AddrMode.Broadcast, address=0xFFFE
    )
    packet.radius = 30

    app._ezsp.send_broadcast = AsyncMock(
        return_value=(bellows.types.named.sl_Status.OK, 0x12)
    )
    app.get_sequence = MagicMock(return_value=sentinel.msg_tag)

    asyncio.get_running_loop().call_soon(
        app.ezsp_callback_handler,
        "messageSentHandler",
        list(
            dict(
                type=t.EmberOutgoingMessageType.OUTGOING_BROADCAST,
                indexOrDestination=0xFFFE,
                apsFrame=sentinel.aps,
                messageTag=sentinel.msg_tag,
                status=t.EmberStatus.SUCCESS,
                message=b"",
            ).values()
        ),
    )

    await app.send_packet(packet)
    assert app._ezsp.send_broadcast.mock_calls == [
        call(
            address=bellows.types.named.BroadcastAddress(0xFFFE),
            aps_frame=t.EmberApsFrame(
                profileId=packet.profile_id,
                clusterId=packet.cluster_id,
                sourceEndpoint=packet.src_ep,
                destinationEndpoint=packet.dst_ep,
                options=t.EmberApsOption.APS_OPTION_ENABLE_ROUTE_DISCOVERY,
                groupId=0x0000,
                sequence=packet.tsn,
            ),
            radius=packet.radius,
            message_tag=sentinel.msg_tag,
            aps_sequence=packet.tsn,
            data=b"some data",
        )
    ]

    assert len(app._pending_requests) == 0


async def test_send_packet_broadcast_ignored_delivery_failure(app, packet):
    packet.dst = zigpy_t.AddrModeAddress(
        addr_mode=zigpy_t.AddrMode.Broadcast, address=0xFFFE
    )
    packet.radius = 30

    app.get_sequence = MagicMock(return_value=sentinel.msg_tag)

    asyncio.get_running_loop().call_soon(
        app.ezsp_callback_handler,
        "messageSentHandler",
        list(
            dict(
                type=t.EmberOutgoingMessageType.OUTGOING_BROADCAST,
                indexOrDestination=0xFFFE,
                apsFrame=sentinel.aps,
                messageTag=sentinel.msg_tag,
                status=t.EmberStatus.DELIVERY_FAILED,
                message=b"",
            ).values()
        ),
    )

    # Does not throw an error
    await app.send_packet(packet)

    assert app._ezsp.send_broadcast.mock_calls == [
        call(
            address=bellows.types.named.BroadcastAddress(0xFFFE),
            aps_frame=t.EmberApsFrame(
                profileId=packet.profile_id,
                clusterId=packet.cluster_id,
                sourceEndpoint=packet.src_ep,
                destinationEndpoint=packet.dst_ep,
                options=t.EmberApsOption.APS_OPTION_ENABLE_ROUTE_DISCOVERY,
                groupId=0x0000,
                sequence=packet.tsn,
            ),
            radius=packet.radius,
            message_tag=sentinel.msg_tag,
            aps_sequence=packet.tsn,
            data=b"some data",
        )
    ]

    assert len(app._pending_requests) == 0


async def test_send_packet_multicast(app, packet):
    packet.dst = zigpy_t.AddrModeAddress(
        addr_mode=zigpy_t.AddrMode.Group, address=0x1234
    )
    packet.radius = 5
    packet.non_member_radius = 6

    app._ezsp._protocol.send_multicast = AsyncMock(
        return_value=(bellows.types.sl_Status.OK, 0x12),
        spec=app._ezsp._protocol.send_multicast,
    )
    app.get_sequence = MagicMock(return_value=sentinel.msg_tag)

    asyncio.get_running_loop().call_soon(
        app.ezsp_callback_handler,
        "messageSentHandler",
        list(
            dict(
                type=t.EmberOutgoingMessageType.OUTGOING_MULTICAST,
                indexOrDestination=0x1234,
                apsFrame=sentinel.aps,
                messageTag=sentinel.msg_tag,
                status=t.EmberStatus.SUCCESS,
                message=b"",
            ).values()
        ),
    )

    await app.send_packet(packet)
    assert app._ezsp.send_multicast.mock_calls == [
        call(
            aps_frame=t.EmberApsFrame(
                profileId=packet.profile_id,
                clusterId=packet.cluster_id,
                sourceEndpoint=packet.src_ep,
                destinationEndpoint=packet.dst_ep,
                options=t.EmberApsOption.APS_OPTION_ENABLE_ROUTE_DISCOVERY,
                groupId=0x1234,
                sequence=packet.tsn,
            ),
            radius=packet.radius,
            non_member_radius=packet.non_member_radius,
            message_tag=sentinel.msg_tag,
            data=b"some data",
        )
    ]

    assert len(app._pending_requests) == 0


def test_is_controller_running(app):
    ezsp_running = PropertyMock(return_value=False)
    with patch.object(type(app._ezsp), "is_ezsp_running", ezsp_running):
        app._ctrl_event.clear()
        assert app.is_controller_running is False
        app._ctrl_event.set()
        assert app.is_controller_running is False
        assert ezsp_running.call_count == 1

    ezsp_running = PropertyMock(return_value=True)
    with patch.object(type(app._ezsp), "is_ezsp_running", ezsp_running):
        app._ctrl_event.clear()
        assert app.is_controller_running is False
        app._ctrl_event.set()
        assert app.is_controller_running is True
        assert ezsp_running.call_count == 1


@pytest.mark.parametrize("ezsp_version", (4, 7))
async def test_watchdog(make_app, monkeypatch, ezsp_version):
    from bellows.zigbee import application

    app = make_app({}, ezsp_version=ezsp_version)

    monkeypatch.setattr(application.ControllerApplication, "_watchdog_period", 0.01)
    monkeypatch.setattr(application, "EZSP_COUNTERS_CLEAR_IN_WATCHDOG_PERIODS", 2)
    nop_success = 7

    async def nop_mock():
        nonlocal nop_success
        if nop_success:
            nop_success -= 1
            if nop_success % 3:
                raise EzspError
            else:
                return ([0] * 10,)
        raise asyncio.TimeoutError

    app._ezsp._protocol.getValue.return_value = [t.EmberStatus.SUCCESS, b"\xFE"]
    app._ezsp._protocol.nop.side_effect = nop_mock
    app._ezsp._protocol.readCounters.side_effect = nop_mock
    app._ezsp._protocol.readAndClearCounters.side_effect = nop_mock
    app._ctrl_event.set()
    app.connection_lost = MagicMock()

    for i in range(nop_success):
        await app._watchdog_feed()

    # Fail four times in a row to exhaust the watchdog buffer
    await app._watchdog_feed()
    await app._watchdog_feed()
    await app._watchdog_feed()
    await app._watchdog_feed()

    # The last time will throw a real error
    with pytest.raises(asyncio.TimeoutError):
        await app._watchdog_feed()

    if ezsp_version == 4:
        assert app._ezsp._protocol.nop.await_count > 4
    else:
        assert app._ezsp._protocol.readCounters.await_count >= 4


async def test_watchdog_counters(app, monkeypatch, caplog):
    from bellows.zigbee import application

    monkeypatch.setattr(application.ControllerApplication, "_watchdog_period", 0.01)
    nop_success = 3

    async def counters_mock():
        nonlocal nop_success
        if nop_success:
            nop_success -= 1
            if nop_success % 2:
                raise EzspError
            else:
                return ([0, 1, 2, 3],)
        raise asyncio.TimeoutError

    app._ezsp._protocol.getValue = AsyncMock(
        return_value=[t.EmberStatus.SUCCESS, b"\xFE"]
    )
    app._ezsp._protocol.readCounters = AsyncMock(side_effect=counters_mock)
    app._ezsp._protocol.nop = AsyncMock(side_effect=EzspError)
    app._handle_reset_request = MagicMock()
    app._ctrl_event.set()

    caplog.set_level(logging.DEBUG, "bellows.zigbee.application")
    await app._watchdog_feed()
    assert app._ezsp._protocol.readCounters.await_count != 0
    assert app._ezsp._protocol.nop.await_count == 0

    # don't do counters on older firmwares
    app._ezsp._ezsp_version = 4
    app._ezsp._protocol.readCounters.reset_mock()
    await app._watchdog_feed()
    assert app._ezsp._protocol.readCounters.await_count == 0
    assert app._ezsp._protocol.nop.await_count != 0


async def test_ezsp_value_counter(app, monkeypatch):
    from bellows.zigbee import application

    monkeypatch.setattr(application.ControllerApplication, "_watchdog_period", 0.01)
    nop_success = 3

    async def counters_mock():
        nonlocal nop_success
        if nop_success:
            nop_success -= 1
            if nop_success % 2:
                raise EzspError
            else:
                return {t.EmberCounterType(i): v for i, v in enumerate([0, 1, 2, 3])}
        raise asyncio.TimeoutError

    app._ezsp.read_counters = AsyncMock(side_effect=counters_mock)
    app._ezsp.nop = AsyncMock(side_effect=EzspError)
    app._ezsp.getValue = AsyncMock(
        return_value=(t.EzspStatus.ERROR_OUT_OF_MEMORY, b"\x20")
    )
    app._handle_reset_request = MagicMock()
    app._ctrl_event.set()

    await app._watchdog_feed()
    assert app._ezsp.read_counters.await_count != 0
    assert app._ezsp.nop.await_count == 0

    cnt = t.EmberCounterType
    assert (
        app.state.counters[application.COUNTERS_EZSP][
            cnt.COUNTER_MAC_RX_BROADCAST.name[8:]
        ]
        == 0
    )
    assert (
        app.state.counters[application.COUNTERS_EZSP][
            cnt.COUNTER_MAC_TX_BROADCAST.name[8:]
        ]
        == 1
    )
    assert (
        app.state.counters[application.COUNTERS_EZSP][
            cnt.COUNTER_MAC_RX_UNICAST.name[8:]
        ]
        == 2
    )
    assert (
        app.state.counters[application.COUNTERS_EZSP][
            cnt.COUNTER_MAC_TX_UNICAST_SUCCESS.name[8:]
        ]
        == 3
    )
    assert (
        app.state.counters[application.COUNTERS_EZSP].get(
            application.COUNTER_EZSP_BUFFERS
        )
        is None
    )
    assert (
        app.state.counters[application.COUNTERS_CTRL][application.COUNTER_WATCHDOG] == 0
    )

    # Ezsp Value success
    app._ezsp.getValue = AsyncMock(return_value=(t.EzspStatus.SUCCESS, b"\x20"))
    nop_success = 3
    await app._watchdog_feed()
    assert (
        app.state.counters[application.COUNTERS_EZSP][application.COUNTER_EZSP_BUFFERS]
        == 0x20
    )


async def test_shutdown(app):
    ezsp = app._ezsp

    await app.disconnect()
    assert app.controller_event.is_set() is False
    assert len(ezsp.disconnect.mock_calls) == 1


@pytest.fixture
def coordinator(app, ieee):
    dev = zigpy.device.Device(app, ieee, 0x0000)
    dev.endpoints[1] = bellows.zigbee.device.EZSPGroupEndpoint.from_descriptor(
        dev, 1, MagicMock()
    )
    dev.model = dev.endpoints[1].model
    dev.manufacturer = dev.endpoints[1].manufacturer

    return dev


async def test_ezsp_add_to_group(coordinator):
    coordinator.application._multicast = MagicMock()
    mc = coordinator.application._multicast
    mc.subscribe = AsyncMock(return_value=t.EmberStatus.SUCCESS)

    grp_id = 0x2345
    assert grp_id not in coordinator.endpoints[1].member_of
    ret = await coordinator.add_to_group(grp_id)
    assert ret is None
    assert mc.subscribe.call_count == 1
    assert mc.subscribe.call_args[0][0] == grp_id
    assert grp_id in coordinator.endpoints[1].member_of


async def test_ezsp_add_to_group_ep(coordinator):
    coordinator.application._multicast = MagicMock()
    mc = coordinator.application._multicast
    mc.subscribe = AsyncMock(return_value=t.EmberStatus.SUCCESS)

    grp_id = 0x2345
    assert grp_id not in coordinator.endpoints[1].member_of
    await coordinator.endpoints[1].add_to_group(grp_id)
    assert mc.subscribe.call_count == 1
    assert mc.subscribe.call_args[0][0] == grp_id
    assert grp_id in coordinator.endpoints[1].member_of

    mc.reset_mock()
    await coordinator.endpoints[1].add_to_group(grp_id)
    assert mc.subscribe.call_count == 0


async def test_ezsp_add_to_group_fail(coordinator):
    coordinator.application._multicast = MagicMock()
    mc = coordinator.application._multicast
    mc.subscribe = AsyncMock(return_value=t.EmberStatus.ERR_FATAL)

    grp_id = 0x2345
    assert grp_id not in coordinator.endpoints[1].member_of
    with pytest.raises(ValueError):
        await coordinator.add_to_group(grp_id)
    assert mc.subscribe.call_count == 1
    assert mc.subscribe.call_args[0][0] == grp_id
    assert grp_id not in coordinator.endpoints[1].member_of


async def test_ezsp_add_to_group_ep_fail(coordinator):
    coordinator.application._multicast = MagicMock()
    mc = coordinator.application._multicast
    mc.subscribe = AsyncMock(return_value=t.EmberStatus.ERR_FATAL)

    grp_id = 0x2345
    assert grp_id not in coordinator.endpoints[1].member_of
    with pytest.raises(ValueError):
        await coordinator.endpoints[1].add_to_group(grp_id)
    assert mc.subscribe.call_count == 1
    assert mc.subscribe.call_args[0][0] == grp_id
    assert grp_id not in coordinator.endpoints[1].member_of


async def test_ezsp_remove_from_group(coordinator):
    coordinator.application._multicast = MagicMock()
    mc = coordinator.application._multicast
    mc.unsubscribe = AsyncMock(return_value=t.EmberStatus.SUCCESS)

    grp_id = 0x2345
    grp = coordinator.application.groups.add_group(grp_id)
    grp.add_member(coordinator.endpoints[1])

    assert grp_id in coordinator.endpoints[1].member_of
    await coordinator.remove_from_group(grp_id)
    assert mc.unsubscribe.call_count == 1
    assert mc.unsubscribe.call_args[0][0] == grp_id
    assert grp_id not in coordinator.endpoints[1].member_of


async def test_ezsp_remove_from_group_ep(coordinator):
    coordinator.application._multicast = MagicMock()
    mc = coordinator.application._multicast
    mc.unsubscribe = AsyncMock(return_value=t.EmberStatus.SUCCESS)

    grp_id = 0x2345
    grp = coordinator.application.groups.add_group(grp_id)
    grp.add_member(coordinator.endpoints[1])

    assert grp_id in coordinator.endpoints[1].member_of
    await coordinator.endpoints[1].remove_from_group(grp_id)
    assert mc.unsubscribe.call_count == 1
    assert mc.unsubscribe.call_args[0][0] == grp_id
    assert grp_id not in coordinator.endpoints[1].member_of

    mc.reset_mock()
    await coordinator.endpoints[1].remove_from_group(grp_id)
    assert mc.subscribe.call_count == 0


async def test_ezsp_remove_from_group_fail(coordinator):
    coordinator.application._multicast = MagicMock()
    mc = coordinator.application._multicast
    mc.unsubscribe = AsyncMock(return_value=t.EmberStatus.ERR_FATAL)

    grp_id = 0x2345
    grp = coordinator.application.groups.add_group(grp_id)
    grp.add_member(coordinator.endpoints[1])

    assert grp_id in coordinator.endpoints[1].member_of

    with pytest.raises(ValueError):
        await coordinator.remove_from_group(grp_id)
    assert mc.unsubscribe.call_count == 1
    assert mc.unsubscribe.call_args[0][0] == grp_id


async def test_ezsp_remove_from_group_fail_ep(coordinator):
    coordinator.application._multicast = MagicMock()
    mc = coordinator.application._multicast
    mc.unsubscribe = AsyncMock(return_value=t.EmberStatus.ERR_FATAL)

    grp_id = 0x2345
    grp = coordinator.application.groups.add_group(grp_id)
    grp.add_member(coordinator.endpoints[1])

    assert grp_id in coordinator.endpoints[1].member_of

    with pytest.raises(ValueError):
        await coordinator.endpoints[1].remove_from_group(grp_id)

    assert mc.unsubscribe.call_count == 1
    assert mc.unsubscribe.call_args[0][0] == grp_id


def test_coordinator_model_manuf(coordinator):
    """Test we get coordinator manufacturer and model."""
    assert coordinator.endpoints[1].manufacturer
    assert coordinator.endpoints[1].model


def test_handle_route_record(app):
    """Test route record handling for an existing device."""
    app.handle_relays = MagicMock(spec_set=app.handle_relays)
    app.ezsp_callback_handler(
        "incomingRouteRecordHandler",
        [sentinel.nwk, sentinel.ieee, sentinel.lqi, sentinel.rssi, sentinel.relays],
    )
    app.handle_relays.assert_called_once_with(nwk=sentinel.nwk, relays=sentinel.relays)


def test_handle_route_error(app):
    """Test route error handler."""
    app.handle_relays = MagicMock(spec_set=app.handle_relays)
    app.ezsp_callback_handler(
        "incomingRouteErrorHandler", [sentinel.status, sentinel.nwk]
    )
    app.handle_relays.assert_not_called()


def test_handle_id_conflict(app, ieee):
    """Test handling of an ID conflict report."""
    nwk = t.EmberNodeId(0x1234)
    app.add_device(ieee, nwk)
    app.handle_leave = MagicMock()

    app.ezsp_callback_handler("idConflictHandler", [nwk + 1])
    assert app.handle_leave.call_count == 0

    app.ezsp_callback_handler("idConflictHandler", [nwk])
    assert app.handle_leave.call_count == 1
    assert app.handle_leave.call_args[0][0] == nwk


async def test_handle_no_such_device(app, ieee):
    """Test handling of an unknown device IEEE lookup."""

    app._ezsp.lookupEui64ByNodeId = AsyncMock()

    p1 = patch.object(
        app._ezsp,
        "lookupEui64ByNodeId",
        AsyncMock(return_value=(t.EmberStatus.ERR_FATAL, ieee)),
    )
    p2 = patch.object(app, "handle_join")
    with p1 as lookup_mock, p2 as handle_join_mock:
        await app._handle_no_such_device(sentinel.nwk)
        assert lookup_mock.mock_calls == [call(nodeId=sentinel.nwk)]
        assert handle_join_mock.call_count == 0

    p1 = patch.object(
        app._ezsp,
        "lookupEui64ByNodeId",
        AsyncMock(return_value=(t.EmberStatus.SUCCESS, sentinel.ieee)),
    )
    with p1 as lookup_mock, p2 as handle_join_mock:
        await app._handle_no_such_device(sentinel.nwk)
        assert lookup_mock.mock_calls == [call(nodeId=sentinel.nwk)]
        assert handle_join_mock.call_count == 1
        assert handle_join_mock.call_args[0][0] == sentinel.nwk
        assert handle_join_mock.call_args[0][1] == sentinel.ieee


async def test_cleanup_tc_link_key(app):
    """Test cleaning up tc link key."""
    ezsp = app._ezsp
    ezsp.findKeyTableEntry = AsyncMock(side_effect=((0xFF,), (sentinel.index,)))
    ezsp.eraseKeyTableEntry = AsyncMock(return_value=(0x00,))

    await app.cleanup_tc_link_key(sentinel.ieee)
    assert ezsp.findKeyTableEntry.mock_calls == [
        call(address=sentinel.ieee, linkKey=True)
    ]
    assert ezsp.eraseKeyTableEntry.await_count == 0
    assert ezsp.eraseKeyTableEntry.call_count == 0

    ezsp.findKeyTableEntry.reset_mock()
    await app.cleanup_tc_link_key(sentinel.ieee2)
    assert ezsp.findKeyTableEntry.mock_calls == [
        call(address=sentinel.ieee2, linkKey=True)
    ]
    assert ezsp.eraseKeyTableEntry.mock_calls == [call(index=sentinel.index)]


# @patch("zigpy.application.ControllerApplication.permit", new=AsyncMock())
async def test_permit(app):
    """Test permit method."""
    await app.permit(10)
    await asyncio.sleep(0.1)
    assert app._ezsp._protocol.add_transient_link_key.await_count == 1


@patch("bellows.zigbee.application.MFG_ID_RESET_DELAY", new=0.01)
@pytest.mark.parametrize(
    "ieee, expected_mfg_id",
    (
        ("54:ef:44:00:00:00:00:11", 0x115F),
        ("04:cf:8c:00:00:00:00:11", 0x115F),
        ("01:22:33:00:00:00:00:11", None),
    ),
)
async def test_set_mfg_id(ieee, expected_mfg_id, app):
    """Test setting manufacturer id based on IEEE address."""

    app.handle_join = MagicMock()
    app.cleanup_tc_link_key = AsyncMock()

    app.ezsp_callback_handler(
        "trustCenterJoinHandler",
        [
            1,
            t.EUI64.convert(ieee),
            t.EmberDeviceUpdate.STANDARD_SECURITY_UNSECURED_JOIN,
            t.EmberJoinDecision.NO_ACTION,
            sentinel.parent,
        ],
    )
    # preempt
    app.ezsp_callback_handler(
        "trustCenterJoinHandler",
        [
            1,
            t.EUI64.convert(ieee),
            t.EmberDeviceUpdate.STANDARD_SECURITY_UNSECURED_JOIN,
            t.EmberJoinDecision.NO_ACTION,
            sentinel.parent,
        ],
    )
    await asyncio.sleep(0.20)
    if expected_mfg_id is not None:
        assert app._ezsp._protocol.setManufacturerCode.mock_calls == [
            call(code=expected_mfg_id),
            call(code=bellows.zigbee.application.DEFAULT_MFG_ID),
        ]
    else:
        assert app._ezsp._protocol.setManufacturerCode.mock_calls == []


async def test_ensure_network_running_joined(app):
    ezsp = app._ezsp

    # Make initialization take two attempts
    ezsp.initialize_network = AsyncMock(
        side_effect=[
            bellows.types.sl_Status.INVALID_PARAMETER,
            bellows.types.sl_Status.OK,
        ]
    )
    ezsp.networkState = AsyncMock(return_value=[t.EmberNetworkStatus.JOINED_NETWORK])

    rsp = await app._ensure_network_running()

    assert not rsp

    ezsp.initialize_network.assert_not_called()


async def test_ensure_network_running_not_joined_failure(app):
    ezsp = app._ezsp
    ezsp.networkState = AsyncMock(return_value=[t.EmberNetworkStatus.NO_NETWORK])
    ezsp.initialize_network = AsyncMock(
        return_value=bellows.types.sl_Status.INVALID_PARAMETER
    )

    with pytest.raises(zigpy.exceptions.ControllerException):
        await app._ensure_network_running()

    ezsp.networkState.assert_called_once()
    ezsp.initialize_network.assert_called_once()


async def test_ensure_network_running_not_joined_success(app):
    ezsp = app._ezsp
    ezsp.networkState = AsyncMock(return_value=[t.EmberNetworkStatus.NO_NETWORK])
    ezsp.initialize_network = AsyncMock(return_value=bellows.types.sl_Status.OK)

    rsp = await app._ensure_network_running()
    assert rsp

    ezsp.networkState.assert_called_once()
    ezsp.initialize_network.assert_called_once()


async def test_startup_coordinator_existing_groups_joined(app, ieee):
    """Coordinator joins groups loaded from the database."""
    with mock_for_startup(app, ieee):
        await app.connect()

        db_device = app.add_device(ieee, 0x0000)
        db_ep = db_device.add_endpoint(1)

        group = app.groups.add_group(0x1234, "Group Name", suppress_event=True)
        group.add_member(db_ep, suppress_event=True)

        await app.start_network()

    assert app._ezsp._protocol.setMulticastTableEntry.mock_calls == [
        call(
            0,
            t.EmberMulticastTableEntry(multicastId=0x1234, endpoint=1, networkIndex=0),
        )
    ]


async def test_startup_coordinator_xncp_wildcard_groups(app, ieee):
    """Coordinator ignores multicast workarounds with XNCP firmware."""
    with mock_for_startup(app, ieee) as ezsp:
        ezsp._xncp_features |= FirmwareFeatures.MEMBER_OF_ALL_GROUPS

        await app.connect()
        await app.start_network()

    # No multicast workarounds are present
    assert app._multicast is None
    assert not isinstance(app._device.endpoints[1], EZSPGroupEndpoint)


async def test_startup_new_coordinator_no_groups_joined(app, ieee):
    """Coordinator freshy added to the database has no groups to join."""
    with mock_for_startup(app, ieee):
        await app.connect()
        await app.start_network()

    assert app._ezsp._protocol.setMulticastTableEntry.mock_calls == []


@pytest.mark.parametrize(
    "scan_results",
    [
        # Normal
        [
            -39,
            -30,
            -26,
            -33,
            -23,
            -53,
            -42,
            -46,
            -69,
            -75,
            -49,
            -67,
            -57,
            -81,
            -29,
            -40,
        ],
        # Maximum
        [10] * (26 - 11 + 1),
        # Minimum
        [-200] * (26 - 11 + 1),
    ],
)
async def test_energy_scanning(app, scan_results):
    app._ezsp.startScan = AsyncMock(
        return_value=list(zip(range(11, 26 + 1), scan_results))
    )

    results = await app.energy_scan(
        channels=t.Channels.ALL_CHANNELS,
        duration_exp=2,
        count=1,
    )

    assert len(app._ezsp.startScan.mock_calls) == 1

    assert set(results.keys()) == set(t.Channels.ALL_CHANNELS)
    assert all(0 <= v <= 255 for v in results.values())


async def test_energy_scanning_partial(app):
    app._ezsp.startScan = AsyncMock(
        side_effect=[
            [(11, 11), (12, 12), (13, 13), (14, 14), (15, 15), (16, 16)],
            [(17, 17)],  # Channel that doesn't exist
            [],
            [(18, 18), (19, 19), (20, 20)],
            [(18, 18), (19, 19), (20, 20)],  # Duplicate results
            [(21, 21), (22, 22), (23, 23), (24, 24), (25, 25), (26, 26)],
        ]
    )

    results = await app.energy_scan(
        channels=t.Channels.from_channel_list([11, 13, 14, 15, 20, 25, 26]),
        duration_exp=2,
        count=1,
    )

    assert len(app._ezsp.startScan.mock_calls) == 6
    assert set(results.keys()) == {11, 13, 14, 15, 20, 25, 26}
    assert results == {c: map_rssi_to_energy(c) for c in [11, 13, 14, 15, 20, 25, 26]}


async def test_connect_failure(app: ControllerApplication) -> None:
    """Test that a failure to connect propagates."""
    ezsp = app._ezsp
    app._ezsp.write_config = AsyncMock(side_effect=OSError())
    app._ezsp.connect = AsyncMock()
    app._ezsp = None

    with patch("bellows.ezsp.EZSP", return_value=ezsp):
        with pytest.raises(OSError):
            await app.connect()

    assert app._ezsp is None

    assert len(ezsp.disconnect.mock_calls) == 1


async def test_repair_tclk_partner_ieee(
    app: ControllerApplication, ieee: zigpy_t.EUI64
) -> None:
    """Test that EZSP is reset after repairing TCLK."""
    app._reset = AsyncMock()

    with mock_for_startup(app, ieee), patch(
        "bellows.zigbee.repairs.fix_invalid_tclk_partner_ieee",
        AsyncMock(return_value=False),
    ):
        await app.connect()
        await app.start_network()

    assert len(app._reset.mock_calls) == 0
    app._reset.reset_mock()

    with mock_for_startup(app, ieee), patch(
        "bellows.zigbee.repairs.fix_invalid_tclk_partner_ieee",
        AsyncMock(return_value=True),
    ):
        await app.start_network()

    assert len(app._reset.mock_calls) == 1


@pytest.fixture
def zigpy_backup() -> zigpy.backups.NetworkBackup:
    return zigpy.backups.NetworkBackup(
        node_info=zigpy.state.NodeInfo(
            nwk=zigpy_t.NWK(0x0000),
            ieee=t.EUI64.convert("07:06:05:04:03:02:01:00"),
            logical_type=zdo_t.LogicalType.Coordinator,
            model="Mock board",
            manufacturer="Mock Manufacturer",
            version="Mock version",
        ),
        network_info=zigpy.state.NetworkInfo(
            extended_pan_id=zigpy_t.ExtendedPanId.convert("aa:bb:cc:dd:ee:ff:aa:bb"),
            pan_id=zigpy_t.PanId(0x55AA),
            nwk_update_id=1,
            nwk_manager_id=zigpy_t.NWK(0x0000),
            channel=t.uint8_t(25),
            channel_mask=t.Channels.ALL_CHANNELS,
            security_level=t.uint8_t(1),
            network_key=zigpy.state.Key(
                key=t.KeyData.convert(
                    "41:63:74:75:61:6c:4e:65:74:77:6f:72:6b:4b:65:79"
                ),
                seq=1,
                tx_counter=305419896,
            ),
            tc_link_key=zigpy.state.Key(
                key=t.KeyData(b"ZigBeeAlliance09"),
                partner_ieee=t.EUI64.convert("07:06:05:04:03:02:01:00"),
                tx_counter=2271560481,
            ),
            key_table=[
                zigpy.state.Key(
                    key=t.KeyData.convert(
                        "74:65:73:74:5f:6c:69:6e:6b:5f:6b:65:79:5f:30:31"
                    ),
                    tx_counter=12345,
                    rx_counter=67890,
                    seq=1,
                    partner_ieee=t.EUI64.convert("aa:bb:cc:dd:ee:ff:00:11"),
                ),
                zigpy.state.Key(
                    key=t.KeyData.convert(
                        "74:65:73:74:5f:6c:69:6e:6b:5f:6b:65:79:5f:30:32"
                    ),
                    tx_counter=54321,
                    rx_counter=98765,
                    seq=2,
                    partner_ieee=t.EUI64.convert("11:22:33:44:55:66:77:88"),
                ),
            ],
            children=[
                t.EUI64.convert("aa:bb:cc:dd:ee:ff:00:11"),
                t.EUI64.convert("11:22:33:44:55:66:77:88"),
            ],
            nwk_addresses={
                t.EUI64.convert("aa:bb:cc:dd:ee:ff:00:11"): zigpy_t.NWK(0x1234),
                t.EUI64.convert("dc:ba:00:11:22:33:44:55"): zigpy_t.NWK(0xDCBA),
                t.EUI64.convert("ab:cd:00:11:22:33:44:55"): zigpy_t.NWK(0xABCD),
                t.EUI64.convert("11:22:33:44:55:66:77:88"): zigpy_t.NWK(0x5678),
            },
            stack_specific={"ezsp": {"hashed_tclk": b"thehashedlinkkey".hex()}},
            source=f"bellows@{importlib.metadata.version('bellows')}",
            metadata={
                "ezsp": {
                    "stack_version": 8,
                    "flow_control": "hardware",
                    "can_burn_userdata_custom_eui64": True,
                    "can_rewrite_custom_eui64": True,
                }
            },
        ),
    )


async def test_load_network_info(
    app: ControllerApplication,
    ieee: zigpy_t.EUI64,
    zigpy_backup: zigpy.backups.NetworkBackup,
) -> None:
    await app.load_network_info(load_devices=True)

    zigpy_backup.network_info.metadata["ezsp"]["flow_control"] = None

    assert app.state.node_info == zigpy_backup.node_info
    assert app.state.network_info == zigpy_backup.network_info


async def test_load_network_info_xncp_flow_control(
    app: ControllerApplication,
    ieee: zigpy_t.EUI64,
    zigpy_backup: zigpy.backups.NetworkBackup,
) -> None:
    app._ezsp._xncp_features |= FirmwareFeatures.FLOW_CONTROL_TYPE
    app._ezsp.xncp_get_flow_control_type = AsyncMock(
        return_value=FlowControlType.HARDWARE
    )

    await app.load_network_info(load_devices=True)

    assert app.state.node_info == zigpy_backup.node_info
    assert app.state.network_info == zigpy_backup.network_info


async def test_write_network_info(
    app: ControllerApplication,
    ieee: zigpy_t.EUI64,
    zigpy_backup: zigpy.backups.NetworkBackup,
) -> None:
    with patch.object(app, "_reset"):
        await app.write_network_info(
            node_info=zigpy_backup.node_info,
            network_info=zigpy_backup.network_info,
        )

    assert app._ezsp._protocol.write_nwk_frame_counter.mock_calls == [
        call(zigpy_backup.network_info.network_key.tx_counter)
    ]
    assert app._ezsp._protocol.write_aps_frame_counter.mock_calls == [
        call(zigpy_backup.network_info.tc_link_key.tx_counter)
    ]
    assert app._ezsp._protocol.formNetwork.mock_calls == [
        call(
            parameters=t.EmberNetworkParameters(
                panId=zigpy_backup.network_info.pan_id,
                extendedPanId=zigpy_backup.network_info.extended_pan_id,
                radioTxPower=t.uint8_t(8),
                radioChannel=zigpy_backup.network_info.channel,
                joinMethod=t.EmberJoinMethod.USE_MAC_ASSOCIATION,
                nwkManagerId=t.EmberNodeId(0x0000),
                nwkUpdateId=zigpy_backup.network_info.nwk_update_id,
                channels=zigpy_backup.network_info.channel_mask,
            )
        )
    ]


async def test_network_scan(app: ControllerApplication) -> None:
    app._ezsp._protocol.startScan.return_value = [t.sl_Status.OK]

    def run_scan() -> None:
        app._ezsp._protocol._handle_callback(
            "networkFoundHandler",
            list(
                {
                    "networkFound": t.EmberZigbeeNetwork(
                        channel=11,
                        panId=zigpy_t.PanId(0x1D13),
                        extendedPanId=t.EUI64.convert("00:07:81:00:00:9a:8f:3b"),
                        allowingJoin=False,
                        stackProfile=2,
                        nwkUpdateId=0,
                    ),
                    "lastHopLqi": 152,
                    "lastHopRssi": -62,
                }.values()
            ),
        )
        app._ezsp._protocol._handle_callback(
            "networkFoundHandler",
            list(
                {
                    "networkFound": t.EmberZigbeeNetwork(
                        channel=11,
                        panId=zigpy_t.PanId(0x2857),
                        extendedPanId=t.EUI64.convert("00:07:81:00:00:9a:34:1b"),
                        allowingJoin=False,
                        stackProfile=2,
                        nwkUpdateId=0,
                    ),
                    "lastHopLqi": 136,
                    "lastHopRssi": -66,
                }.values()
            ),
        )
        app._ezsp._protocol._handle_callback(
            "scanCompleteHandler",
            list(
                {
                    "channel": 26,
                    "status": t.sl_Status.OK,
                }.values()
            ),
        )

    asyncio.get_running_loop().call_soon(run_scan)

    results = [
        beacon
        async for beacon in app.network_scan(
            channels=t.Channels.from_channel_list([11, 15, 26]), duration_exp=4
        )
    ]

    assert results == [
        zigpy_t.NetworkBeacon(
            pan_id=0x1D13,
            extended_pan_id=t.EUI64.convert("00:07:81:00:00:9a:8f:3b"),
            channel=11,
            permit_joining=False,
            stack_profile=2,
            nwk_update_id=0,
            lqi=152,
            src=None,
            rssi=-62,
            depth=None,
            router_capacity=None,
            device_capacity=None,
            protocol_version=None,
        ),
        zigpy_t.NetworkBeacon(
            pan_id=0x2857,
            extended_pan_id=t.EUI64.convert("00:07:81:00:00:9a:34:1b"),
            channel=11,
            permit_joining=False,
            stack_profile=2,
            nwk_update_id=0,
            lqi=136,
            src=None,
            rssi=-66,
            depth=None,
            router_capacity=None,
            device_capacity=None,
            protocol_version=None,
        ),
    ]


async def test_network_scan_failure(app: ControllerApplication) -> None:
    app._ezsp._protocol.startScan.return_value = [t.sl_Status.FAIL]

    with pytest.raises(zigpy.exceptions.ControllerException):
        async for beacon in app.network_scan(
            channels=t.Channels.from_channel_list([11, 15, 26]), duration_exp=4
        ):
            pass


async def test_packet_capture(app: ControllerApplication) -> None:
    app._ezsp._protocol.mfglibStart.return_value = [t.sl_Status.OK]
    app._ezsp._protocol.mfglibSetChannel.return_value = [t.sl_Status.OK]
    app._ezsp._protocol.mfglibEnd.return_value = [t.sl_Status.OK]

    async def receive_packets() -> None:
        app._ezsp._protocol._handle_callback(
            "mfglibRxHandler",
            list(
                {
                    "linkQuality": 150,
                    "rssi": -70,
                    "packetContents": b"packet 1\xAB\xCD",
                }.values()
            ),
        )

        await asyncio.sleep(0.5)

        app._ezsp._protocol._handle_callback(
            "mfglibRxHandler",
            list(
                {
                    "linkQuality": 200,
                    "rssi": -50,
                    "packetContents": b"packet 2\xAB\xCD",
                }.values()
            ),
        )

    task = asyncio.create_task(receive_packets())
    packets = []

    async for packet in app.packet_capture(channel=15):
        packets.append(packet)

        if len(packets) == 1:
            await app.packet_capture_change_channel(channel=20)
        elif len(packets) == 2:
            break

    assert packets == [
        zigpy_t.CapturedPacket(
            timestamp=packets[0].timestamp,
            rssi=-70,
            lqi=150,
            channel=15,
            data=b"packet 1",
        ),
        zigpy_t.CapturedPacket(
            timestamp=packets[1].timestamp,
            rssi=-50,
            lqi=200,
            channel=20,  # The second packet's channel was changed
            data=b"packet 2",
        ),
    ]

    await task
    await asyncio.sleep(0.1)

    assert app._ezsp._protocol.mfglibEnd.mock_calls == [call()]


async def test_packet_capture_failure(app: ControllerApplication) -> None:
    app._ezsp._protocol.mfglibStart.return_value = [t.sl_Status.FAIL]

    with pytest.raises(zigpy.exceptions.ControllerException):
        async for packet in app.packet_capture(channel=15):
            pass


async def test_migration_failure_eui64_overwrite_confirmation(
    app: ControllerApplication,
    zigpy_backup: zigpy.backups.NetworkBackup,
) -> None:
    app._ezsp.can_rewrite_custom_eui64 = AsyncMock(return_value=False)

    # Migration explicitly fails if we need to write the EUI64 but the adapter treats it
    # as a write-once operation
    with pytest.raises(
        zigpy.exceptions.ControllerException,
        match=(
            "Please upgrade your adapter firmware. The adapter IEEE address needs to be"
            " replaced and firmware 'Mock version' does not support writing it multiple"
            " times."
        ),
    ):
        with patch.object(app, "_reset"):
            await app.write_network_info(
                node_info=zigpy_backup.node_info.replace(
                    ieee=t.EUI64.convert("aa:aa:aa:aa:aa:aa:aa:aa")
                ),
                network_info=zigpy_backup.network_info,
            )

    # Even if we opt in, if the adapter doesn't support it, we can't do anything
    with patch.object(app, "_reset"), patch.object(
        app._ezsp, "write_custom_eui64", wraps=app._ezsp.write_custom_eui64
    ), patch.object(app._ezsp, "can_burn_userdata_custom_eui64", return_value=False):
        with pytest.raises(
            zigpy.exceptions.ControllerException,
            match=(
                "Please upgrade your adapter firmware. The adapter IEEE address has"
                " been overwritten and firmware 'Mock version' does not support writing"
                " it a second time."
            ),
        ):
            await app.write_network_info(
                node_info=zigpy_backup.node_info.replace(
                    ieee=t.EUI64.convert("aa:aa:aa:aa:aa:aa:aa:aa")
                ),
                network_info=zigpy_backup.network_info.replace(
                    stack_specific={
                        "ezsp": {
                            **zigpy_backup.network_info.stack_specific["ezsp"],
                            "i_understand_i_can_update_eui64_only_once_and_i_still_want_to_do_it": True,
                        }
                    }
                ),
            )

        assert app._ezsp.write_custom_eui64.mock_calls == []

    # It works if everything is correct
    with patch.object(app, "_reset"), patch.object(
        app._ezsp, "write_custom_eui64"
    ), patch.object(app._ezsp, "can_burn_userdata_custom_eui64", return_value=True):
        await app.write_network_info(
            node_info=zigpy_backup.node_info.replace(
                ieee=t.EUI64.convert("aa:aa:aa:aa:aa:aa:aa:aa")
            ),
            network_info=zigpy_backup.network_info.replace(
                stack_specific={
                    "ezsp": {
                        **zigpy_backup.network_info.stack_specific["ezsp"],
                        "i_understand_i_can_update_eui64_only_once_and_i_still_want_to_do_it": True,
                    }
                }
            ),
        )

        assert app._ezsp.write_custom_eui64.mock_calls == [
            call(t.EUI64.convert("aa:aa:aa:aa:aa:aa:aa:aa"), burn_into_userdata=True)
        ]
