from unittest import mock

import pytest

import bellows.types as t
import bellows.zigbee.device
import bellows.zigbee.zdo as zdo


def test_commands():
    for cmdid, cmdspec in zdo.types.CLUSTERS.items():
        assert 0 <= cmdid <= 0xffff
        assert isinstance(cmdspec, tuple)
        assert isinstance(cmdspec[0], str)
        for paramname, paramtype in zip(cmdspec[1], cmdspec[2]):
            assert isinstance(paramname, str)
            assert hasattr(paramtype, 'serialize')
            assert hasattr(paramtype, 'deserialize')


def test_deserialize():
    tsn, command_id, is_reply, args = zdo.deserialize(2, b'\x01\x02\x03xx')
    assert tsn == 1
    assert is_reply is False
    assert args == [0x0302]


def test_deserialize_unknown():
    tsn, command_id, is_reply, args = zdo.deserialize(0x0100, b'\x01')
    assert tsn == 1
    assert is_reply is False


@pytest.fixture
def zdo_f():
    app = mock.MagicMock()
    app.ieee = t.EmberEUI64(map(t.uint8_t, [8, 9, 10, 11, 12, 13, 14, 15]))
    app.get_sequence = mock.MagicMock(return_value=123)
    ieee = t.EmberEUI64(map(t.uint8_t, [0, 1, 2, 3, 4, 5, 6, 7]))
    dev = bellows.zigbee.device.Device(app, ieee, 65535)
    return zdo.ZDO(dev)


def test_request(zdo_f):
    zdo_f.request(2, 65535)
    app_mock = zdo_f._device._application
    assert app_mock.request.call_count == 1
    assert app_mock.get_sequence.call_count == 1


def test_bind(zdo_f):
    zdo_f.bind(1, 1026)
    app_mock = zdo_f._device._application
    assert app_mock.request.call_count == 1
    assert app_mock.request.call_args[0][1].clusterId == 0x0021


def test_unbind(zdo_f):
    zdo_f.unbind(1, 1026)
    app_mock = zdo_f._device._application
    assert app_mock.request.call_count == 1
    assert app_mock.request.call_args[0][1].clusterId == 0x0022


def test_leave(zdo_f):
    zdo_f.leave()
    app_mock = zdo_f._device._application
    assert app_mock.request.call_count == 1
    assert app_mock.request.call_args[0][1].clusterId == 0x0034


def _handle_match_desc(zdo_f, profile):
    zdo_f.reply = mock.MagicMock()
    aps = t.EmberApsFrame()
    zdo_f.handle_message(False, aps, 123, 0x0006, [None, profile, [], []])
    assert zdo_f.reply.call_count == 1


def test_handle_match_desc_zha(zdo_f):
    return _handle_match_desc(zdo_f, 260)


def test_handle_match_desc_generic(zdo_f):
    return _handle_match_desc(zdo_f, 0)


def test_handle_addr(zdo_f):
    aps = t.EmberApsFrame()
    nwk = zdo_f._device.application.nwk
    zdo_f.reply = mock.MagicMock()
    zdo_f.handle_message(False, aps, 234, 0x0001, [nwk])
    assert zdo_f.reply.call_count == 1


def test_handle_announce(zdo_f):
    dev = zdo_f._device
    dev._application.devices.pop(dev.ieee)
    aps = t.EmberApsFrame()
    zdo_f.handle_message(False, aps, 111, 0x0013, [0, dev.ieee, dev.nwk])


def test_handle_unsupported(zdo_f):
    aps = t.EmberApsFrame()
    zdo_f.handle_message(False, aps, 321, 0xffff, [])


def test_device_accessor(zdo_f):
    assert zdo_f.device.nwk == 65535
