import asyncio

import asynctest
from asynctest import CoroutineMock, mock
import bellows.config as config
from bellows.exception import ControllerError, EzspError
import bellows.ezsp as ezsp
import bellows.ezsp.v4.types as t
import bellows.uart as uart
import bellows.zigbee.application
import pytest
import zigpy.config
from zigpy.device import Device
from zigpy.zcl.clusters import security

APP_CONFIG = {
    config.CONF_DEVICE: {
        config.CONF_DEVICE_PATH: "/dev/null",
        config.CONF_DEVICE_BAUDRATE: 115200,
    },
    config.CONF_PARAM_UNK_DEV: "yes",
    zigpy.config.CONF_DATABASE: None,
}


@pytest.fixture
def app(monkeypatch):
    ezsp = mock.MagicMock()
    ezsp.ezsp_version = 7
    ezsp.set_source_route = asynctest.CoroutineMock(
        return_value=[t.EmberStatus.SUCCESS]
    )
    type(ezsp).is_ezsp_running = mock.PropertyMock(return_value=True)
    config = bellows.zigbee.application.ControllerApplication.SCHEMA(APP_CONFIG)
    ctrl = bellows.zigbee.application.ControllerApplication(config)
    ctrl._ezsp = ezsp
    monkeypatch.setattr(bellows.zigbee.application, "APS_ACK_TIMEOUT", 0.1)
    ctrl._ctrl_event.set()
    ctrl._in_flight_msg = asyncio.Semaphore()
    ctrl.handle_message = mock.MagicMock()
    return ctrl


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


def get_mock_coro(return_value):
    async def mock_coro(*args, **kwargs):
        return return_value

    return mock.Mock(wraps=mock_coro)


def _test_startup(app, nwk_type, ieee, auto_form=False, init=0, ezsp_version=4):
    async def mockezsp(*args, **kwargs):
        return [0, nwk_type]

    async def mockinit(*args, **kwargs):
        return [init]

    app._in_flight_msg = None
    ezsp_mock = mock.MagicMock()
    type(ezsp_mock.return_value).ezsp_version = mock.PropertyMock(
        return_value=ezsp_version
    )
    ezsp_mock.initialize = CoroutineMock(return_value=ezsp_mock)
    ezsp_mock.connect = CoroutineMock()
    ezsp_mock.setConcentrator = CoroutineMock()
    ezsp_mock._command = mockezsp
    ezsp_mock.addEndpoint = mockezsp
    ezsp_mock.setConfigurationValue = mockezsp
    ezsp_mock.networkInit = mockinit
    ezsp_mock.getNetworkParameters = mockezsp
    ezsp_mock.setPolicy = mockezsp
    ezsp_mock.getMfgToken = CoroutineMock(return_value=(b"Some token\xff",))
    ezsp_mock.getNodeId = mockezsp
    ezsp_mock.getEui64.side_effect = CoroutineMock(return_value=[ieee])
    ezsp_mock.getValue = CoroutineMock(return_value=(0, b"\x01" * 6))
    ezsp_mock.leaveNetwork = mockezsp
    app.form_network = CoroutineMock()
    ezsp_mock.reset.side_effect = CoroutineMock()
    ezsp_mock.version.side_effect = CoroutineMock()
    ezsp_mock.getConfigurationValue.side_effect = CoroutineMock(return_value=(0, 1))
    ezsp_mock.update_policies = CoroutineMock()

    loop = asyncio.get_event_loop()
    p1 = mock.patch.object(bellows.ezsp, "EZSP", new=ezsp_mock)
    p2 = mock.patch.object(bellows.multicast.Multicast, "startup")

    with p1, p2 as multicast_mock:
        loop.run_until_complete(app.startup(auto_form=auto_form))
    assert multicast_mock.await_count == 1


def test_startup(app, ieee):
    return _test_startup(app, t.EmberNodeType.COORDINATOR, ieee)


def test_startup_ezsp_ver7(app, ieee):
    return _test_startup(app, t.EmberNodeType.COORDINATOR, ieee, ezsp_version=7)


def test_startup_no_status(app, ieee):
    with pytest.raises(Exception):
        return _test_startup(app, None, ieee, init=1)


def test_startup_no_status_form(app, ieee):
    return _test_startup(app, None, ieee, auto_form=True, init=1)


def test_startup_end(app, ieee):
    with pytest.raises(Exception):
        return _test_startup(app, t.EmberNodeType.SLEEPY_END_DEVICE, ieee)


def test_startup_end_form(app, ieee):
    return _test_startup(app, t.EmberNodeType.SLEEPY_END_DEVICE, ieee, True)


def test_form_network(app):
    f = asyncio.Future()
    f.set_result([0])
    app._ezsp.setInitialSecurityState.side_effect = [f]
    app._ezsp.formNetwork.side_effect = asyncio.coroutine(mock.MagicMock())
    app._ezsp.setValue.side_effect = asyncio.coroutine(mock.MagicMock())

    loop = asyncio.get_event_loop()
    loop.run_until_complete(app.form_network())


def _frame_handler(app, aps, ieee, src_ep, cluster=0, data=b"\x01\x00\x00"):
    if ieee not in app.devices:
        app.add_device(ieee, 3)
    aps.sourceEndpoint = src_ep
    aps.clusterId = cluster
    app.ezsp_callback_handler(
        "incomingMessageHandler", [None, aps, 1, 2, 3, 4, 5, data]
    )


@pytest.mark.asyncio
async def test_frame_handler_unknown_device(app, aps, ieee):
    app.handle_join = mock.MagicMock()
    app.add_device(ieee, 99)
    with mock.patch.object(app, "_handle_no_such_device") as no_dev_mock:
        _frame_handler(app, aps, ieee, 0)
        await asyncio.sleep(0)
    assert no_dev_mock.call_count == 1
    assert no_dev_mock.await_count == 1
    assert app.handle_message.call_count == 0
    assert app.handle_join.call_count == 0


def test_frame_handler(app, aps, ieee):
    app.handle_join = mock.MagicMock()
    data = b"\x18\x19\x22\xaa\x55"
    _frame_handler(app, aps, ieee, 0, data=data)
    assert app.handle_message.call_count == 1
    assert app.handle_message.call_args[0][5] is data
    assert app.handle_join.call_count == 0


def test_frame_handler_zdo_annce(app, aps, ieee):
    aps.destinationEndpoint = 0
    app.handle_join = mock.MagicMock()
    nwk = t.uint16_t(0xAA55)
    data = b"\x18" + nwk.serialize() + ieee.serialize()
    _frame_handler(app, aps, ieee, 0, cluster=0x0013, data=data)
    assert app.handle_message.call_count == 1
    assert app.handle_message.call_args[0][5] is data
    assert app.handle_join.call_count == 1
    assert app.handle_join.call_args[0][0] == nwk
    assert app.handle_join.call_args[0][1] == ieee


def test_send_failure(app, aps, ieee):
    req = app._pending[254] = mock.MagicMock()
    app.ezsp_callback_handler(
        "messageSentHandler", [None, 0xBEED, aps, 254, mock.sentinel.status, b""]
    )
    assert req.result.set_exception.call_count == 0
    assert req.result.set_result.call_count == 1
    assert req.result.set_result.call_args[0][0][0] is mock.sentinel.status


def test_dup_send_failure(app, aps, ieee):
    req = app._pending[254] = mock.MagicMock()
    req.result.set_result.side_effect = asyncio.InvalidStateError()
    app.ezsp_callback_handler(
        "messageSentHandler", [None, 0xBEED, aps, 254, mock.sentinel.status, b""]
    )
    assert req.result.set_exception.call_count == 0
    assert req.result.set_result.call_count == 1


def test_send_failure_unexpected(app, aps, ieee):
    app.ezsp_callback_handler("messageSentHandler", [None, 0xBEED, aps, 257, 1, b""])


def test_send_success(app, aps, ieee):
    req = app._pending[253] = mock.MagicMock()
    app.ezsp_callback_handler(
        "messageSentHandler", [None, 0xBEED, aps, 253, mock.sentinel.success, b""]
    )
    assert req.result.set_exception.call_count == 0
    assert req.result.set_result.call_count == 1
    assert req.result.set_result.call_args[0][0][0] is mock.sentinel.success


def test_unexpected_send_success(app, aps, ieee):
    app.ezsp_callback_handler("messageSentHandler", [None, 0xBEED, aps, 253, 0, b""])


def test_dup_send_success(app, aps, ieee):
    req = app._pending[253] = mock.MagicMock()
    req.result.set_result.side_effect = asyncio.InvalidStateError()
    app.ezsp_callback_handler("messageSentHandler", [None, 0xBEED, aps, 253, 0, b""])
    assert req.result.set_exception.call_count == 0
    assert req.result.set_result.call_count == 1


def test_join_handler(app, ieee):
    # Calls device.initialize, leaks a task
    app.handle_join = mock.MagicMock()
    app.ezsp_callback_handler(
        "trustCenterJoinHandler", [1, ieee, None, None, mock.sentinel.parent]
    )
    assert ieee not in app.devices
    assert app.handle_join.call_count == 1
    assert app.handle_join.call_args[0][0] == 1
    assert app.handle_join.call_args[0][1] == ieee
    assert app.handle_join.call_args[0][2] is mock.sentinel.parent


def test_leave_handler(app, ieee):
    app.devices[ieee] = mock.MagicMock()
    app.ezsp_callback_handler(
        "trustCenterJoinHandler", [1, ieee, t.EmberDeviceUpdate.DEVICE_LEFT, None, None]
    )
    assert ieee in app.devices


def test_force_remove(app, ieee):
    app._ezsp.removeDevice.side_effect = asyncio.coroutine(mock.MagicMock())
    dev = mock.MagicMock()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(app.force_remove(dev))


def test_sequence(app):
    for i in range(1000):
        seq = app.get_sequence()
        assert seq >= 0
        assert seq < 256


def test_permit(app):
    app.permit_ncp(60)
    assert app._ezsp.permitJoining.call_count == 1


def test_permit_with_key(app):
    app._ezsp.addTransientLinkKey = get_mock_coro([0])
    app._ezsp.setPolicy = get_mock_coro([0])
    app.permit = get_mock_coro([0])

    loop = asyncio.get_event_loop()
    loop.run_until_complete(
        app.permit_with_key(
            bytes([1, 2, 3, 4, 5, 6, 7, 8]),
            bytes([0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77, 0x88, 0x4A, 0xF7]),
            60,
        )
    )

    assert app._ezsp.addTransientLinkKey.call_count == 1
    assert app.permit.call_count == 1


def test_permit_with_key_ieee(app, ieee):
    app._ezsp.addTransientLinkKey = get_mock_coro([0])
    app._ezsp.setPolicy = get_mock_coro([0])
    app.permit = get_mock_coro([0])

    loop = asyncio.get_event_loop()
    loop.run_until_complete(
        app.permit_with_key(
            ieee,
            bytes([0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77, 0x88, 0x4A, 0xF7]),
            60,
        )
    )

    assert app._ezsp.addTransientLinkKey.call_count == 1
    assert app.permit.call_count == 1


def test_permit_with_key_invalid_install_code(app, ieee):
    loop = asyncio.get_event_loop()

    with pytest.raises(Exception):
        loop.run_until_complete(
            app.permit_with_key(
                ieee, bytes([0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77, 0x88]), 60
            )
        )


def test_permit_with_key_failed_add_key(app, ieee):
    app._ezsp.addTransientLinkKey = get_mock_coro([1, 1])

    loop = asyncio.get_event_loop()
    with pytest.raises(Exception):
        loop.run_until_complete(
            app.permit_with_key(
                ieee,
                bytes([0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77, 0x88, 0x4A, 0xF7]),
                60,
            )
        )


def test_permit_with_key_failed_set_policy(app, ieee):
    app._ezsp.addTransientLinkKey = get_mock_coro([0])
    app._ezsp.setPolicy = get_mock_coro([1])

    loop = asyncio.get_event_loop()
    with pytest.raises(Exception):
        loop.run_until_complete(
            app.permit_with_key(
                ieee,
                bytes([0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77, 0x88, 0x4A, 0xF7]),
                60,
            )
        )


@pytest.mark.asyncio
async def _request(
    app,
    send_status=0,
    send_ack_received=True,
    send_ack_success=True,
    ezsp_operational=True,
    is_end_device=False,
    relays=None,
    **kwargs
):
    async def mocksend(method, nwk, aps_frame, seq, data):
        if not ezsp_operational:
            raise EzspError
        req = app._pending[seq]
        if send_ack_received:
            if send_ack_success:
                req.result.set_result((0, "success"))
            else:
                req.result.set_result((102, "failure"))
        return [send_status, "send message"]

    app._ezsp.sendUnicast = mock.CoroutineMock(side_effect=mocksend)
    app._ezsp.setExtendedTimeout = mock.CoroutineMock()
    device = mock.MagicMock()
    device.relays = relays
    device.node_desc.is_end_device = is_end_device
    res = await app.request(device, 9, 8, 7, 6, 5, b"", **kwargs)
    assert len(app._pending) == 0
    return res


@pytest.mark.asyncio
async def test_request(app):
    res = await _request(app)
    assert res[0] == 0


@pytest.mark.asyncio
async def test_request_ack_timeout(app, aps):
    with pytest.raises(asyncio.TimeoutError):
        await _request(app, send_ack_received=False)


@pytest.mark.asyncio
async def test_request_send_unicast_fail(app):
    res = await _request(app, send_status=2)
    assert res[0] != 0


@pytest.mark.asyncio
async def test_request_ezsp_failed(app):
    with pytest.raises(EzspError):
        await _request(app, ezsp_operational=False)
    assert len(app._pending) == 0


@pytest.mark.asyncio
async def test_request_reply_timeout_send_timeout(app):
    with pytest.raises(asyncio.TimeoutError):
        await _request(app, send_ack_received=False)
    assert app._pending == {}


@pytest.mark.asyncio
async def test_request_ctrl_not_running(app):
    app._ctrl_event.clear()
    with pytest.raises(ControllerError):
        await _request(app)


@pytest.mark.asyncio
async def test_request_use_ieee(app):
    res = await _request(app, use_ieee=True)
    assert res[0] == 0


@pytest.mark.asyncio
async def test_request_extended_timeout(app):
    res = await _request(app)
    assert res[0] == 0
    assert app._ezsp.setExtendedTimeout.call_count == 0

    res = await _request(app, is_end_device=None)
    assert res[0] == 0
    assert app._ezsp.setExtendedTimeout.call_count == 1
    assert app._ezsp.setExtendedTimeout.call_args[0][1] is True

    res = await _request(app, is_end_device=True)
    assert res[0] == 0
    assert app._ezsp.setExtendedTimeout.call_count == 1
    assert app._ezsp.setExtendedTimeout.call_args[0][1] is True


@pytest.mark.parametrize("relays", [None, [], [0x1234]])
@pytest.mark.asyncio
async def test_request_src_rtg_not_enabled(relays, app):
    app.use_source_routing = False
    res = await _request(app, relays=relays)
    assert res[0] == 0
    assert app._ezsp.set_source_route.await_count == 0
    assert app._ezsp.sendUnicast.await_count == 1
    assert (
        app._ezsp.sendUnicast.call_args[0][2].options
        & t.EmberApsOption.APS_OPTION_ENABLE_ROUTE_DISCOVERY
    )


@pytest.mark.parametrize("relays", [[], [0x1234]])
@pytest.mark.asyncio
async def test_request_src_rtg_success(relays, app):
    app.use_source_routing = True
    res = await _request(app, relays=relays)
    assert res[0] == 0
    assert app._ezsp.set_source_route.await_count == 1
    assert app._ezsp.sendUnicast.await_count == 1
    assert (
        not app._ezsp.sendUnicast.call_args[0][2].options
        & t.EmberApsOption.APS_OPTION_ENABLE_ROUTE_DISCOVERY
    )


@pytest.mark.parametrize("relays", [[], [0x1234]])
@pytest.mark.asyncio
async def test_request_src_rtg_fail(relays, app):
    app.use_source_routing = True
    app._ezsp.set_source_route.return_value = [1]
    res = await _request(app, relays=relays)
    assert res[0] == 0
    assert app._ezsp.set_source_route.await_count == 1
    assert app._ezsp.sendUnicast.await_count == 1
    assert (
        app._ezsp.sendUnicast.call_args[0][2].options
        & t.EmberApsOption.APS_OPTION_ENABLE_ROUTE_DISCOVERY
    )


@pytest.mark.parametrize(
    "send_status, sleep_count, send_unicast_count", ((0, 0, 1), (114, 3, 4), (2, 0, 1))
)
@pytest.mark.asyncio
async def test_request_max_message_limit(
    send_status, sleep_count, send_unicast_count, app
):
    async def mocksend(method, nwk, aps_frame, seq, data):
        if send_status == t.EmberStatus.SUCCESS:
            req = app._pending[seq]
            req.result.set_result((0, "success"))
        return [send_status, "send message"]

    app._ezsp.sendUnicast = mock.CoroutineMock(side_effect=mocksend)
    app._ezsp.setExtendedTimeout = mock.CoroutineMock()
    device = mock.MagicMock()
    device.relays = []
    device.node_desc.is_end_device = False

    with mock.patch("asyncio.sleep") as sleep_mock:
        await app.request(device, 9, 8, 7, 6, 5, b"", expect_reply=False)
    assert sleep_mock.await_count == sleep_count
    assert app._ezsp.sendUnicast.await_count == send_unicast_count


@pytest.mark.asyncio
async def _test_broadcast(
    app, broadcast_success=True, send_timeout=False, ezsp_running=True
):
    (profile, cluster, src_ep, dst_ep, grpid, radius, tsn, data) = (
        0x260,
        1,
        2,
        3,
        0x0100,
        0x06,
        210,
        b"\x02\x01\x00",
    )

    async def mock_send(nwk, aps, radius, tsn, data):
        if not ezsp_running:
            raise EzspError
        if broadcast_success:
            if not send_timeout:
                app._pending[tsn].result.set_result((0, "sendBroadcast failure"))
            return [0]
        else:
            return [t.EmberStatus.ERR_FATAL]

    app._ezsp.sendBroadcast.side_effect = mock_send
    app.get_sequence = mock.MagicMock(return_value=mock.sentinel.msg_tag)

    res = await app.broadcast(
        profile, cluster, src_ep, dst_ep, grpid, radius, tsn, data
    )
    assert app._ezsp.sendBroadcast.call_count == 1
    assert app._ezsp.sendBroadcast.call_args[0][2] == radius
    assert app._ezsp.sendBroadcast.call_args[0][3] == mock.sentinel.msg_tag
    assert app._ezsp.sendBroadcast.call_args[0][4] == data
    assert len(app._pending) == 0
    return res


@pytest.mark.asyncio
async def test_broadcast(app):
    await _test_broadcast(app)
    assert len(app._pending) == 0


@pytest.mark.asyncio
async def test_broadcast_fail(app):
    res = await _test_broadcast(app, broadcast_success=False)
    assert res[0] != 0
    assert len(app._pending) == 0


@pytest.mark.asyncio
async def test_broadcast_send_timeout(app):
    with pytest.raises(asyncio.TimeoutError):
        await _test_broadcast(app, send_timeout=True)
    assert len(app._pending) == 0


@pytest.mark.asyncio
async def test_broadcast_ezsp_fail(app):
    with pytest.raises(EzspError):
        await _test_broadcast(app, ezsp_running=False)
    assert len(app._pending) == 0


@pytest.mark.asyncio
async def test_broadcast_ctrl_not_running(app):
    app._ctrl_event.clear()
    (profile, cluster, src_ep, dst_ep, grpid, radius, tsn, data) = (
        0x260,
        1,
        2,
        3,
        0x0100,
        0x06,
        210,
        b"\x02\x01\x00",
    )

    async def mocksend(nwk, aps, radiusm, tsn, data):
        raise EzspError

    app._ezsp.sendBroadcast.side_effect = mocksend

    with pytest.raises(ControllerError):
        await app.broadcast(profile, cluster, src_ep, dst_ep, grpid, radius, tsn, data)
        assert len(app._pending) == 0
        assert app._ezsp.sendBroadcast.call_count == 0


def test_is_controller_running(app):
    ezsp_running = mock.PropertyMock(return_value=False)
    type(app._ezsp).is_ezsp_running = ezsp_running
    app._ctrl_event.clear()
    assert app.is_controller_running is False
    app._ctrl_event.set()
    assert app.is_controller_running is False
    assert ezsp_running.call_count == 1

    ezsp_running = mock.PropertyMock(return_value=True)
    type(app._ezsp).is_ezsp_running = ezsp_running
    app._ctrl_event.clear()
    assert app.is_controller_running is False
    app._ctrl_event.set()
    assert app.is_controller_running is True
    assert ezsp_running.call_count == 1


def test_reset_frame(app):
    app._handle_reset_request = mock.MagicMock(spec_set=app._handle_reset_request)
    app.ezsp_callback_handler("_reset_controller_application", (mock.sentinel.error,))
    assert app._handle_reset_request.call_count == 1
    assert app._handle_reset_request.call_args[0][0] is mock.sentinel.error


@pytest.mark.asyncio
async def test_handle_reset_req(app):
    # no active reset task, no reset task preemption
    app._ctrl_event.set()
    assert app._reset_task is None
    reset_ctrl_mock = asyncio.coroutine(mock.MagicMock())
    app._reset_controller_loop = mock.MagicMock(side_effect=reset_ctrl_mock)

    app._handle_reset_request(mock.sentinel.error)

    assert asyncio.isfuture(app._reset_task)
    assert app._ctrl_event.is_set() is False
    await app._reset_task
    assert app._reset_controller_loop.call_count == 1


@pytest.mark.asyncio
async def test_handle_reset_req_existing_preempt(app):
    # active reset task, preempt reset task
    app._ctrl_event.set()
    assert app._reset_task is None
    old_reset = asyncio.Future()
    app._reset_task = old_reset
    reset_ctrl_mock = asyncio.coroutine(mock.MagicMock())
    app._reset_controller_loop = mock.MagicMock(side_effect=reset_ctrl_mock)

    app._handle_reset_request(mock.sentinel.error)

    assert asyncio.isfuture(app._reset_task)
    await app._reset_task
    assert app._ctrl_event.is_set() is False
    assert app._reset_controller_loop.call_count == 1
    assert old_reset.done() is True
    assert old_reset.cancelled() is True


@pytest.mark.asyncio
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

    app._reset_controller = mock.MagicMock(side_effect=reset_controller_mock)

    await app._reset_controller_loop()

    assert app._watchdog_task.cancelled() is True
    assert app._reset_controller.call_count == reset_call_count
    assert app._reset_task is None


@pytest.mark.asyncio
async def test_reset_controller_routine(app):
    reconn_mock = asyncio.coroutine(mock.MagicMock())
    app._ezsp.reconnect = mock.MagicMock(side_effect=reconn_mock)
    startup_mock = asyncio.coroutine(mock.MagicMock())
    app.startup = mock.MagicMock(side_effect=startup_mock)

    await app._reset_controller()

    assert app._ezsp.close.call_count == 1
    assert app.startup.call_count == 1


@pytest.mark.asyncio
async def test_watchdog(app, monkeypatch):
    from bellows.zigbee import application

    monkeypatch.setattr(application, "WATCHDOG_WAKE_PERIOD", 0.1)
    nop_success = 3

    async def nop_mock():
        nonlocal nop_success
        if nop_success:
            nop_success -= 1
            if nop_success % 2:
                raise EzspError
            else:
                return
        raise asyncio.TimeoutError

    app._ezsp.nop = mock.MagicMock(side_effect=nop_mock)
    app._handle_reset_request = mock.MagicMock()
    app._ctrl_event.set()

    await app._watchdog()

    assert app._ezsp.nop.call_count > 4
    assert app._handle_reset_request.call_count == 1


@pytest.mark.asyncio
async def test_shutdown(app):
    reset_f = asyncio.Future()
    watchdog_f = asyncio.Future()
    app._reset_task = reset_f
    app._watchdog_task = watchdog_f

    await app.shutdown()
    assert app.controller_event.is_set() is False
    assert reset_f.done() is True
    assert reset_f.cancelled() is True
    assert watchdog_f.done() is True
    assert watchdog_f.cancelled() is True
    assert app._ezsp.close.call_count == 1


@pytest.fixture
def coordinator(app, ieee):
    dev = Device(app, ieee, 0x0000)
    ep = dev.add_endpoint(1)
    ep.profile_id = 0x0104
    ep.device_type = 0xBEEF
    ep.add_output_cluster(security.IasZone.cluster_id)
    return bellows.zigbee.application.EZSPCoordinator(app, ieee, 0x0000, dev)


@pytest.mark.asyncio
async def test_ezsp_add_to_group(coordinator):
    coordinator.application._multicast = mock.MagicMock()
    mc = coordinator.application._multicast
    mc.subscribe.side_effect = asyncio.coroutine(
        mock.MagicMock(return_value=t.EmberStatus.SUCCESS)
    )

    grp_id = 0x2345
    assert grp_id not in coordinator.endpoints[1].member_of
    ret = await coordinator.add_to_group(grp_id)
    assert ret is None
    assert mc.subscribe.call_count == 1
    assert mc.subscribe.call_args[0][0] == grp_id
    assert grp_id in coordinator.endpoints[1].member_of


@pytest.mark.asyncio
async def test_ezsp_add_to_group_ep(coordinator):
    coordinator.application._multicast = mock.MagicMock()
    mc = coordinator.application._multicast
    mc.subscribe.side_effect = asyncio.coroutine(
        mock.MagicMock(return_value=t.EmberStatus.SUCCESS)
    )

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


@pytest.mark.asyncio
async def test_ezsp_add_to_group_fail(coordinator):
    coordinator.application._multicast = mock.MagicMock()
    mc = coordinator.application._multicast
    mc.subscribe.side_effect = asyncio.coroutine(
        mock.MagicMock(return_value=t.EmberStatus.ERR_FATAL)
    )

    grp_id = 0x2345
    assert grp_id not in coordinator.endpoints[1].member_of
    ret = await coordinator.add_to_group(grp_id)
    assert ret is None
    assert mc.subscribe.call_count == 1
    assert mc.subscribe.call_args[0][0] == grp_id
    assert grp_id not in coordinator.endpoints[1].member_of


@pytest.mark.asyncio
async def test_ezsp_add_to_group_ep_fail(coordinator):
    coordinator.application._multicast = mock.MagicMock()
    mc = coordinator.application._multicast
    mc.subscribe.side_effect = asyncio.coroutine(
        mock.MagicMock(return_value=t.EmberStatus.ERR_FATAL)
    )

    grp_id = 0x2345
    assert grp_id not in coordinator.endpoints[1].member_of
    ret = await coordinator.endpoints[1].add_to_group(grp_id)
    assert ret != t.EmberStatus.SUCCESS
    assert ret is not None
    assert mc.subscribe.call_count == 1
    assert mc.subscribe.call_args[0][0] == grp_id
    assert grp_id not in coordinator.endpoints[1].member_of


@pytest.mark.asyncio
async def test_ezsp_remove_from_group(coordinator):
    coordinator.application._multicast = mock.MagicMock()
    mc = coordinator.application._multicast
    mc.unsubscribe.side_effect = asyncio.coroutine(
        mock.MagicMock(return_value=t.EmberStatus.SUCCESS)
    )

    grp_id = 0x2345
    grp = coordinator.application.groups.add_group(grp_id)
    grp.add_member(coordinator.endpoints[1])

    assert grp_id in coordinator.endpoints[1].member_of
    ret = await coordinator.remove_from_group(grp_id)
    assert ret is None
    assert mc.unsubscribe.call_count == 1
    assert mc.unsubscribe.call_args[0][0] == grp_id
    assert grp_id not in coordinator.endpoints[1].member_of


@pytest.mark.asyncio
async def test_ezsp_remove_from_group_ep(coordinator):
    coordinator.application._multicast = mock.MagicMock()
    mc = coordinator.application._multicast
    mc.unsubscribe.side_effect = asyncio.coroutine(
        mock.MagicMock(return_value=t.EmberStatus.SUCCESS)
    )

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


@pytest.mark.asyncio
async def test_ezsp_remove_from_group_fail(coordinator):
    coordinator.application._multicast = mock.MagicMock()
    mc = coordinator.application._multicast
    mc.unsubscribe.side_effect = asyncio.coroutine(
        mock.MagicMock(return_value=t.EmberStatus.ERR_FATAL)
    )

    grp_id = 0x2345
    grp = coordinator.application.groups.add_group(grp_id)
    grp.add_member(coordinator.endpoints[1])

    assert grp_id in coordinator.endpoints[1].member_of
    ret = await coordinator.remove_from_group(grp_id)
    assert ret is None
    assert mc.unsubscribe.call_count == 1
    assert mc.unsubscribe.call_args[0][0] == grp_id


@pytest.mark.asyncio
async def test_ezsp_remove_from_group_fail_ep(coordinator):
    coordinator.application._multicast = mock.MagicMock()
    mc = coordinator.application._multicast
    mc.unsubscribe.side_effect = asyncio.coroutine(
        mock.MagicMock(return_value=t.EmberStatus.ERR_FATAL)
    )

    grp_id = 0x2345
    grp = coordinator.application.groups.add_group(grp_id)
    grp.add_member(coordinator.endpoints[1])

    assert grp_id in coordinator.endpoints[1].member_of
    ret = await coordinator.endpoints[1].remove_from_group(grp_id)
    assert ret != t.EmberStatus.SUCCESS
    assert ret is not None
    assert mc.unsubscribe.call_count == 1
    assert mc.unsubscribe.call_args[0][0] == grp_id


@pytest.mark.asyncio
async def _mrequest(
    app,
    send_success=True,
    send_ack_received=True,
    send_ack_success=True,
    ezsp_operational=True,
    **kwargs
):
    async def mocksend(method, nwk, aps_frame, seq, data):
        if not ezsp_operational:
            raise EzspError
        req = app._pending[seq]
        if send_ack_received:
            if send_ack_success:
                req.result.set_result((0, "success"))
            else:
                req.result.set_result((102, "failure"))
        if send_success:
            return [0]
        return [2]

    app._ezsp.sendMulticast = mocksend
    res = await app.mrequest(0x1234, 9, 8, 7, 6, b"", **kwargs)
    assert len(app._pending) == 0
    return res


@pytest.mark.asyncio
async def test_mrequest(app):
    res = await _mrequest(app)
    assert res[0] == 0


@pytest.mark.asyncio
async def test_mrequest_ack_timeout(app, aps):
    with pytest.raises(asyncio.TimeoutError):
        await _mrequest(app, send_ack_received=False)


@pytest.mark.asyncio
async def test_mrequest_send_unicast_fail(app):
    res = await _mrequest(app, send_success=False)
    assert res[0] != 0


@pytest.mark.asyncio
async def test_mrequest_ezsp_failed(app):
    with pytest.raises(EzspError):
        await _mrequest(app, ezsp_operational=False)
    assert len(app._pending) == 0


@pytest.mark.asyncio
async def test_mrequest_send_timeout(app):
    with pytest.raises(asyncio.TimeoutError):
        await _mrequest(app, send_ack_received=False)
    assert app._pending == {}


@pytest.mark.asyncio
async def test_mrequest_ctrl_not_running(app):
    app._ctrl_event.clear()
    with pytest.raises(ControllerError):
        await _mrequest(app)


def test_handle_route_record(app):
    """Test route record handling for an existing device."""
    s = mock.sentinel
    dev = mock.MagicMock()
    app.handle_join = mock.MagicMock()
    app.get_device = mock.MagicMock(return_value=dev)
    app.ezsp_callback_handler(
        "incomingRouteRecordHandler", [s.nwk, s.ieee, s.lqi, s.rssi, s.relays]
    )
    assert dev.relays is s.relays
    assert app.handle_join.call_count == 0


def test_handle_route_record_unkn(app):
    """Test route record handling for an unknown device."""
    s = mock.sentinel
    app.handle_join = mock.MagicMock()
    app.get_device = mock.MagicMock(side_effect=KeyError)
    app.ezsp_callback_handler(
        "incomingRouteRecordHandler", [s.nwk, s.ieee, s.lqi, s.rssi, s.relays]
    )
    assert app.handle_join.call_count == 1
    assert app.handle_join.call_args[0][0] is s.nwk
    assert app.handle_join.call_args[0][1] is s.ieee


def test_handle_route_error(app):
    """Test route error handler."""
    dev = mock.MagicMock()
    dev.relays = mock.sentinel.old_relays
    app.get_device = mock.MagicMock(return_value=dev)

    app.ezsp_callback_handler(
        "incomingRouteErrorHandler", [mock.sentinel.status, mock.sentinel.nwk]
    )
    assert dev.relays is None

    app.get_device = mock.MagicMock(side_effect=KeyError)
    app.ezsp_callback_handler(
        "incomingRouteErrorHandler", [mock.sentinel.status, mock.sentinel.nwk]
    )


@pytest.mark.parametrize(
    "config, result",
    [
        ({}, False),
        ({"wrong_key": True}, False),
        ({"source_routing": False}, False),
        ({"source_routing": True}, True),
        ({"source_routing": "on"}, True),
    ],
)
def test_src_rtg_config(config, result):
    """Test src routing configuration parameter."""
    app_cfg = bellows.zigbee.application.ControllerApplication.SCHEMA(APP_CONFIG)
    ctrl = bellows.zigbee.application.ControllerApplication(app_cfg)
    assert ctrl.use_source_routing is False

    app_cfg = bellows.zigbee.application.ControllerApplication.SCHEMA(
        {**APP_CONFIG, **config}
    )
    ctrl = bellows.zigbee.application.ControllerApplication(config=app_cfg)
    assert ctrl.use_source_routing is result


@pytest.mark.asyncio
@mock.patch.object(ezsp.EZSP, "reset", new_callable=CoroutineMock)
@mock.patch.object(uart, "connect")
async def test_probe_success(mock_connect, mock_reset):
    """Test device probing."""

    res = await ezsp.EZSP.probe(APP_CONFIG[config.CONF_DEVICE])
    assert res is True
    assert mock_connect.call_count == 1
    assert mock_connect.await_count == 1
    assert mock_reset.call_count == 1
    assert mock_connect.return_value.close.call_count == 1

    mock_connect.reset_mock()
    mock_reset.reset_mock()
    mock_connect.reset_mock()
    res = await ezsp.EZSP.probe(APP_CONFIG[config.CONF_DEVICE])
    assert res is True
    assert mock_connect.call_count == 1
    assert mock_connect.await_count == 1
    assert mock_reset.call_count == 1
    assert mock_connect.return_value.close.call_count == 1


def test_handle_id_conflict(app, ieee):
    """Test handling of an ID confict report."""
    nwk = t.EmberNodeId(0x1234)
    app.add_device(ieee, nwk)
    app.handle_leave = mock.MagicMock()

    app.ezsp_callback_handler("idConflictHandler", [nwk + 1])
    assert app.handle_leave.call_count == 0

    app.ezsp_callback_handler("idConflictHandler", [nwk])
    assert app.handle_leave.call_count == 1
    assert app.handle_leave.call_args[0][0] == nwk


@pytest.mark.asyncio
async def test_handle_no_such_device(app, ieee):
    """Test handling of an unknown device IEEE lookup."""

    p1 = mock.patch.object(
        app._ezsp,
        "lookupEui64ByNodeId",
        CoroutineMock(return_value=(t.EmberStatus.ERR_FATAL, ieee)),
    )
    p2 = mock.patch.object(app, "handle_join")
    with p1 as lookup_mock, p2 as handle_join_mock:
        await app._handle_no_such_device(mock.sentinel.nwk)
        assert lookup_mock.await_count == 1
        assert lookup_mock.await_args[0][0] is mock.sentinel.nwk
        assert handle_join_mock.call_count == 0

    p1 = mock.patch.object(
        app._ezsp,
        "lookupEui64ByNodeId",
        CoroutineMock(return_value=(t.EmberStatus.SUCCESS, mock.sentinel.ieee)),
    )
    with p1 as lookup_mock, p2 as handle_join_mock:
        await app._handle_no_such_device(mock.sentinel.nwk)
        assert lookup_mock.await_count == 1
        assert lookup_mock.await_args[0][0] is mock.sentinel.nwk
        assert handle_join_mock.call_count == 1
        assert handle_join_mock.call_args[0][0] == mock.sentinel.nwk
        assert handle_join_mock.call_args[0][1] == mock.sentinel.ieee
