import logging

from bellows import types as t

LOGGER = logging.getLogger(__name__)


class Multicast:
    """Multicast table controller for EZSP."""

    def __init__(self, ezsp):
        self._ezsp = ezsp
        self._multicast = {}
        self._available = set()

    async def _initialize(self) -> None:
        self._multicast = {}
        self._available = set()

        status, size = await self._ezsp.getConfigurationValue(
            t.EzspConfigId.CONFIG_MULTICAST_TABLE_SIZE
        )
        if t.sl_Status.from_ember_status(status) != t.sl_Status.OK:
            return

        for i in range(0, size):
            status, entry = await self._ezsp.getMulticastTableEntry(i)
            if t.sl_Status.from_ember_status(status) != t.sl_Status.OK:
                LOGGER.error("Couldn't get MulticastTableEntry #%s: %s", i, status)
                continue
            LOGGER.debug("MulticastTableEntry[%s] = %s", i, entry)
            if entry.endpoint != 0:
                self._multicast[entry.multicastId] = (entry, i)
            else:
                self._available.add(i)

    async def startup(self, coordinator) -> None:
        await self._initialize()
        for ep_id, ep in coordinator.endpoints.items():
            if ep_id == 0:
                continue
            for group_id in ep.member_of:
                await self.subscribe(group_id)

    async def subscribe(self, group_id) -> t.sl_Status:
        if group_id in self._multicast:
            LOGGER.debug("%s is already subscribed", t.EmberMulticastId(group_id))
            return t.sl_Status.OK

        try:
            idx = self._available.pop()
        except KeyError:
            LOGGER.error("No more available slots MulticastId subscription")
            return t.sl_Status.INVALID_INDEX
        entry = t.EmberMulticastTableEntry()
        entry.endpoint = t.uint8_t(1)
        entry.multicastId = t.EmberMulticastId(group_id)
        entry.networkIndex = t.uint8_t(0)
        status = await self._ezsp.setMulticastTableEntry(idx, entry)
        if t.sl_Status.from_ember_status(status[0]) != t.sl_Status.OK:
            LOGGER.warning(
                "Set MulticastTableEntry #%s for %s multicast id: %s",
                idx,
                entry.multicastId,
                status,
            )
            self._available.add(idx)
            return status[0]

        self._multicast[entry.multicastId] = (entry, idx)
        LOGGER.debug(
            "Set MulticastTableEntry #%s for %s multicast id: %s",
            idx,
            entry.multicastId,
            status,
        )
        return status[0]

    async def unsubscribe(self, group_id) -> t.sl_Status:
        try:
            entry, idx = self._multicast[group_id]
        except KeyError:
            LOGGER.error(
                "Couldn't find MulticastTableEntry for %s multicast_id", group_id
            )
            return t.sl_Status.INVALID_INDEX

        entry.endpoint = t.uint8_t(0)
        status = await self._ezsp.setMulticastTableEntry(idx, entry)
        if t.sl_Status.from_ember_status(status[0]) != t.sl_Status.OK:
            LOGGER.warning(
                "Set MulticastTableEntry #%s for %s multicast id: %s",
                idx,
                entry.multicastId,
                status,
            )
            return status[0]

        self._multicast.pop(group_id)
        self._available.add(idx)
        LOGGER.debug(
            "Set MulticastTableEntry #%s for %s multicast id: %s",
            idx,
            entry.multicastId,
            status,
        )
        return status[0]
