import asyncio
from unittest import mock

import pytest

import bellows.types as t
import bellows.zigbee.zcl as zcl


@pytest.fixture
def aps():
    return t.EmberApsFrame()


def test_deserialize_general(aps):
    aps.clusterId = 0
    tsn, command_id, is_reply, args = zcl.deserialize(aps, b'\x00\x01\x00')
    assert tsn == 1
    assert command_id == 0
    assert is_reply is False


def test_deserialize_general_unknown(aps):
    aps.clusterId = 0
    tsn, command_id, is_reply, args = zcl.deserialize(aps, b'\x00\x01\xff')
    assert tsn == 1
    assert command_id == 255
    assert is_reply is False


def test_deserialize_cluster(aps):
    aps.clusterId = 0
    tsn, command_id, is_reply, args = zcl.deserialize(aps, b'\x01\x01\x00xxx')
    assert tsn == 1
    assert command_id == 256
    assert is_reply is False


def test_deserialize_cluster_client(aps):
    aps.clusterId = 3
    tsn, command_id, is_reply, args = zcl.deserialize(aps, b'\x09\x01\x00AB')
    assert tsn == 1
    assert command_id == 256
    assert is_reply is True
    assert args == [0x4241]


def test_deserialize_cluster_unknown(aps):
    aps.clusterId = 0xff00
    tsn, command_id, is_reply, args = zcl.deserialize(aps, b'\x05\x00\x00\x01\x00')
    assert tsn == 1
    assert command_id == 256
    assert is_reply is False


def test_deserialize_cluster_command_unknown(aps):
    aps.clusterId = 0
    tsn, command_id, is_reply, args = zcl.deserialize(aps, b'\x01\x01\xff')
    assert tsn == 1
    assert command_id == 255 + 256
    assert is_reply is False


def test_unknown_cluster():
    c = zcl.Cluster.from_id(None, 999)
    assert isinstance(c, zcl.Cluster)
    assert c.cluster_id == 999


@pytest.fixture
def cluster(aps):
    epmock = mock.MagicMock()
    aps.clusterId = 0
    aps.sequence = 123
    epmock.get_aps.return_value = aps
    return zcl.Cluster.from_id(epmock, 0)


def test_request_general(cluster):
    cluster.request(True, 0, [])
    assert cluster._endpoint.device.request.call_count == 1


def test_attribute_report(cluster):
    attr = zcl.foundation.Attribute()
    attr.attrid = 4
    attr.value = zcl.foundation.TypeValue()
    attr.value.value = 1
    cluster.handle_message(False, aps, 0, 0x0a, [[attr]])
    assert cluster._attr_cache[4] == 1


def test_handle_request_unknown(cluster, aps):
    cluster.handle_message(False, aps, 0, 0xff, [])


def test_handle_cluster_request(cluster, aps):
    cluster.handle_message(False, aps, 0, 256, [])


def test_handle_unexpected_reply(cluster, aps):
    cluster.handle_message(True, aps, 0, 0, [])


def test_read_attributes_uncached(cluster):
    @asyncio.coroutine
    def mockrequest(foundation, command, schema, args):
        assert foundation is True
        assert command == 0
        rar0 = zcl.foundation.ReadAttributeRecord()
        rar0.attrid = 0
        rar0.status = 0
        rar0.value = zcl.foundation.TypeValue()
        rar0.value.value = 99
        rar4 = zcl.foundation.ReadAttributeRecord()
        rar4.attrid = 4
        rar4.status = 0
        rar4.value = zcl.foundation.TypeValue()
        rar4.value.value = b'Manufacturer'
        rar99 = zcl.foundation.ReadAttributeRecord()
        rar99.attrid = 99
        rar99.status = 1
        return [[rar0, rar4, rar99]]
    cluster.request = mockrequest
    loop = asyncio.get_event_loop()
    success, failure = loop.run_until_complete(cluster.read_attributes(
        [0, "manufacturer", 99],
    ))
    assert success[0] == 99
    assert success["manufacturer"] == b'Manufacturer'
    assert failure[99] == 1


def test_read_attributes_cached(cluster):
    cluster.request = mock.MagicMock()
    cluster._attr_cache[0] = 99
    cluster._attr_cache[4] = b'Manufacturer'
    loop = asyncio.get_event_loop()
    success, failure = loop.run_until_complete(cluster.read_attributes(
        [0, "manufacturer"],
        allow_cache=True,
    ))
    assert cluster.request.call_count == 0
    assert success[0] == 99
    assert success["manufacturer"] == b'Manufacturer'
    assert failure == {}


def test_read_attributes_mixed_cached(cluster):
    @asyncio.coroutine
    def mockrequest(foundation, command, schema, args):
        assert foundation is True
        assert command == 0
        rar5 = zcl.foundation.ReadAttributeRecord()
        rar5.attrid = 5
        rar5.status = 0
        rar5.value = zcl.foundation.TypeValue()
        rar5.value.value = b'Model'
        return [[rar5]]

    cluster.request = mockrequest
    cluster._attr_cache[0] = 99
    cluster._attr_cache[4] = b'Manufacturer'
    loop = asyncio.get_event_loop()
    success, failure = loop.run_until_complete(cluster.read_attributes(
        [0, "manufacturer", "model"],
        allow_cache=True,
    ))
    assert success[0] == 99
    assert success["manufacturer"] == b'Manufacturer'
    assert success["model"] == b'Model'
    assert failure == {}


def test_write_attributes(cluster):
    cluster.write_attributes({0: 5})
    assert cluster._endpoint.device.request.call_count == 1


def test_bind(cluster):
    cluster.bind()


def test_unbind(cluster):
    cluster.unbind()


def test_configure_reporting(cluster):
    cluster.configure_reporting(0, 10, 20, 1)


def test_command(cluster):
    cluster.command(0x00)
    assert cluster._endpoint.device.request.call_count == 1


def test_name(cluster):
    assert cluster.name == 'Basic'
