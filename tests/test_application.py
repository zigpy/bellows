import asyncio
from unittest import mock

import pytest

import bellows.types as t
import bellows.zigbee.application
from bellows.exception import ControllerError, EzspError
from zigpy.device import Device
from zigpy.exceptions import DeliveryError
from zigpy.zcl.clusters import security


@pytest.fixture
def app(monkeypatch):
    ezsp = mock.MagicMock()
    type(ezsp).is_ezsp_running = mock.PropertyMock(return_value=True)
    ctrl = bellows.zigbee.application.ControllerApplication(ezsp)
    monkeypatch.setattr(bellows.zigbee.application, 'APS_ACK_TIMEOUT', 0.1)
    monkeypatch.setattr(bellows.zigbee.application, 'APS_REPLY_TIMEOUT', 0.1)
    monkeypatch.setattr(bellows.zigbee.application,
                        'APS_REPLY_TIMEOUT_EXTENDED', 0.1)
    ctrl._ctrl_event.set()
    ctrl._in_flight_msg = asyncio.Semaphore()
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


def _test_startup(app, nwk_type, ieee, auto_form=False, init=0):
    async def mockezsp(*args, **kwargs):
        return [0, nwk_type]

    async def mockinit(*args, **kwargs):
        return [init]

    app._in_flight_msg = None
    app._ezsp._command = mockezsp
    app._ezsp.addEndpoint = mockezsp
    app._ezsp.setConfigurationValue = mockezsp
    app._ezsp.networkInit = mockinit
    app._ezsp.getNetworkParameters = mockezsp
    app._ezsp.setPolicy = mockezsp
    app._ezsp.getNodeId = mockezsp
    app._ezsp.getEui64.side_effect = asyncio.coroutine(
        mock.MagicMock(return_value=[ieee]))
    app._ezsp.leaveNetwork = mockezsp
    app.form_network = mock.MagicMock(side_effect=asyncio.coroutine(mock.MagicMock()))
    app._ezsp.reset.side_effect = asyncio.coroutine(mock.MagicMock())
    app._ezsp.version.side_effect = asyncio.coroutine(mock.MagicMock())
    app._ezsp.getConfigurationValue.side_effect = asyncio.coroutine(
        mock.MagicMock(return_value=(0, 1)))
    app.multicast._initialize = mockezsp

    loop = asyncio.get_event_loop()
    loop.run_until_complete(app.startup(auto_form=auto_form))


def test_startup(app, ieee):
    return _test_startup(app, t.EmberNodeType.COORDINATOR, ieee)


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


def _frame_handler(app, aps, ieee, endpoint, deserialize, cluster=0):
    if ieee not in app.devices:
        app.add_device(ieee, 3)
    aps.sourceEndpoint = endpoint
    aps.clusterId = cluster
    app.deserialize = deserialize
    app.ezsp_callback_handler(
        'incomingMessageHandler',
        [None, aps, 1, 2, 3, 4, 5, b'\x01\x00\x00']
    )


def test_frame_handler_unknown_device(app, aps, ieee):
    app.add_device(ieee, 99)
    deserialize = mock.MagicMock()
    _frame_handler(app, aps, ieee, 0, deserialize)
    assert deserialize.call_count == 0


def test_frame_handler_zdo(app, aps, ieee):
    _frame_handler(app, aps, ieee, 0, mock.MagicMock(return_value=(1, 1, False, [1])))


def test_frame_handler_zdo_reply(app, aps, ieee):
    request = app._pending[1] = mock.MagicMock()
    deserialize = mock.MagicMock(return_value=(1, 1, True, []))
    _frame_handler(app, aps, ieee, 0, deserialize, 0x8000)
    assert request.send.set_result.call_count == 0
    assert request.reply.set_result.call_count == 1


def test_frame_handler_dup_zdo_reply(app, aps, ieee):
    req = app._pending[1] = mock.MagicMock()
    req.reply.set_result.side_effect = asyncio.futures.InvalidStateError()
    deserialize = mock.MagicMock(return_value=(1, 1, True, []))
    _frame_handler(app, aps, ieee, 0, deserialize, 0x8000)
    assert req.send.set_result.call_count == 0
    assert req.reply.set_result.call_count == 1


def test_frame_handler_zdo_reply_unknown(app, aps, ieee):
    app.handle_message = mock.MagicMock()
    deserialize = mock.MagicMock(return_value=(1, 1, True, []))
    _frame_handler(app, aps, ieee, 0, deserialize, 0x8000)
    # An unknown reply drops through to device's message handling code
    assert app.handle_message.call_count == 1


def test_frame_handler_bad_message(app, aps, ieee, caplog):
    deserialize = mock.MagicMock(side_effect=ValueError)
    app._handle_reply = mock.MagicMock()
    app.handle_message = mock.MagicMock()
    _frame_handler(app, aps, ieee, 0, deserialize)
    assert any(record.levelname == 'ERROR' for record in caplog.records)
    assert app._handle_reply.call_count == 0
    assert app.handle_message.call_count == 0


def test_send_failure(app, aps, ieee):
    req = app._pending[254] = mock.MagicMock()
    app.ezsp_callback_handler(
        'messageSentHandler',
        [None, 0xbeed, aps, 254, 1, b'']
    )
    assert req.send.set_exception.call_count == 1
    assert req.reply.set_exception.call_count == 0


def test_dup_send_failure(app, aps, ieee):
    req = app._pending[254] = mock.MagicMock()
    req.send.set_exception.side_effect = asyncio.futures.InvalidStateError()
    app.ezsp_callback_handler(
        'messageSentHandler',
        [None, 0xbeed, aps, 254, 1, b'']
    )
    assert req.send.set_exception.call_count == 1
    assert req.reply.set_exception.call_count == 0


def test_send_failure_unexpected(app, aps, ieee):
    app.ezsp_callback_handler(
        'messageSentHandler',
        [None, 0xbeed, aps, 257, 1, b'']
    )


def test_send_success(app, aps, ieee):
    req = app._pending[253] = mock.MagicMock()
    app.ezsp_callback_handler(
        'messageSentHandler',
        [None, 0xbeed, aps, 253, 0, b'']
    )
    assert req.send.set_exception.call_count == 0
    assert req.send.set_result.call_count == 1
    assert req.reply.set_exception.call_count == 0
    assert req.reply.set_result.call_count == 0


def test_unexpected_send_success(app, aps, ieee):
    app.ezsp_callback_handler(
        'messageSentHandler',
        [None, 0xbeed, aps, 253, 0, b'']
    )


def test_dup_send_success(app, aps, ieee):
    req = app._pending[253] = mock.MagicMock()
    req.send.set_result.side_effect = asyncio.futures.InvalidStateError()
    app.ezsp_callback_handler(
        'messageSentHandler',
        [None, 0xbeed, aps, 253, 0, b'']
    )
    assert req.send.set_exception.call_count == 0
    assert req.send.set_result.call_count == 1
    assert req.reply.set_exception.call_count == 0
    assert req.reply.set_result.call_count == 0


def test_receive_invalid_message(app, aps, ieee):
    app._handle_reply = mock.MagicMock()
    app.handle_message = mock.MagicMock()
    aps.destinationEndpoint = 1
    aps.clusterId = 6
    app.ezsp_callback_handler(
        'incomingMessageHandler',
        [None, aps, 0, 0, 0, 0, 0, b'\x08\x13\x0b\x00\x71']
    )
    assert app._handle_reply.call_count == 0
    assert app.handle_message.call_count == 0


def test_join_handler(app, ieee):
    # Calls device.initialize, leaks a task
    app.ezsp_callback_handler(
        'trustCenterJoinHandler',
        [1, ieee, None, None, None],
    )
    assert ieee in app.devices


def test_leave_handler(app, ieee):
    app.devices[ieee] = mock.sentinel.device
    app.ezsp_callback_handler(
        'trustCenterJoinHandler',
        [1, ieee, t.EmberDeviceUpdate.DEVICE_LEFT, None, None]
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

    loop = asyncio.get_event_loop()
    loop.run_until_complete(app.permit_with_key(bytes([1, 2, 3, 4, 5, 6, 7, 8]), bytes([0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77, 0x88, 0x4A, 0xF7]), 60))

    assert app._ezsp.addTransientLinkKey.call_count == 1
    assert app._ezsp.permitJoining.call_count == 1


def test_permit_with_key_ieee(app, ieee):
    app._ezsp.addTransientLinkKey = get_mock_coro([0])
    app._ezsp.setPolicy = get_mock_coro([0])

    loop = asyncio.get_event_loop()
    loop.run_until_complete(app.permit_with_key(ieee, bytes([0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77, 0x88, 0x4A, 0xF7]), 60))

    assert app._ezsp.addTransientLinkKey.call_count == 1
    assert app._ezsp.permitJoining.call_count == 1


def test_permit_with_key_invalid_install_code(app, ieee):
    loop = asyncio.get_event_loop()

    with pytest.raises(Exception):
        loop.run_until_complete(app.permit_with_key(ieee, bytes([0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77, 0x88]), 60))


def test_permit_with_key_failed_add_key(app, ieee):
    app._ezsp.addTransientLinkKey = get_mock_coro([1, 1])

    loop = asyncio.get_event_loop()
    with pytest.raises(Exception):
        loop.run_until_complete(app.permit_with_key(ieee, bytes([0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77, 0x88, 0x4A, 0xF7]), 60))


def test_permit_with_key_failed_set_policy(app, ieee):
    app._ezsp.addTransientLinkKey = get_mock_coro([0])
    app._ezsp.setPolicy = get_mock_coro([1])

    loop = asyncio.get_event_loop()
    with pytest.raises(Exception):
        loop.run_until_complete(app.permit_with_key(ieee, bytes([0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77, 0x88, 0x4A, 0xF7]), 60))


def _request(app, returnvals, do_reply=True, send_ack_received=True,
             send_ack_success=True, ezsp_operational=True, is_an_end_dev=None,
             **kwargs):
    async def mocksend(method, nwk, aps_frame, seq, data):
        if not ezsp_operational:
            raise EzspError
        req = app._pending[seq]
        if send_ack_received:
            if send_ack_success:
                req.send.set_result(mock.sentinel.result)
            else:
                req.send.set_exception(DeliveryError())

        if req.reply:
            if do_reply:
                req.reply.set_result(mock.sentinel.result)
        return [returnvals.pop(0)]

    def mock_get_device(*args, **kwargs):
        dev = Device(app, mock.sentinel.ieee, 0xaa55)
        dev.node_desc = mock.MagicMock()
        dev.node_desc.is_end_device = is_an_end_dev
        return dev

    app.get_device = mock_get_device
    app._ezsp.sendUnicast = mocksend
    app._ezsp.setExtendedTimeout.side_effect = asyncio.coroutine(
        mock.MagicMock())
    loop = asyncio.get_event_loop()
    res = loop.run_until_complete(app.request(0x1234, 9, 8, 7, 6, 5, b'', **kwargs))
    assert len(app._pending) == 0
    return res


def test_request(app):
    assert _request(app, [0]) == mock.sentinel.result


def test_request_without_reply(app, aps):
    assert _request(app, [0], expect_reply=False) == mock.sentinel.result


def test_request_without_reply_send_timeout(app, aps):
    with pytest.raises(asyncio.TimeoutError):
        _request(app, [0], expect_reply=False, send_ack_received=False, timeout=0.1)


def test_request_fail(app):
    with pytest.raises(DeliveryError):
        _request(app, [1])


def test_request_retry(app):
    returnvals = [1, 0, 0]
    assert _request(app, returnvals, tries=2, delay=0) == mock.sentinel.result
    assert returnvals == [0]


def test_request_ezsp_failed(app):
    with pytest.raises(EzspError):
        _request(app, [1], do_reply=True, ezsp_operational=False,
                 expect_reply=True)
        assert len(app._pending) == 0


def test_request_retry_fail(app):
    returnvals = [1, 1, 0, 0]
    with pytest.raises(DeliveryError):
        assert _request(app, returnvals, tries=2, delay=0)
    assert returnvals == [0, 0]


def test_request_retry_msg_send_exception(app):
    returnvals = [1, 0, 0, 0]
    with pytest.raises(DeliveryError):
        assert _request(app, returnvals, tries=2, delay=0,
                        send_ack_received=True, send_ack_success=False,
                        do_reply=False)
    assert returnvals == [0, 0]


def test_request_reply_timeout(app):
    with pytest.raises(asyncio.TimeoutError):
        _request(app, [0], do_reply=False, expect_reply=True, timeout=0.1)


def test_request_reply_timeout_send_timeout(app):
    with pytest.raises(asyncio.TimeoutError):
        _request(app, [0], do_reply=False, expect_reply=True,
                 send_ack_received=False, timeout=0.1)
    assert app._pending == {}


def test_request_send_timeout_reply_success(app):
    with pytest.raises(asyncio.TimeoutError):
        assert _request(app, [0], do_reply=True, expect_reply=True,
                        send_ack_received=False, timeout=0.1)
    assert app._pending == {}


def test_request_ctrl_not_running(app):
    app._ctrl_event.clear()
    with pytest.raises(ControllerError):
        _request(app, [0], do_reply=False, expect_reply=True, timeout=0.1)


def test_request_extended_timeout(app):
    app._ezsp.setExtendedTimeout.side_effect = asyncio.coroutine(
        mock.MagicMock())
    assert _request(app, [0], is_an_end_dev=False) == mock.sentinel.result
    assert app._ezsp.setExtendedTimeout.call_count == 0

    assert _request(app, [0], is_an_end_dev=True) == mock.sentinel.result
    assert app._ezsp.setExtendedTimeout.call_count == 1

    assert _request(app, [0], is_an_end_dev=None) == mock.sentinel.result
    assert app._ezsp.setExtendedTimeout.call_count == 2


@pytest.mark.asyncio
async def _test_broadcast(app, broadcast_success=True, send_timeout=False,
                          ezsp_running=True):
    (profile, cluster, src_ep, dst_ep, grpid, radius, tsn, data) = (
        0x260, 1, 2, 3, 0x0100, 0x06, 210, b'\x02\x01\x00'
    )

    async def mock_send(nwk, aps, radiusm, tsn, data):
        if not ezsp_running:
            raise EzspError
        if broadcast_success:
            if not send_timeout:
                app._pending[tsn].send.set_result(mock.sentinel.result)
            return [0]
        else:
            return [t.EmberStatus.ERR_FATAL]

    app._ezsp.sendBroadcast.side_effect = mock_send

    await app.broadcast(
        profile, cluster, src_ep, dst_ep, grpid, radius, tsn, data)
    assert app._ezsp.sendBroadcast.call_count == 1
    assert app._ezsp.sendBroadcast.call_args[0][2] == radius
    assert app._ezsp.sendBroadcast.call_args[0][3] == tsn
    assert app._ezsp.sendBroadcast.call_args[0][4] == data
    assert len(app._pending) == 0


@pytest.mark.asyncio
async def test_broadcast(app):
    await _test_broadcast(app)
    assert len(app._pending) == 0


@pytest.mark.asyncio
async def test_broadcast_fail(app):
    with pytest.raises(DeliveryError):
        await _test_broadcast(app, broadcast_success=False)
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
        0x260, 1, 2, 3, 0x0100, 0x06, 210, b'\x02\x01\x00'
    )

    async def mocksend(nwk, aps, radiusm, tsn, data):
        raise EzspError

    app._ezsp.sendBroadcast.side_effect = mocksend

    with pytest.raises(ControllerError):
        await app.broadcast(
            profile, cluster, src_ep, dst_ep, grpid, radius, tsn, data)
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
    app._handle_reset_request = mock.MagicMock(
        spec_set=app._handle_reset_request)
    app.ezsp_callback_handler('_reset_controller_application',
                              (mock.sentinel.error, ))
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

    monkeypatch.setattr(application, 'RESET_ATTEMPT_BACKOFF_TIME', 0.1)
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
    assert app._ezsp.reconnect.call_count == 1
    assert app.startup.call_count == 1


@pytest.mark.asyncio
async def test_watchdog(app, monkeypatch):
    from bellows.zigbee import application
    monkeypatch.setattr(application, 'WATCHDOG_WAKE_PERIOD', 0.1)
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
    ep.device_type = 0xbeef
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
