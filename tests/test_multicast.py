import pytest
from zigpy.endpoint import Endpoint

import bellows.ezsp
import bellows.multicast
import bellows.types as t

from .async_mock import AsyncMock, MagicMock, sentinel

CUSTOM_SIZE = 12


@pytest.fixture
def ezsp_f():
    e = MagicMock()
    e.getConfigurationValue = AsyncMock(return_value=[0, CUSTOM_SIZE])
    return e


@pytest.fixture
def multicast(ezsp_f):
    m = bellows.multicast.Multicast(ezsp_f)
    return m


async def test_initialize(multicast):
    group_id = 0x0200
    mct = active_multicasts = 4

    async def mock_get(*args):
        nonlocal group_id, mct
        entry = t.EmberMulticastTableEntry()
        if mct > 0:
            entry.endpoint = t.uint8_t(group_id % 3 + 1)
        else:
            entry.endpoint = t.uint8_t(0)
        entry.multicastId = t.EmberMulticastId(group_id)
        entry.networkIndex = t.uint8_t(0)
        group_id += 1
        mct -= 1
        return [t.EmberStatus.SUCCESS, entry]

    multicast._ezsp.getMulticastTableEntry.side_effect = mock_get
    await multicast._initialize()
    assert multicast._ezsp.getMulticastTableEntry.call_count == CUSTOM_SIZE
    assert len(multicast._available) == CUSTOM_SIZE - active_multicasts


async def test_initialize_fail_configured_size(multicast):
    multicast._ezsp.getConfigurationValue.return_value = t.EmberStatus.ERR_FATAL, 16
    await multicast._initialize()
    ezsp = multicast._ezsp
    assert ezsp.getMulticastTableEntry.call_count == 0
    assert len(multicast._available) == 0


async def test_initialize_fail(multicast):
    group_id = 0x0200

    async def mock_get(*args):
        nonlocal group_id
        entry = t.EmberMulticastTableEntry()
        entry.endpoint = t.uint8_t(group_id % 3 + 1)
        entry.multicastId = t.EmberMulticastId(group_id)
        entry.networkIndex = t.uint8_t(0)
        group_id += 1
        return [t.EmberStatus.ERR_FATAL, entry]

    multicast._ezsp.getMulticastTableEntry.side_effect = mock_get
    await multicast._initialize()
    ezsp = multicast._ezsp
    assert ezsp.getMulticastTableEntry.call_count == CUSTOM_SIZE
    assert len(multicast._available) == 0


async def test_startup(multicast):
    coordinator = MagicMock()
    ep1 = MagicMock(spec_set=Endpoint)
    ep1.member_of = [sentinel.grp, sentinel.grp, sentinel.grp]
    coordinator.endpoints = {0: sentinel.ZDO, 1: ep1}
    multicast._initialize = AsyncMock()
    multicast.subscribe = MagicMock()
    multicast.subscribe.side_effect = AsyncMock()
    await multicast.startup(coordinator)

    assert multicast._initialize.await_count == 1
    assert multicast.subscribe.call_count == len(ep1.member_of)
    assert multicast.subscribe.call_args[0][0] == sentinel.grp


def _subscribe(multicast, group_id, success=True):
    async def mock_set(*args):
        if success:
            return [t.EmberStatus.SUCCESS]
        return [t.EmberStatus.ERR_FATAL]

    multicast._ezsp.setMulticastTableEntry = MagicMock()
    multicast._ezsp.setMulticastTableEntry.side_effect = mock_set
    return multicast.subscribe(group_id)


async def test_subscribe(multicast):
    grp_id = 0x0200
    multicast._available.add(1)
    multicast._ezsp = ezsp_f

    ret = await _subscribe(multicast, grp_id, success=True)
    assert ret == t.EmberStatus.SUCCESS
    set_entry = multicast._ezsp.setMulticastTableEntry
    assert set_entry.call_count == 1
    assert set_entry.call_args[0][1].multicastId == grp_id
    assert grp_id in multicast._multicast

    set_entry.reset_mock()
    ret = await _subscribe(multicast, grp_id, success=True)
    assert ret == t.EmberStatus.SUCCESS
    set_entry = multicast._ezsp.setMulticastTableEntry
    assert set_entry.call_count == 0
    assert grp_id in multicast._multicast


async def test_subscribe_fail(multicast):
    grp_id = 0x0200
    multicast._available.add(1)

    ret = await _subscribe(multicast, grp_id, success=False)
    assert ret != t.EmberStatus.SUCCESS
    set_entry = multicast._ezsp.setMulticastTableEntry
    assert set_entry.call_count == 1
    assert set_entry.call_args[0][1].multicastId == grp_id
    assert grp_id not in multicast._multicast
    assert len(multicast._available) == 1


async def test_subscribe_no_avail(multicast):
    grp_id = 0x0200

    ret = await _subscribe(multicast, grp_id, success=True)
    assert ret != t.EmberStatus.SUCCESS


def _unsubscribe(multicast, group_id, success=True):
    async def mock_set(*args):
        if success:
            return [t.EmberStatus.SUCCESS]
        return [t.EmberStatus.ERR_FATAL]

    multicast._ezsp.setMulticastTableEntry = MagicMock()
    multicast._ezsp.setMulticastTableEntry.side_effect = mock_set
    return multicast.unsubscribe(group_id)


async def test_unsubscribe(multicast):
    grp_id = 0x0200
    multicast._available.add(1)

    await _subscribe(multicast, grp_id, success=True)

    multicast._ezsp.setMulticastTableEntry.reset_mock()
    ret = await _unsubscribe(multicast, grp_id, success=True)
    assert ret == t.EmberStatus.SUCCESS
    set_entry = multicast._ezsp.setMulticastTableEntry
    assert set_entry.call_count == 1
    assert grp_id not in multicast._multicast
    assert len(multicast._available) == 1

    multicast._ezsp.setMulticastTableEntry.reset_mock()
    ret = await _unsubscribe(multicast, grp_id, success=True)
    assert ret != t.EmberStatus.SUCCESS
    set_entry = multicast._ezsp.setMulticastTableEntry
    assert set_entry.call_count == 0
    assert grp_id not in multicast._multicast
    assert len(multicast._available) == 1


async def test_unsubscribe_fail(multicast):
    grp_id = 0x0200
    multicast._available.add(1)

    await _subscribe(multicast, grp_id, success=True)

    multicast._ezsp.setMulticastTableEntry.reset_mock()
    ret = await _unsubscribe(multicast, grp_id, success=False)
    assert ret != t.EmberStatus.SUCCESS
    set_entry = multicast._ezsp.setMulticastTableEntry
    assert set_entry.call_count == 1
    assert grp_id in multicast._multicast
    assert len(multicast._available) == 0
