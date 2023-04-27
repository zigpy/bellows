from __future__ import annotations

import logging
import typing

import zigpy.device
import zigpy.endpoint
import zigpy.util
import zigpy.zdo

import bellows.types as t

if typing.TYPE_CHECKING:
    import zigpy.application  # pragma: no cover

LOGGER = logging.getLogger(__name__)


class EZSPEndpoint(zigpy.endpoint.Endpoint):
    @property
    def manufacturer(self) -> str:
        """Manufacturer."""
        return "Silicon Labs"

    @property
    def model(self) -> str:
        """Model."""
        return "EZSP"

    async def add_to_group(self, grp_id: int, name: str = None) -> t.EmberStatus:
        if grp_id in self.member_of:
            return t.EmberStatus.SUCCESS

        app = self.device.application
        status = await app.multicast.subscribe(grp_id)
        if status != t.EmberStatus.SUCCESS:
            self.debug("Couldn't subscribe to 0x%04x group", grp_id)
            return status

        group = app.groups.add_group(grp_id, name)
        group.add_member(self)
        return status

    async def remove_from_group(self, grp_id: int) -> t.EmberStatus:
        if grp_id not in self.member_of:
            return t.EmberStatus.SUCCESS

        app = self.device.application
        status = await app.multicast.unsubscribe(grp_id)
        if status != t.EmberStatus.SUCCESS:
            self.debug("Couldn't unsubscribe 0x%04x group", grp_id)
            return status

        app.groups[grp_id].remove_member(self)
        return status
