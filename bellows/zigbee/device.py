from __future__ import annotations

import logging

import zigpy.device
import zigpy.endpoint
import zigpy.profiles.zgp
import zigpy.profiles.zha
import zigpy.profiles.zll
import zigpy.zdo.types as zdo_t

import bellows.types as t

LOGGER = logging.getLogger(__name__)

PROFILE_TO_DEVICE_TYPE = {
    zigpy.profiles.zha.PROFILE_ID: zigpy.profiles.zha.DeviceType,
    zigpy.profiles.zll.PROFILE_ID: zigpy.profiles.zll.DeviceType,
    zigpy.profiles.zgp.PROFILE_ID: zigpy.profiles.zgp.DeviceType,
}


class EZSPEndpoint(zigpy.endpoint.Endpoint):
    def __init__(
        self,
        device: zigpy.device.Device,
        endpoint_id: int,
        descriptor: zdo_t.SimpleDescriptor,
    ) -> None:
        super().__init__(device, endpoint_id)

        self.profile_id = descriptor.profile

        if self.profile_id in PROFILE_TO_DEVICE_TYPE:
            self.device_type = PROFILE_TO_DEVICE_TYPE[self.profile_id](
                descriptor.device_type
            )
        else:
            self.device_type = descriptor.device_type

        for cluster in descriptor.input_clusters:
            self.add_input_cluster(cluster)

        for cluster in descriptor.output_clusters:
            self.add_output_cluster(cluster)

        self.status = zigpy.endpoint.Status.ZDO_INIT

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
