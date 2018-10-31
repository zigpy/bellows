import asyncio
from unittest import mock

import pytest

import bellows.types as t
from bellows.zigbee.application import ControllerApplication
from zigpy.exceptions import DeliveryError


@pytest.fixture
def app():
    ezsp = mock.MagicMock()
    return ControllerApplication(ezsp)


@pytest.fixture
def aps():
    f = t.EmberApsFrame()
    f.profileId = 99
    f.sourceEndpoint = 8
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


def _test_startup(app, nwk_type, auto_form=False, init=0):
    async def mockezsp(*args, **kwargs):
        return [0, nwk_type]

    async def mockinit(*args, **kwargs):
        return [init]

    app._ezsp._command = mockezsp
    app._ezsp.addEndpoint = mockezsp
    app._ezsp.setConfigurationValue = mockezsp
    app._ezsp.networkInit = mockinit
    app._ezsp.getNetworkParameters = mockezsp
    app._ezsp.setPolicy = mockezsp
    app._ezsp.getNodeId = mockezsp
    app._ezsp.getEui64 = mockezsp
    app._ezsp.leaveNetwork = mockezsp
    app.form_network = mock.MagicMock(side_effect=asyncio.coroutine(mock.MagicMock()))
    app._ezsp.reset.side_effect = asyncio.coroutine(mock.MagicMock())
    app._ezsp.version.side_effect = asyncio.coroutine(mock.MagicMock())

    loop = asyncio.get_event_loop()
    loop.run_until_complete(app.startup(auto_form=auto_form))


def test_startup(app):
    return _test_startup(app, t.EmberNodeType.COORDINATOR)


def test_startup_no_status(app):
    with pytest.raises(Exception):
        return _test_startup(app, None, init=1)


def test_startup_no_status_form(app):
    return _test_startup(app, None, auto_form=True, init=1)


def test_startup_end(app):
    with pytest.raises(Exception):
        return _test_startup(app, t.EmberNodeType.SLEEPY_END_DEVICE)


def test_startup_end_form(app):
    return _test_startup(app, t.EmberNodeType.SLEEPY_END_DEVICE, True)


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
    send_fut, reply_fut = app._pending[1] = (mock.MagicMock(), mock.MagicMock())
    deserialize = mock.MagicMock(return_value=(1, 1, True, []))
    _frame_handler(app, aps, ieee, 0, deserialize, 0x8000)
    assert send_fut.set_result.call_count == 0
    assert reply_fut.set_result.call_count == 1


def test_frame_handler_dup_zdo_reply(app, aps, ieee):
    send_fut, reply_fut = app._pending[1] = (mock.MagicMock(), mock.MagicMock())
    reply_fut.set_result.side_effect = asyncio.futures.InvalidStateError()
    deserialize = mock.MagicMock(return_value=(1, 1, True, []))
    _frame_handler(app, aps, ieee, 0, deserialize, 0x8000)
    assert send_fut.set_result.call_count == 0
    assert reply_fut.set_result.call_count == 1


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
    send_fut, reply_fut = app._pending[254] = (mock.MagicMock(), mock.MagicMock())
    app.ezsp_callback_handler(
        'messageSentHandler',
        [None, None, None, 254, 1, b'']
    )
    assert send_fut.set_exception.call_count == 1
    assert reply_fut.set_exception.call_count == 0


def test_dup_send_failure(app, aps, ieee):
    send_fut, reply_fut = app._pending[254] = (mock.MagicMock(), mock.MagicMock())
    send_fut.set_exception.side_effect = asyncio.futures.InvalidStateError()
    app.ezsp_callback_handler(
        'messageSentHandler',
        [None, None, None, 254, 1, b'']
    )
    assert send_fut.set_exception.call_count == 1
    assert reply_fut.set_exception.call_count == 0


def test_send_failure_unexpected(app, aps, ieee):
    app.ezsp_callback_handler(
        'messageSentHandler',
        [None, None, None, 257, 1, b'']
    )


def test_send_success(app, aps, ieee):
    send_fut, reply_fut = app._pending[253] = (mock.MagicMock(), mock.MagicMock())
    app.ezsp_callback_handler(
        'messageSentHandler',
        [None, None, None, 253, 0, b'']
    )
    assert send_fut.set_exception.call_count == 0
    assert send_fut.set_result.call_count == 1
    assert reply_fut.set_result.call_count == 0


def test_unexpected_send_success(app, aps, ieee):
    app.ezsp_callback_handler(
        'messageSentHandler',
        [None, None, None, 253, 0, b'']
    )


def test_dup_send_success(app, aps, ieee):
    send_fut, reply_fut = app._pending[253] = (mock.MagicMock(), mock.MagicMock())
    send_fut.set_result.side_effect = asyncio.futures.InvalidStateError()
    app.ezsp_callback_handler(
        'messageSentHandler',
        [None, None, None, 253, 0, b'']
    )
    assert send_fut.set_exception.call_count == 0
    assert send_fut.set_result.call_count == 1
    assert reply_fut.set_result.call_count == 0


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


def _request(app, returnvals, do_reply=True, **kwargs):
    async def mocksend(method, nwk, aps_frame, seq, data):
        if app._pending[seq][1] is None:
            app._pending[seq][0].set_result(mock.sentinel.result)
        else:
            app._pending[seq][0].set_result(True)
            if do_reply:
                app._pending[seq][1].set_result(mock.sentinel.result)
        return [returnvals.pop(0)]

    app._ezsp.sendUnicast = mocksend
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(app.request(0x1234, 9, 8, 7, 6, 5, b'', **kwargs))


def test_request(app):
    assert _request(app, [0]) == mock.sentinel.result


def test_request_without_reply(app, aps):
    assert _request(app, [0], expect_reply=False) == mock.sentinel.result


def test_request_fail(app):
    with pytest.raises(DeliveryError):
        _request(app, [1])


def test_request_retry(app):
    returnvals = [1, 0, 0]
    assert _request(app, returnvals, tries=2, delay=0) == mock.sentinel.result
    assert returnvals == [0]


def test_request_retry_fail(app):
    returnvals = [1, 1, 0, 0]
    with pytest.raises(DeliveryError):
        assert _request(app, returnvals, tries=2, delay=0)
    assert returnvals == [0, 0]


def test_request_reply_timeout(app):
    with pytest.raises(asyncio.TimeoutError):
        _request(app, [0], do_reply=False, expect_reply=True, timeout=0.1)
    assert app._pending == {}


@pytest.mark.asyncio
async def test_broadcast(app):
    (profile, cluster, src_ep, dst_ep, grpid, radius, tsn, data) = (
        0x260, 1, 2, 3, 0x0100, 0x06, 210, b'\x02\x01\x00'
    )

    async def mocksend(nwk, aps, radiusm, tsn, data):
        app._pending[tsn][0].set_result(mock.sentinel.result)
        return [0]

    app._ezsp.sendBroadcast.side_effect = mocksend

    await app.broadcast(
        profile, cluster, src_ep, dst_ep, grpid, radius, tsn, data)
    assert app._ezsp.sendBroadcast.call_count == 1
    assert app._ezsp.sendBroadcast.call_args[0][2] == radius
    assert app._ezsp.sendBroadcast.call_args[0][3] == tsn
    assert app._ezsp.sendBroadcast.call_args[0][4] == data
