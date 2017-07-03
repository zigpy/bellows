import asyncio
from unittest import mock

import pytest

import bellows.types as t
from bellows.zigbee import device, endpoint
from bellows.zigbee.zdo import types


@pytest.fixture
def ep():
    dev = mock.MagicMock()
    return endpoint.Endpoint(dev, 1)


def _test_initialize(ep, profile):
    loop = asyncio.get_event_loop()

    @asyncio.coroutine
    def mockrequest(req, nwk, epid):
        sd = types.SimpleDescriptor()
        sd.endpoint = 1
        sd.profile = profile
        sd.device_type = 0xff
        sd.input_clusters = [5]
        sd.output_clusters = [6]
        return [0, None, sd]

    ep._device.zdo.request = mockrequest
    loop.run_until_complete(ep.initialize())

    assert ep.status > endpoint.Status.NEW
    assert 5 in ep.in_clusters
    assert 6 in ep.out_clusters


def test_initialize_zha(ep):
    return _test_initialize(ep, 260)


def test_initialize_zll(ep):
    return _test_initialize(ep, 49246)


def test_initialize_fail(ep):
    loop = asyncio.get_event_loop()

    @asyncio.coroutine
    def mockrequest(req, nwk, epid):
        return [1, None, None]

    ep._device.zdo.request = mockrequest
    loop.run_until_complete(ep.initialize())

    assert ep.status == endpoint.Status.NEW


def test_reinitialize(ep):
    _test_initialize(ep, 260)
    assert ep.profile_id == 260
    ep.profile_id = 10
    _test_initialize(ep, 260)
    assert ep.profile_id == 10


def test_add_input_cluster(ep):
    ep.add_input_cluster(0)
    assert 0 in ep.in_clusters


def test_add_output_cluster(ep):
    ep.add_output_cluster(0)
    assert 0 in ep.out_clusters


def test_multiple_add_input_cluster(ep):
    ep.add_input_cluster(0)
    assert ep.in_clusters[0].cluster_id is 0
    ep.in_clusters[0].cluster_id = 1
    assert ep.in_clusters[0].cluster_id is 1
    ep.add_input_cluster(0)
    assert ep.in_clusters[0].cluster_id is 1


def test_multiple_add_output_cluster(ep):
    ep.add_output_cluster(0)
    assert ep.out_clusters[0].cluster_id is 0
    ep.out_clusters[0].cluster_id = 1
    assert ep.out_clusters[0].cluster_id is 1
    ep.add_output_cluster(0)
    assert ep.out_clusters[0].cluster_id is 1


def test_get_aps():
    app_mock = mock.MagicMock()
    ieee = t.EmberEUI64(map(t.uint8_t, [0, 1, 2, 3, 4, 5, 6, 7]))
    dev = device.Device(app_mock, ieee, 65535)
    ep = endpoint.Endpoint(dev, 55)
    ep.status = endpoint.Status.ZDO_INIT
    ep.profile_id = 99
    aps = ep.get_aps(255)
    assert aps.profileId == 99
    assert aps.clusterId == 255
    assert aps.sourceEndpoint == 55
    assert aps.destinationEndpoint == 55


def test_handle_message(ep):
    c = ep.add_input_cluster(0)
    c.handle_message = mock.MagicMock()
    f = t.EmberApsFrame()
    f.clusterId = 0
    ep.handle_message(False, f, 0, 1, [])
    c.handle_message.assert_called_once_with(False, f, 0, 1, [])


def test_handle_message_output(ep):
    c = ep.add_output_cluster(0)
    c.handle_message = mock.MagicMock()
    f = t.EmberApsFrame()
    f.clusterId = 0
    ep.handle_message(False, f, 0, 1, [])
    c.handle_message.assert_called_once_with(False, f, 0, 1, [])


def test_handle_request_unknown(ep):
    f = t.EmberApsFrame()
    f.clusterId = 99
    ep.handle_message(False, f, 0, 0, [])


def test_cluster_attr(ep):
    with pytest.raises(AttributeError):
        ep.basic
    ep.add_input_cluster(0)
    ep.basic
