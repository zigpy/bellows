from __future__ import annotations

import logging
import typing

import zigpy.device
import zigpy.endpoint
import zigpy.util
import zigpy.zdo
import zigpy.zdo.types as zdo_t
import zigpy.profiles.zha
import zigpy.profiles.zll
import zigpy.profiles.zgp

import bellows.types as t

if typing.TYPE_CHECKING:
    import zigpy.application  # pragma: no cover

LOGGER = logging.getLogger(__name__)


class EZSPEndpoint(zigpy.endpoint.Endpoint):
    def __init__(self, device, descriptor: zdo_t.SimpleDescriptor) -> None:
        self._desc = descriptor
        super().__init__(device, descriptor.endpoint)

    @property
    def manufacturer(self) -> str:
        """Manufacturer."""
        return "Silicon Labs"

    @property
    def model(self) -> str:
        """Model."""
        return "EZSP"

    async def initialize(self) -> None:
        if self.profile_id is not None or self.status == zigpy.endpoint.Status.ENDPOINT_INACTIVE:
            self.info("Endpoint already initialized")
        else:
            sd = self._desc
            self.info("Reusing endpoint information: %s", sd)
            self.profile_id = sd.profile
            self.device_type = sd.device_type

            if self.profile_id == zigpy.profiles.zha.PROFILE_ID:
                self.device_type = zigpy.profiles.zha.DeviceType(self.device_type)
            elif self.profile_id == zigpy.profiles.zll.PROFILE_ID:
                self.device_type = zigpy.profiles.zll.DeviceType(self.device_type)
            elif self.profile_id == zigpy.profiles.zgp.PROFILE_ID:
                self.device_type = zigpy.profiles.zgp.DeviceType(self.device_type)

            for cluster in sd.input_clusters:
                self.add_input_cluster(cluster)

            for cluster in sd.output_clusters:
                self.add_output_cluster(cluster)

        self.status = zigpy.endpoint.Status.ENDPOINT_INACTIVE

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
