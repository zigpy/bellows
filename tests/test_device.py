import asyncio
from unittest import mock

import pytest

import bellows.types as t
from bellows.zigbee import device, endpoint


@pytest.fixture
def dev():
    app_mock = mock.MagicMock()
    ieee = t.EmberEUI64(map(t.uint8_t, [0, 1, 2, 3, 4, 5, 6, 7]))
    return device.Device(app_mock, ieee, 65535)


def test_initialize(monkeypatch, dev):
    loop = asyncio.get_event_loop()

    @asyncio.coroutine
    def mockrequest(req, nwk):
        return [0, None, [1, 2]]

    @asyncio.coroutine
    def mockepinit(self):
        return

    monkeypatch.setattr(endpoint.Endpoint, 'initialize', mockepinit)

    dev.zdo.request = mockrequest
    loop.run_until_complete(dev.initialize())

    assert dev.status > device.Status.NEW
    assert 1 in dev.endpoints
    assert 2 in dev.endpoints


def test_initialize_fail(dev):
    loop = asyncio.get_event_loop()

    @asyncio.coroutine
    def mockrequest(req, nwk):
        return [1]

    dev.zdo.request = mockrequest
    loop.run_until_complete(dev.initialize())

    assert dev.status == device.Status.NEW


def test_aps(dev):
    f = dev.get_aps(1, 2, 3)
    assert f.profileId == 1
    assert f.clusterId == 2
    assert f.sourceEndpoint == 3
    assert f.destinationEndpoint == 3


def test_request(dev):
    aps = dev.get_aps(1, 2, 3)
    dev.request(aps, b'')
    app_mock = dev._application
    assert app_mock.request.call_count == 1
    assert app_mock.get_sequence.call_count == 1


def test_radio_details(dev):
    dev.radio_details(1, 2)
    assert dev.lqi == 1
    assert dev.rssi == 2


def test_handle_request_no_endpoint(dev):
    f = dev.get_aps(1, 2, 3)
    dev.handle_message(False, f, 1, 0, [])


def test_handle_request(dev):
    f = dev.get_aps(1, 2, 3)
    ep = dev.add_endpoint(3)
    ep.handle_message = mock.MagicMock()
    dev.handle_message(False, f, 1, 0, [])
    assert ep.handle_message.call_count == 1
