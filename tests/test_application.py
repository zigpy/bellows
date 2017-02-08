import asyncio
import os
from unittest import mock

import pytest

import bellows.types as t
from bellows.zigbee.application import ControllerApplication
from bellows.zigbee import zha


@pytest.fixture
def app():
    ezsp = mock.MagicMock()
    return ControllerApplication(ezsp)


@pytest.fixture
def aps():
    f = t.EmberApsFrame()
    f.sequence = 100
    return f


@pytest.fixture
def ieee(init=0):
    return t.EmberEUI64(map(t.uint8_t, range(init, init + 8)))


def _test_startup(app, nwk_type):
    # This is a fairly brittle and pointless test. Except the point is just
    # to allow startup to run all its paths and check types etc.
    @asyncio.coroutine
    def mockezsp(*args, **kwargs):
        return [0, nwk_type]
    app._ezsp.setConfigurationValue = mockezsp
    app._ezsp.networkInit = mockezsp
    app._ezsp.getNetworkParameters = mockezsp
    app._ezsp.setPolicy = mockezsp
    app._ezsp.getNodeId = mockezsp
    app._ezsp.getEui64 = mockezsp

    loop = asyncio.get_event_loop()
    loop.run_until_complete(app.startup())


def test_startup(app):
    return _test_startup(app, t.EmberNodeType.EMBER_COORDINATOR)


def test_startup_not_coordinator(app):
    with pytest.raises(Exception):
        return _test_startup(app, t.EmberNodeType.EMBER_SLEEPY_END_DEVICE)


def _frame_handler(app, aps, ieee, endpoint, cluster=0, sender=3):
    app.add_device(ieee, 3)
    app._ieee = [t.uint8_t(0)] * 8
    app._nwk = 0
    aps.destinationEndpoint = endpoint
    aps.clusterId = cluster
    app.ezsp_callback_handler(
        'incomingMessageHandler',
        [None, aps, 1, 2, sender, 4, 5, b'\x01\x00\x00']
    )


def test_frame_handler_unknown_device(app, aps, ieee):
    return _frame_handler(app, aps, ieee, 0, sender=99)


def test_frame_handler_zdo(app, aps, ieee):
    return _frame_handler(app, aps, ieee, 0)


def test_frame_handler_zdo_reply(app, aps, ieee):
    fut = app._pending[1] = mock.MagicMock()
    _frame_handler(app, aps, ieee, 0, 0x8000)
    assert fut.set_result.call_count == 1


def test_frame_handler_zdo_reply_unknown(app, aps, ieee):
    _frame_handler(app, aps, ieee, 0, 0x8000)


def test_frame_handler_zcl(app, aps, ieee):
    return _frame_handler(app, aps, ieee, 1)


def test_send_failure(app, aps, ieee):
    fut = app._pending[254] = mock.MagicMock()
    app.ezsp_callback_handler(
        'messageSentHandler',
        [None, None, None, 254, 1, b'']
    )
    assert fut.set_exception.call_count == 1


def test_send_failure_unexpected(app, aps, ieee):
    app.ezsp_callback_handler(
        'messageSentHandler',
        [None, None, None, 257, 1, b'']
    )


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
        [1, ieee, t.EmberDeviceUpdate.EMBER_DEVICE_LEFT, None, None]
    )
    assert ieee not in app.devices


def test_database(app, tmpdir, ieee):

    db = os.path.join(str(tmpdir), 'test.db')
    dev = app.add_device(ieee, 99)
    ep = dev.add_endpoint(1)
    ep.device_type = zha.DeviceType.PUMP
    ep = dev.add_endpoint(2)
    ep.add_cluster(0)
    app.save(db)
    app.load(db)

    os.unlink(db)
    app.load(db)


def test_sequence(app):
    for i in range(1000):
        seq = app.get_sequence()
        assert seq >= 0
        assert seq < 256


def test_get_device_nwk(app, ieee):
    dev = app.add_device(ieee, 8)
    assert app.get_device(nwk=8) is dev


def test_get_device_ieee(app, ieee):
    dev = app.add_device(ieee, 8)
    assert app.get_device(ieee=ieee) is dev


def test_get_device_both(app, ieee):
    dev = app.add_device(ieee, 8)
    assert app.get_device(ieee=ieee, nwk=8) is dev


def test_permit(app):
    app.permit(60)
    assert app._ezsp.permitJoining.call_count == 1


def _request(app, aps, returnval):
    @asyncio.coroutine
    def mocksend(method, nwk, aps_frame, seq, data):
        app._pending[seq].set_result(mock.sentinel.result)
        return [returnval]

    app._ezsp.sendUnicast = mocksend
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(app.request(0x1234, aps, b''))


def test_request(app, aps):
    assert _request(app, aps, 0) == mock.sentinel.result


def test_request_fail(app, aps):
    with pytest.raises(Exception):
        _request(app, aps, 1)
