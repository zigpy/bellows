import logging

from bellows import types as t

LOGGER = logging.getLogger(__name__)


class Multicast:
    """Multicast table controller for EZSP."""
    TABLE_SIZE = 16

    def __init__(self, ezsp):
        self._ezsp = ezsp
        self._multicast = {}
        self._available = set()

    async def initialize(self) -> None:
        e = self._ezsp
        for i in range(0, self.TABLE_SIZE):
            status, entry = await e.getMulticastTableEntry(i)
            if status != t.EmberStatus.SUCCESS:
                LOGGER.error("Couldn't get MulticastTableEntry #%s: %s",
                             i, status)
                continue
            LOGGER.debug("MulticastTableEntry[%s] = %s", i, entry)
            if entry.endpoint != 0:
                self._multicast[entry.multicastId] = (entry, i)
            else:
                self._available.add(i)

    async def subscribe(self, group_id) -> t.EmberStatus:
        try:
            idx = self._available.pop()
        except KeyError:
            LOGGER.error("No more available slots MulticastId subscription")
            return t.EmberStatus.INDEX_OUT_OF_RANGE
        entry = t.EmberMulticastTableEntry()
        entry.endpoint = t.uint8_t(1)
        entry.multicastId = t.EmberMulticastId(group_id)
        entry.networkIndex = t.uint8_t(0)
        status = await self._ezsp.setMulticastTableEntry(idx, entry)
        if status[0] != t.EmberStatus.SUCCESS:
            LOGGER.warning(
                "Set MulticastTableEntry #%s for %s multicast id: %s",
                idx, entry.multicastId, status)
            self._available.add(idx)
            return status[0]

        self._multicast[entry.multicastId] = (entry, idx)
        LOGGER.debug("Set MulticastTableEntry #%s for %s multicast id: %s",
                     idx, entry.multicastId, status)
        return status[0]

    async def unsubscribe(self, group_id) -> t.EmberStatus:
        try:
            entry, idx = self._multicast[group_id]
        except KeyError:
            LOGGER.error(
                "Couldn't find MulticastTableEntry for %s multicast_id",
                group_id)
            return t.EmberStatus.INDEX_OUT_OF_RANGE

        entry.endpoint = t.uint8_t(0)
        status = await self._ezsp.setMulticastTableEntry(idx, entry)
        if status[0] != t.EmberStatus.SUCCESS:
            LOGGER.warning(
                "Set MulticastTableEntry #%s for %s multicast id: %s",
                idx, entry.multicastId, status)
            return status[0]

        self._multicast.pop(group_id)
        self._available.add(idx)
        LOGGER.debug("Set MulticastTableEntry #%s for %s multicast id: %s",
                     idx, entry.multicastId, status)
        return status[0]
