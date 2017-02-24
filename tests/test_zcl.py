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
    assert cluster._endpoint._device.request.call_count == 1


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


def test_read_attributes(cluster):
    @asyncio.coroutine
    def mockrequest(foundation, command, schema, args):
        rar = zcl.foundation.ReadAttributeRecord()
        rar.status = 0
        rar.attrid = 0
        rar.value = zcl.foundation.TypeValue()
        rar.value.value = 99
        return [[rar]]
    cluster.request = mockrequest
    loop = asyncio.get_event_loop()
    loop.run_until_complete(cluster.read_attributes([0]))


def test_write_attributes(cluster):
    cluster.write_attributes({0: 5})
    assert cluster._endpoint._device.request.call_count == 1


def test_bind(cluster):
    cluster.bind()


def test_unbind(cluster):
    cluster.unbind()


def test_configure_reporting(cluster):
    cluster.configure_reporting(0, 10, 20, 1)


def test_command(cluster):
    cluster.command(0x00)
    assert cluster._endpoint._device.request.call_count == 1


def test_name(cluster):
    assert cluster.name == 'Basic'


def test_log(cluster):
    cluster.debug("Test debug")
    cluster.info("Test info")
    cluster.warn("Test warn")
    cluster.error("Test error")
