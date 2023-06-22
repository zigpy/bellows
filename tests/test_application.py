import asyncio
import logging

import pytest
import zigpy.config
import zigpy.device
import zigpy.exceptions
import zigpy.types as zigpy_t
import zigpy.zdo.types as zdo_t

import bellows.config as config
from bellows.exception import ControllerError, EzspError
import bellows.ezsp as ezsp
import bellows.ezsp.v4.types as t
import bellows.ezsp.v5.types as ezsp_t5
import bellows.ezsp.v6.types as ezsp_t6
import bellows.ezsp.v7.types as ezsp_t7
import bellows.ezsp.v8.types as ezsp_t8
import bellows.types.struct
import bellows.uart as uart
import bellows.zigbee.application
import bellows.zigbee.device
from bellows.zigbee.util import map_rssi_to_energy

from .async_mock import AsyncMock, MagicMock, PropertyMock, patch, sentinel

APP_CONFIG = {
    config.CONF_DEVICE: {
        config.CONF_DEVICE_PATH: "/dev/null",
        config.CONF_DEVICE_BAUDRATE: 115200,
    },
    zigpy.config.CONF_DATABASE: None,
}


@pytest.fixture
def ezsp_mock():
    """EZSP fixture"""
    mock_ezsp = MagicMock(spec=ezsp.EZSP)
    mock_ezsp.ezsp_version = 7
    mock_ezsp.setManufacturerCode = AsyncMock()
    mock_ezsp.set_source_route = AsyncMock(return_value=[t.EmberStatus.SUCCESS])
    mock_ezsp.addTransientLinkKey = AsyncMock(return_value=[0])
    mock_ezsp.readCounters = AsyncMock(return_value=[[0] * 10])
    mock_ezsp.readAndClearCounters = AsyncMock(return_value=[[0] * 10])
    mock_ezsp.setPolicy = AsyncMock(return_value=[0])
    mock_ezsp.get_board_info = AsyncMock(
        return_value=("Mock Manufacturer", "Mock board", "Mock version")
    )
    mock_ezsp.wait_for_stack_status.return_value.__enter__ = AsyncMock(
        return_value=t.EmberStatus.NETWORK_UP
    )

    type(mock_ezsp).types = ezsp_t7
    type(mock_ezsp).is_ezsp_running = PropertyMock(return_value=True)

    return mock_ezsp


@pytest.fixture
def make_app(monkeypatch, event_loop, ezsp_mock):
    def inner(config):
        app_cfg = bellows.zigbee.application.ControllerApplication.SCHEMA(
            {**APP_CONFIG, **config}
        )
        app = bellows.zigbee.application.ControllerApplication(app_cfg)

        app._ezsp = ezsp_mock
        monkeypatch.setattr(bellows.zigbee.application, "APS_ACK_TIMEOUT", 0.05)
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


@pytest.fixture
def ieee(init=0):
    return t.EmberEUI64(map(t.uint8_t, range(init, init + 8)))


@patch("zigpy.device.Device._initialize", new=AsyncMock())
@patch("bellows.zigbee.application.ControllerApplication._watchdog", new=AsyncMock())
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

    async def mock_leave(*args, **kwargs):
        app._ezsp.handle_callback("stackStatusHandler", [t.EmberStatus.NETWORK_DOWN])
        return [t.EmberStatus.NETWORK_DOWN]

    app._in_flight_msg = None
    ezsp_mock = MagicMock()
    ezsp_mock.types = ezsp_t7
    type(ezsp_mock).ezsp_version = PropertyMock(return_value=ezsp_version)
    ezsp_mock.initialize = AsyncMock(return_value=ezsp_mock)
    ezsp_mock.connect = AsyncMock()
    ezsp_mock.setConcentrator = AsyncMock()
    ezsp_mock._command = AsyncMock(return_value=t.EmberStatus.SUCCESS)
    ezsp_mock.addEndpoint = AsyncMock(return_value=t.EmberStatus.SUCCESS)
    ezsp_mock.setConfigurationValue = AsyncMock(return_value=t.EmberStatus.SUCCESS)
    ezsp_mock.networkInit = AsyncMock(return_value=[init])
    ezsp_mock.getNetworkParameters = AsyncMock(return_value=[0, nwk_type, nwk_params])
    ezsp_mock.can_burn_userdata_custom_eui64 = AsyncMock(return_value=True)
    ezsp_mock.can_rewrite_custom_eui64 = AsyncMock(return_value=True)
    ezsp_mock.startScan = AsyncMock(return_value=[[c, 1] for c in range(11, 26 + 1)])

    if board_info:
        ezsp_mock.get_board_info = AsyncMock(
            return_value=("Mock Manufacturer", "Mock board", "Mock version")
        )
    else:
        ezsp_mock.get_board_info = AsyncMock(side_effect=EzspError("Not supported"))

    ezsp_mock.setPolicy = AsyncMock(return_value=[t.EmberStatus.SUCCESS])
    ezsp_mock.getMfgToken = AsyncMock(return_value=(b"Some token\xff",))
    ezsp_mock.getNodeId = AsyncMock(return_value=[t.EmberNodeId(0x0000)])
    ezsp_mock.getEui64 = AsyncMock(return_value=[ieee])
    ezsp_mock.getValue = AsyncMock(return_value=(0, b"\x01" * 6))
    ezsp_mock.leaveNetwork = AsyncMock(side_effect=mock_leave)
    ezsp_mock.reset = AsyncMock()
    ezsp_mock.version = AsyncMock()
    ezsp_mock.getConfigurationValue = AsyncMock(return_value=(0, 1))
    ezsp_mock.update_policies = AsyncMock()
    ezsp_mock.networkState = AsyncMock(return_value=[network_state])
    ezsp_mock.getKey = AsyncMock(
        return_value=[
            t.EmberStatus.SUCCESS,
            t.EmberKeyStruct(
                bitmask=t.EmberKeyStructBitmask.KEY_HAS_SEQUENCE_NUMBER
                | t.EmberKeyStructBitmask.KEY_HAS_OUTGOING_FRAME_COUNTER,
                type=t.EmberKeyType.CURRENT_NETWORK_KEY,
                key=t.EmberKeyData(b"ActualNetworkKey"),
                outgoingFrameCounter=t.uint32_t(0x12345678),
                incomingFrameCounter=t.uint32_t(0x00000000),
                sequenceNumber=t.uint8_t(1),
                partnerEUI64=t.EmberEUI64.convert("ff:ff:ff:ff:ff:ff:ff:ff"),
            ),
        ]
    )

    ezsp_mock.getCurrentSecurityState = AsyncMock(
        return_value=[
            t.EmberStatus.SUCCESS,
            t.EmberCurrentSecurityState(
                bitmask=t.EmberCurrentSecurityBitmask.TRUST_CENTER_USES_HASHED_LINK_KEY,
                trustCenterLongAddress=t.EmberEUI64.convert("ff:ff:ff:ff:ff:ff:ff:ff"),
            ),
        ]
    )
    ezsp_mock.pre_permit = AsyncMock()
    app.permit = AsyncMock()

    def form_network():
        ezsp_mock.getNetworkParameters.return_value = [
            0,
            t.EmberNodeType.COORDINATOR,
            nwk_params,
        ]

    app.form_network = AsyncMock(side_effect=form_network)

    p1 = patch.object(bellows.ezsp, "EZSP", new=ezsp_mock)
    p2 = patch.object(bellows.multicast.Multicast, "startup")

    with p1, p2 as multicast_mock:
        await app.startup(auto_form=auto_form)
    assert multicast_mock.await_count == 1


async def test_startup(app, ieee):
    await _test_startup(app, t.EmberNodeType.COORDINATOR, ieee)


async def test_startup_ezsp_ver7(app, ieee):
    app.state.counters["ezsp_counters"] = MagicMock()
    await _test_startup(app, t.EmberNodeType.COORDINATOR, ieee, ezsp_version=7)
    assert app.state.counters["ezsp_counters"].reset.call_count == 1


async def test_startup_ezsp_ver8(app, ieee):
    app.state.counters["ezsp_counters"] = MagicMock()
    ieee_1 = t.EmberEUI64.convert("11:22:33:44:55:66:77:88")
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
            init=t.EmberStatus.NOT_JOINED,
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
            init=t.EmberStatus.ERR_FATAL,
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
    req = app._pending[254] = MagicMock()
    app.ezsp_callback_handler(
        "messageSentHandler", [msg_type, 0xBEED, aps, 254, sentinel.status, b""]
    )
    assert req.result.set_exception.call_count == 0
    assert req.result.set_result.call_count == 1
    assert req.result.set_result.call_args[0][0][0] is sentinel.status


def test_dup_send_failure(app, aps, ieee):
    req = app._pending[254] = MagicMock()
    req.result.set_result.side_effect = asyncio.InvalidStateError()
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
    assert req.result.set_exception.call_count == 0
    assert req.result.set_result.call_count == 1


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
    req = app._pending[253] = MagicMock()
    app.ezsp_callback_handler(
        "messageSentHandler",
        [
            t.EmberIncomingMessageType.INCOMING_MULTICAST_LOOPBACK,
            0xBEED,
            aps,
            253,
            sentinel.success,
            b"",
        ],
    )
    assert req.result.set_exception.call_count == 0
    assert req.result.set_result.call_count == 1
    assert req.result.set_result.call_args[0][0][0] is sentinel.success


def test_unexpected_send_success(app, aps, ieee):
    app.ezsp_callback_handler(
        "messageSentHandler",
        [t.EmberIncomingMessageType.INCOMING_MULTICAST, 0xBEED, aps, 253, 0, b""],
    )


def test_dup_send_success(app, aps, ieee):
    req = app._pending[253] = MagicMock()
    req.result.set_result.side_effect = asyncio.InvalidStateError()
    app.ezsp_callback_handler(
        "messageSentHandler",
        [t.EmberIncomingMessageType.INCOMING_MULTICAST, 0xBEED, aps, 253, 0, b""],
    )
    assert req.result.set_exception.call_count == 0
    assert req.result.set_result.call_count == 1


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
    app._ezsp.removeDevice = AsyncMock()
    dev = MagicMock()
    await app.force_remove(dev)


def test_sequence(app):
    for i in range(1000):
        seq = app.get_sequence()
        assert seq >= 0
        assert seq < 256


def test_permit_ncp(app):
    app._ezsp.permitJoining = AsyncMock()
    app.permit_ncp(60)
    assert app._ezsp.permitJoining.call_count == 1


@pytest.mark.parametrize(
    "version, tc_policy_count, ezsp_types",
    ((4, 0, t), (5, 0, ezsp_t5), (6, 0, ezsp_t6), (7, 0, ezsp_t7), (8, 1, ezsp_t8)),
)
async def test_permit_with_key(app, version, tc_policy_count, ezsp_types):
    p1 = patch("zigpy.application.ControllerApplication.permit")
    p2 = patch.object(app._ezsp, "types", ezsp_types)

    with patch.object(app._ezsp, "ezsp_version", version), p1 as permit_mock, p2:
        await app.permit_with_key(
            bytes([1, 2, 3, 4, 5, 6, 7, 8]),
            bytes([0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77, 0x88, 0x4A, 0xF7]),
            60,
        )

    assert app._ezsp.addTransientLinkKey.await_count == 1
    assert permit_mock.await_count == 1
    assert app._ezsp.setPolicy.await_count == tc_policy_count


@pytest.mark.parametrize(
    "version, tc_policy_count, ezsp_types",
    ((4, 0, t), (5, 0, ezsp_t5), (6, 0, ezsp_t6), (7, 0, ezsp_t7), (8, 1, ezsp_t8)),
)
async def test_permit_with_key_ieee(app, ieee, version, tc_policy_count, ezsp_types):
    p1 = patch("zigpy.application.ControllerApplication.permit")
    p2 = patch.object(app._ezsp, "types", ezsp_types)

    with patch.object(app._ezsp, "ezsp_version", version), p1 as permit_mock, p2:
        await app.permit_with_key(
            ieee,
            bytes([0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77, 0x88, 0x4A, 0xF7]),
            60,
        )

    assert app._ezsp.addTransientLinkKey.await_count == 1
    assert permit_mock.await_count == 1
    assert app._ezsp.setPolicy.await_count == tc_policy_count


async def test_permit_with_key_invalid_install_code(app, ieee):
    with pytest.raises(Exception):
        await app.permit_with_key(
            ieee, bytes([0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77, 0x88]), 60
        )


async def test_permit_with_key_failed_add_key(app, ieee):
    app._ezsp.addTransientLinkKey = AsyncMock(return_value=[1, 1])

    with pytest.raises(Exception):
        await app.permit_with_key(
            ieee,
            bytes([0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77, 0x88, 0x4A, 0xF7]),
            60,
        )


async def test_permit_with_key_failed_set_policy(app, ieee):
    app._ezsp.addTransientLinkKey = AsyncMock(return_value=[0])
    app._ezsp.setPolicy = AsyncMock(return_value=[1])

    with pytest.raises(Exception):
        await app.permit_with_key(
            ieee,
            bytes([0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77, 0x88, 0x4A, 0xF7]),
            60,
        )


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


async def _test_send_packet_unicast(app, packet, *, statuses=(t.EmberStatus.SUCCESS,)):
    def send_unicast(*args, **kwargs):
        nonlocal statuses

        status = statuses[0]
        statuses = statuses[1:]

        if not statuses:
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
                        status=status,
                        message=b"",
                    ).values()
                ),
            )

        return [status, 0x12]

    app._ezsp.sendUnicast = AsyncMock(side_effect=send_unicast)
    app.get_sequence = MagicMock(return_value=sentinel.msg_tag)

    expected_unicast_calls = len(statuses)

    await app.send_packet(packet)
    assert app._ezsp.sendUnicast.call_count == expected_unicast_calls
    assert (
        app._ezsp.sendUnicast.mock_calls[-1].args[0]
        == t.EmberOutgoingMessageType.OUTGOING_DIRECT
    )
    assert app._ezsp.sendUnicast.mock_calls[-1].args[1] == t.EmberNodeId(0x1234)

    aps_frame = app._ezsp.sendUnicast.mock_calls[-1].args[2]
    assert aps_frame.profileId == packet.profile_id
    assert aps_frame.clusterId == packet.cluster_id
    assert aps_frame.sourceEndpoint == packet.src_ep
    assert aps_frame.destinationEndpoint == packet.dst_ep
    assert aps_frame.sequence == packet.tsn
    assert aps_frame.groupId == 0x0000

    assert app._ezsp.sendUnicast.mock_calls[-1].args[3] == sentinel.msg_tag
    assert app._ezsp.sendUnicast.mock_calls[-1].args[4] == b"some data"

    assert len(app._pending) == 0


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

    assert app._ezsp.sendUnicast.call_count == 0


async def test_send_packet_unicast_source_route_ezsp7(make_app, packet):
    app = make_app({zigpy.config.CONF_SOURCE_ROUTING: True})
    app._ezsp.ezsp_version = 7
    app._ezsp.setSourceRoute = AsyncMock(return_value=(t.EmberStatus.SUCCESS,))

    packet.source_route = [0x0001, 0x0002]
    await _test_send_packet_unicast(app, packet)

    assert app._ezsp.setSourceRoute.await_count == 1
    app._ezsp.setSourceRoute.assert_called_once_with(
        packet.dst.address, [0x0001, 0x0002]
    )


async def test_send_packet_unicast_source_route_ezsp8_have_relays(make_app, packet):
    app = make_app({zigpy.config.CONF_SOURCE_ROUTING: True})
    app._ezsp.ezsp_version = 8

    device = MagicMock()
    device.relays = [0x0003]

    app.get_device = MagicMock(return_value=device)

    packet.source_route = [0x0001, 0x0002]
    await _test_send_packet_unicast(app, packet)

    aps_frame = app._ezsp.sendUnicast.mock_calls[0].args[2]
    assert t.EmberApsOption.APS_OPTION_ENABLE_ROUTE_DISCOVERY not in aps_frame.options


async def test_send_packet_unicast_source_route_ezsp8_no_relays(make_app, packet):
    app = make_app({zigpy.config.CONF_SOURCE_ROUTING: True})
    app._ezsp.ezsp_version = 8

    packet.source_route = [0x0001, 0x0002]
    await _test_send_packet_unicast(app, packet)

    aps_frame = app._ezsp.sendUnicast.mock_calls[0].args[2]
    assert t.EmberApsOption.APS_OPTION_ENABLE_ROUTE_DISCOVERY in aps_frame.options


async def test_send_packet_unicast_retries_success(app, packet):
    await _test_send_packet_unicast(
        app,
        packet,
        statuses=(
            t.EmberStatus.NO_BUFFERS,
            t.EmberStatus.NO_BUFFERS,
            t.EmberStatus.SUCCESS,
        ),
    )


async def test_send_packet_unicast_unexpected_failure(app, packet):
    with pytest.raises(zigpy.exceptions.DeliveryError):
        await _test_send_packet_unicast(
            app, packet, statuses=(t.EmberStatus.ERR_FATAL,)
        )


async def test_send_packet_unicast_retries_failure(app, packet):
    with pytest.raises(zigpy.exceptions.DeliveryError):
        await _test_send_packet_unicast(
            app,
            packet,
            statuses=(
                t.EmberStatus.NO_BUFFERS,
                t.EmberStatus.NO_BUFFERS,
                t.EmberStatus.NO_BUFFERS,
            ),
        )


async def test_send_packet_unicast_concurrency(app, packet, monkeypatch):
    monkeypatch.setattr(bellows.zigbee.application, "APS_ACK_TIMEOUT", 0.5)

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

    async def send_unicast(type, indexOrDestination, apsFrame, messageTag, message):
        nonlocal max_concurrency, in_flight_requests

        in_flight_requests += 1
        max_concurrency = max(max_concurrency, in_flight_requests)

        asyncio.create_task(
            send_message_sent_reply(
                type, indexOrDestination, apsFrame, messageTag, message
            )
        )

        return [t.EmberStatus.SUCCESS, 0x12]

    app._ezsp.sendUnicast = AsyncMock(side_effect=send_unicast)

    responses = await asyncio.gather(*[app.send_packet(packet) for _ in range(100)])
    assert len(responses) == 100
    assert max_concurrency == 10
    assert in_flight_requests == 0


async def test_send_packet_broadcast(app, packet):
    packet.dst = zigpy_t.AddrModeAddress(
        addr_mode=zigpy_t.AddrMode.Broadcast, address=0xFFFE
    )
    packet.radius = 30

    app._ezsp.sendBroadcast = AsyncMock(return_value=(t.EmberStatus.SUCCESS, 0x12))
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
    assert app._ezsp.sendBroadcast.call_count == 1
    assert app._ezsp.sendBroadcast.mock_calls[0].args[0] == t.EmberNodeId(0xFFFE)

    aps_frame = app._ezsp.sendBroadcast.mock_calls[0].args[1]
    assert aps_frame.profileId == packet.profile_id
    assert aps_frame.clusterId == packet.cluster_id
    assert aps_frame.sourceEndpoint == packet.src_ep
    assert aps_frame.destinationEndpoint == packet.dst_ep
    assert aps_frame.sequence == packet.tsn
    assert aps_frame.groupId == 0x0000

    assert app._ezsp.sendBroadcast.mock_calls[0].args[2] == packet.radius
    assert app._ezsp.sendBroadcast.mock_calls[0].args[3] == sentinel.msg_tag
    assert app._ezsp.sendBroadcast.mock_calls[0].args[4] == b"some data"

    assert len(app._pending) == 0


async def test_send_packet_broadcast_ignored_delivery_failure(app, packet):
    packet.dst = zigpy_t.AddrModeAddress(
        addr_mode=zigpy_t.AddrMode.Broadcast, address=0xFFFE
    )
    packet.radius = 30

    app._ezsp.sendBroadcast = AsyncMock(return_value=(t.EmberStatus.SUCCESS, 0x12))
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

    assert app._ezsp.sendBroadcast.call_count == 1
    assert app._ezsp.sendBroadcast.mock_calls[0].args[0] == t.EmberNodeId(0xFFFE)

    aps_frame = app._ezsp.sendBroadcast.mock_calls[0].args[1]
    assert aps_frame.profileId == packet.profile_id
    assert aps_frame.clusterId == packet.cluster_id
    assert aps_frame.sourceEndpoint == packet.src_ep
    assert aps_frame.destinationEndpoint == packet.dst_ep
    assert aps_frame.sequence == packet.tsn
    assert aps_frame.groupId == 0x0000

    assert app._ezsp.sendBroadcast.mock_calls[0].args[2] == packet.radius
    assert app._ezsp.sendBroadcast.mock_calls[0].args[3] == sentinel.msg_tag
    assert app._ezsp.sendBroadcast.mock_calls[0].args[4] == b"some data"

    assert len(app._pending) == 0


async def test_send_packet_multicast(app, packet):
    packet.dst = zigpy_t.AddrModeAddress(
        addr_mode=zigpy_t.AddrMode.Group, address=0x1234
    )
    packet.radius = 5
    packet.non_member_radius = 6

    app._ezsp.sendMulticast = AsyncMock(return_value=(t.EmberStatus.SUCCESS, 0x12))
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
    assert app._ezsp.sendMulticast.call_count == 1

    aps_frame = app._ezsp.sendMulticast.mock_calls[0].args[0]
    assert aps_frame.profileId == packet.profile_id
    assert aps_frame.clusterId == packet.cluster_id
    assert aps_frame.sourceEndpoint == packet.src_ep
    assert aps_frame.destinationEndpoint == packet.dst_ep
    assert aps_frame.sequence == packet.tsn
    assert aps_frame.groupId == 0x1234

    assert app._ezsp.sendMulticast.mock_calls[0].args[1] == packet.radius
    assert app._ezsp.sendMulticast.mock_calls[0].args[2] == packet.non_member_radius
    assert app._ezsp.sendMulticast.mock_calls[0].args[3] == sentinel.msg_tag
    assert app._ezsp.sendMulticast.mock_calls[0].args[4] == b"some data"

    assert len(app._pending) == 0


def test_is_controller_running(app):
    ezsp_running = PropertyMock(return_value=False)
    type(app._ezsp).is_ezsp_running = ezsp_running
    app._ctrl_event.clear()
    assert app.is_controller_running is False
    app._ctrl_event.set()
    assert app.is_controller_running is False
    assert ezsp_running.call_count == 1

    ezsp_running = PropertyMock(return_value=True)
    type(app._ezsp).is_ezsp_running = ezsp_running
    app._ctrl_event.clear()
    assert app.is_controller_running is False
    app._ctrl_event.set()
    assert app.is_controller_running is True
    assert ezsp_running.call_count == 1


def test_reset_frame(app):
    app._handle_reset_request = MagicMock(spec_set=app._handle_reset_request)
    app.ezsp_callback_handler("_reset_controller_application", (sentinel.error,))
    assert app._handle_reset_request.call_count == 1
    assert app._handle_reset_request.call_args[0][0] is sentinel.error


async def test_handle_reset_req(app):
    # no active reset task, no reset task preemption
    app._ctrl_event.set()
    assert app._reset_task is None
    reset_ctrl_mock = AsyncMock()
    app._reset_controller_loop = MagicMock(side_effect=reset_ctrl_mock)

    app._handle_reset_request(sentinel.error)

    assert asyncio.isfuture(app._reset_task)
    assert app._ctrl_event.is_set() is False
    await app._reset_task
    assert app._reset_controller_loop.call_count == 1


async def test_handle_reset_req_existing_preempt(app):
    # active reset task, preempt reset task
    app._ctrl_event.set()
    assert app._reset_task is None
    old_reset = asyncio.Future()
    app._reset_task = old_reset
    reset_ctrl_mock = AsyncMock()
    app._reset_controller_loop = MagicMock(side_effect=reset_ctrl_mock)

    app._handle_reset_request(sentinel.error)

    assert asyncio.isfuture(app._reset_task)
    await app._reset_task
    assert app._ctrl_event.is_set() is False
    assert app._reset_controller_loop.call_count == 1
    assert old_reset.done() is True
    assert old_reset.cancelled() is True


async def test_reset_controller_loop(app, monkeypatch):
    from bellows.zigbee import application

    monkeypatch.setattr(application, "RESET_ATTEMPT_BACKOFF_TIME", 0.1)
    app._watchdog_task = asyncio.Future()

    reset_succ_on_try = reset_call_count = 2

    async def reset_controller_mock():
        nonlocal reset_succ_on_try
        if reset_succ_on_try:
            reset_succ_on_try -= 1
            if reset_succ_on_try > 0:
                raise asyncio.TimeoutError
        return

    app._reset_controller = AsyncMock(side_effect=reset_controller_mock)

    await app._reset_controller_loop()

    assert app._watchdog_task.cancelled() is True
    assert app._reset_controller.call_count == reset_call_count
    assert app._reset_task is None


async def test_reset_controller_routine(app, monkeypatch):
    from bellows.zigbee import application

    monkeypatch.setattr(application, "RESET_ATTEMPT_BACKOFF_TIME", 0.01)

    # Fails to connect, then connects but fails to start network, then finally works
    app.connect = AsyncMock(side_effect=[RuntimeError("broken"), None, None])
    app.initialize = AsyncMock(side_effect=[asyncio.TimeoutError(), None])
    app._watchdog_task = MagicMock()

    await app._reset_controller_loop()
    assert app.connect.call_count == 3
    assert app.initialize.call_count == 2


@pytest.mark.parametrize("ezsp_version", (4, 7))
async def test_watchdog(app, monkeypatch, ezsp_version):
    from bellows.zigbee import application

    monkeypatch.setattr(application, "WATCHDOG_WAKE_PERIOD", 0.01)
    monkeypatch.setattr(application, "EZSP_COUNTERS_CLEAR_IN_WATCHDOG_PERIODS", 2)
    nop_success = 7
    app._ezsp.ezsp_version = ezsp_version

    async def nop_mock():
        nonlocal nop_success
        if nop_success:
            nop_success -= 1
            if nop_success % 3:
                raise EzspError
            else:
                return ([0] * 10,)
        raise asyncio.TimeoutError

    app._ezsp.nop = AsyncMock(side_effect=nop_mock)
    app._ezsp.readCounters = AsyncMock(side_effect=nop_mock)
    app._ezsp.readAndClearCounters = AsyncMock(side_effect=nop_mock)
    app._handle_reset_request = MagicMock()
    app._ctrl_event.set()

    await app._watchdog()

    if ezsp_version == 4:
        assert app._ezsp.nop.await_count > 4
    else:
        assert app._ezsp.readCounters.await_count >= 4

    assert app._handle_reset_request.call_count == 1


async def test_watchdog_counters(app, monkeypatch, caplog):
    from bellows.zigbee import application

    monkeypatch.setattr(application, "WATCHDOG_WAKE_PERIOD", 0.01)
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

    app._ezsp.readCounters = AsyncMock(side_effect=counters_mock)
    app._ezsp.nop = AsyncMock(side_effect=EzspError)
    app._handle_reset_request = MagicMock()
    app._ctrl_event.set()

    caplog.set_level(logging.DEBUG, "bellows.zigbee.application")
    await app._watchdog()
    assert app._ezsp.readCounters.await_count != 0
    assert app._ezsp.nop.await_count == 0

    # don't do counters on older firmwares
    app._ezsp.ezsp_version = 4
    app._ezsp.readCounters.reset_mock()
    await app._watchdog()
    assert app._ezsp.readCounters.await_count == 0
    assert app._ezsp.nop.await_count != 0


async def test_ezsp_value_counter(app, monkeypatch):
    from bellows.zigbee import application

    monkeypatch.setattr(application, "WATCHDOG_WAKE_PERIOD", 0.01)
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

    app._ezsp.readCounters = AsyncMock(side_effect=counters_mock)
    app._ezsp.nop = AsyncMock(side_effect=EzspError)
    app._ezsp.getValue = AsyncMock(
        return_value=(t.EzspStatus.ERROR_OUT_OF_MEMORY, b"\x20")
    )
    app._handle_reset_request = MagicMock()
    app._ctrl_event.set()

    await app._watchdog()
    assert app._ezsp.readCounters.await_count != 0
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
        app.state.counters[application.COUNTERS_CTRL][application.COUNTER_WATCHDOG] == 1
    )

    # Ezsp Value success
    app._ezsp.getValue = AsyncMock(return_value=(t.EzspStatus.SUCCESS, b"\x20"))
    nop_success = 3
    await app._watchdog()
    assert (
        app.state.counters[application.COUNTERS_EZSP][application.COUNTER_EZSP_BUFFERS]
        == 0x20
    )


async def test_watchdog_cancel(app, monkeypatch):
    """Coverage for watchdog cancellation."""

    from bellows.zigbee import application

    monkeypatch.setattr(application, "WATCHDOG_WAKE_PERIOD", 0.01)

    app._ezsp.readCounters = AsyncMock(side_effect=asyncio.CancelledError)

    with pytest.raises(asyncio.CancelledError):
        await app._watchdog()


async def test_shutdown(app):
    reset_f = asyncio.Future()
    watchdog_f = asyncio.Future()
    app._reset_task = reset_f
    app._watchdog_task = watchdog_f
    ezsp = app._ezsp

    await app.shutdown()
    assert app.controller_event.is_set() is False
    assert reset_f.done() is True
    assert reset_f.cancelled() is True
    assert watchdog_f.done() is True
    assert watchdog_f.cancelled() is True
    assert ezsp.close.call_count == 1


@pytest.fixture
def coordinator(app, ieee):
    dev = zigpy.device.Device(app, ieee, 0x0000)
    dev.endpoints[1] = bellows.zigbee.device.EZSPEndpoint(dev, 1)
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
    ret = await coordinator.endpoints[1].add_to_group(grp_id)
    assert ret == t.EmberStatus.SUCCESS
    assert mc.subscribe.call_count == 1
    assert mc.subscribe.call_args[0][0] == grp_id
    assert grp_id in coordinator.endpoints[1].member_of

    mc.reset_mock()
    ret = await coordinator.endpoints[1].add_to_group(grp_id)
    assert ret == t.EmberStatus.SUCCESS
    assert mc.subscribe.call_count == 0


async def test_ezsp_add_to_group_fail(coordinator):
    coordinator.application._multicast = MagicMock()
    mc = coordinator.application._multicast
    mc.subscribe = AsyncMock(return_value=t.EmberStatus.ERR_FATAL)

    grp_id = 0x2345
    assert grp_id not in coordinator.endpoints[1].member_of
    ret = await coordinator.add_to_group(grp_id)
    assert ret is None
    assert mc.subscribe.call_count == 1
    assert mc.subscribe.call_args[0][0] == grp_id
    assert grp_id not in coordinator.endpoints[1].member_of


async def test_ezsp_add_to_group_ep_fail(coordinator):
    coordinator.application._multicast = MagicMock()
    mc = coordinator.application._multicast
    mc.subscribe = AsyncMock(return_value=t.EmberStatus.ERR_FATAL)

    grp_id = 0x2345
    assert grp_id not in coordinator.endpoints[1].member_of
    ret = await coordinator.endpoints[1].add_to_group(grp_id)
    assert ret != t.EmberStatus.SUCCESS
    assert ret is not None
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
    ret = await coordinator.remove_from_group(grp_id)
    assert ret is None
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
    ret = await coordinator.endpoints[1].remove_from_group(grp_id)
    assert ret == t.EmberStatus.SUCCESS
    assert mc.unsubscribe.call_count == 1
    assert mc.unsubscribe.call_args[0][0] == grp_id
    assert grp_id not in coordinator.endpoints[1].member_of

    mc.reset_mock()
    ret = await coordinator.endpoints[1].remove_from_group(grp_id)
    assert ret == t.EmberStatus.SUCCESS
    assert mc.subscribe.call_count == 0


async def test_ezsp_remove_from_group_fail(coordinator):
    coordinator.application._multicast = MagicMock()
    mc = coordinator.application._multicast
    mc.unsubscribe = AsyncMock(return_value=t.EmberStatus.ERR_FATAL)

    grp_id = 0x2345
    grp = coordinator.application.groups.add_group(grp_id)
    grp.add_member(coordinator.endpoints[1])

    assert grp_id in coordinator.endpoints[1].member_of
    ret = await coordinator.remove_from_group(grp_id)
    assert ret is None
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
    ret = await coordinator.endpoints[1].remove_from_group(grp_id)
    assert ret != t.EmberStatus.SUCCESS
    assert ret is not None
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
    app.handle_relays.assert_called_once_with(nwk=sentinel.nwk, relays=None)


@patch.object(ezsp.EZSP, "version", new_callable=AsyncMock)
@patch("bellows.uart.connect", return_value=MagicMock(spec_set=uart.Gateway))
async def test_probe_success(mock_connect, mock_version):
    """Test device probing."""

    res = await ezsp.EZSP.probe(APP_CONFIG[config.CONF_DEVICE])
    assert res
    assert type(res) is dict
    assert mock_connect.call_count == 1
    assert mock_connect.await_count == 1
    assert mock_version.call_count == 1
    assert mock_connect.return_value.close.call_count == 1

    mock_connect.reset_mock()
    mock_version.reset_mock()
    mock_connect.reset_mock()
    res = await ezsp.EZSP.probe(APP_CONFIG[config.CONF_DEVICE])
    assert res
    assert type(res) is dict
    assert mock_connect.call_count == 1
    assert mock_connect.await_count == 1
    assert mock_version.call_count == 1
    assert mock_connect.return_value.close.call_count == 1


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
        assert lookup_mock.await_count == 1
        assert lookup_mock.await_args[0][0] is sentinel.nwk
        assert handle_join_mock.call_count == 0

    p1 = patch.object(
        app._ezsp,
        "lookupEui64ByNodeId",
        AsyncMock(return_value=(t.EmberStatus.SUCCESS, sentinel.ieee)),
    )
    with p1 as lookup_mock, p2 as handle_join_mock:
        await app._handle_no_such_device(sentinel.nwk)
        assert lookup_mock.await_count == 1
        assert lookup_mock.await_args[0][0] is sentinel.nwk
        assert handle_join_mock.call_count == 1
        assert handle_join_mock.call_args[0][0] == sentinel.nwk
        assert handle_join_mock.call_args[0][1] == sentinel.ieee


async def test_cleanup_tc_link_key(app):
    """Test cleaning up tc link key."""
    ezsp = app._ezsp
    ezsp.findKeyTableEntry = AsyncMock(side_effect=((0xFF,), (sentinel.index,)))
    ezsp.eraseKeyTableEntry = AsyncMock(return_value=(0x00,))

    await app.cleanup_tc_link_key(sentinel.ieee)
    assert ezsp.findKeyTableEntry.await_count == 1
    assert ezsp.findKeyTableEntry.await_args[0][0] is sentinel.ieee
    assert ezsp.eraseKeyTableEntry.await_count == 0
    assert ezsp.eraseKeyTableEntry.call_count == 0

    ezsp.findKeyTableEntry.reset_mock()
    await app.cleanup_tc_link_key(sentinel.ieee2)
    assert ezsp.findKeyTableEntry.await_count == 1
    assert ezsp.findKeyTableEntry.await_args[0][0] is sentinel.ieee2
    assert ezsp.eraseKeyTableEntry.await_count == 1
    assert ezsp.eraseKeyTableEntry.await_args[0][0] is sentinel.index


@patch("zigpy.application.ControllerApplication.permit", new=AsyncMock())
async def test_permit(app):
    """Test permit method."""
    ezsp = app._ezsp
    ezsp.addTransientLinkKey = AsyncMock(return_value=(t.EmberStatus.SUCCESS,))
    ezsp.pre_permit = AsyncMock()
    await app.permit(10, None)
    await asyncio.sleep(0)
    assert ezsp.addTransientLinkKey.await_count == 0
    assert ezsp.pre_permit.await_count == 1


@patch("bellows.zigbee.application.MFG_ID_RESET_DELAY", new=0.01)
@pytest.mark.parametrize(
    "ieee, expected_mfg_id",
    (
        ("54:ef:44:00:00:00:00:11", 0x115F),
        ("04:cf:8c:00:00:00:00:11", 0x115F),
        ("01:22:33:00:00:00:00:11", None),
    ),
)
async def test_set_mfg_id(ieee, expected_mfg_id, app, ezsp_mock):
    """Test setting manufacturer id based on IEEE address."""

    app.handle_join = MagicMock()
    app.cleanup_tc_link_key = AsyncMock()

    app.ezsp_callback_handler(
        "trustCenterJoinHandler",
        [
            1,
            t.EmberEUI64.convert(ieee),
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
            t.EmberEUI64.convert(ieee),
            t.EmberDeviceUpdate.STANDARD_SECURITY_UNSECURED_JOIN,
            t.EmberJoinDecision.NO_ACTION,
            sentinel.parent,
        ],
    )
    await asyncio.sleep(0.20)
    if expected_mfg_id is not None:
        assert ezsp_mock.setManufacturerCode.await_count == 2
        assert ezsp_mock.setManufacturerCode.await_args_list[0][0][0] == expected_mfg_id
        assert (
            ezsp_mock.setManufacturerCode.await_args_list[1][0][0]
            == bellows.zigbee.application.DEFAULT_MFG_ID
        )
    else:
        assert ezsp_mock.setManufacturerCode.await_count == 0


async def test_ensure_network_running_joined(app):
    ezsp = app._ezsp

    # Make initialization take two attempts
    ezsp.networkInit = AsyncMock(
        side_effect=[(t.EmberStatus.NETWORK_BUSY,), (t.EmberStatus.SUCCESS,)]
    )
    ezsp.networkState = AsyncMock(
        return_value=[ezsp.types.EmberNetworkStatus.JOINED_NETWORK]
    )

    rsp = await app._ensure_network_running()

    assert not rsp

    ezsp.networkInit.assert_not_called()


async def test_ensure_network_running_not_joined_failure(app):
    ezsp = app._ezsp
    ezsp.networkState = AsyncMock(
        return_value=[ezsp.types.EmberNetworkStatus.NO_NETWORK]
    )
    ezsp.networkInit = AsyncMock(return_value=[ezsp.types.EmberStatus.INVALID_CALL])

    with pytest.raises(zigpy.exceptions.ControllerException):
        await app._ensure_network_running()

    ezsp.networkState.assert_called_once()
    ezsp.networkInit.assert_called_once()


async def test_ensure_network_running_not_joined_success(app):
    ezsp = app._ezsp
    ezsp.networkState = AsyncMock(
        return_value=[ezsp.types.EmberNetworkStatus.NO_NETWORK]
    )
    ezsp.networkInit = AsyncMock(return_value=[ezsp.types.EmberStatus.SUCCESS])

    rsp = await app._ensure_network_running()
    assert rsp

    ezsp.networkState.assert_called_once()
    ezsp.networkInit.assert_called_once()


async def test_startup_coordinator_existing_groups_joined(app, ieee):
    """Coordinator joins groups loaded from the database."""

    app._ensure_network_running = AsyncMock()
    app._ezsp.update_policies = AsyncMock()
    app.load_network_info = AsyncMock()

    app._multicast = bellows.multicast.Multicast(app._ezsp)
    app.state.node_info.ieee = ieee

    db_device = app.add_device(ieee, 0x0000)
    db_ep = db_device.add_endpoint(1)

    app.groups.add_group(0x1234, "Group Name", suppress_event=True)
    app.groups[0x1234].add_member(db_ep, suppress_event=True)

    p1 = patch.object(bellows.multicast.Multicast, "_initialize")
    p2 = patch.object(bellows.multicast.Multicast, "subscribe")

    with p1 as p1, p2 as p2:
        await app.start_network()

    p2.assert_called_once_with(0x1234)


async def test_startup_new_coordinator_no_groups_joined(app, ieee):
    """Coordinator freshy added to the database has no groups to join."""

    app._ensure_network_running = AsyncMock()
    app._ezsp.update_policies = AsyncMock()
    app.load_network_info = AsyncMock()

    app._multicast = bellows.multicast.Multicast(app._ezsp)
    app.state.node_info.ieee = ieee

    p1 = patch.object(bellows.multicast.Multicast, "_initialize")
    p2 = patch.object(bellows.multicast.Multicast, "subscribe")

    with p1 as p1, p2 as p2:
        await app.start_network()

    p2.assert_not_called()


@pytest.mark.parametrize("enable_source_routing", [True, False])
async def test_startup_source_routing(make_app, ieee, enable_source_routing):
    """Existing relays are cleared on startup."""

    app = make_app({zigpy.config.CONF_SOURCE_ROUTING: enable_source_routing})

    app._ezsp.ezsp_version = 9
    app._ezsp.update_policies = AsyncMock()

    app._ensure_network_running = AsyncMock()
    app.load_network_info = AsyncMock()
    app.state.node_info.ieee = ieee

    app._multicast = bellows.multicast.Multicast(app._ezsp)
    app._multicast._initialize = AsyncMock()

    mock_device = MagicMock()
    mock_device.relays = sentinel.relays
    mock_device.initialize = AsyncMock()
    app.devices[0xABCD] = mock_device

    await app.start_network()

    if enable_source_routing:
        assert mock_device.relays is None
    else:
        assert mock_device.relays is sentinel.relays


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
