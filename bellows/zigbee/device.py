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
    @classmethod
    def from_descriptor(
        cls,
        device: zigpy.device.Device,
        endpoint_id: int,
        descriptor: zdo_t.SimpleDescriptor,
    ) -> None:
        ep = cls(device, endpoint_id)
        ep.profile_id = descriptor.profile

        if ep.profile_id in PROFILE_TO_DEVICE_TYPE:
            ep.device_type = PROFILE_TO_DEVICE_TYPE[ep.profile_id](
                descriptor.device_type
            )
        else:
            ep.device_type = descriptor.device_type

        for cluster in descriptor.input_clusters:
            ep.add_input_cluster(cluster)

        for cluster in descriptor.output_clusters:
            ep.add_output_cluster(cluster)

        ep.status = zigpy.endpoint.Status.ZDO_INIT

        return ep

    @property
    def manufacturer(self) -> str:
        """Manufacturer."""
        return "Silicon Labs"

    @property
    def model(self) -> str:
        """Model."""
        return "EZSP"


class EZSPGroupEndpoint(EZSPEndpoint):
    async def add_to_group(self, grp_id: int, name: str = None) -> t.EmberStatus:
        if grp_id in self.member_of:
            return

        app = self.device.application
        status = await app.multicast.subscribe(grp_id)
        if status != t.sl_Status.OK:
            raise ValueError(f"Couldn't subscribe to 0x{grp_id:04x} group")

        group = app.groups.add_group(grp_id, name)
        group.add_member(self)

    async def remove_from_group(self, grp_id: int) -> None:
        if grp_id not in self.member_of:
            return

        app = self.device.application
        status = await app.multicast.unsubscribe(grp_id)
        if status != t.sl_Status.OK:
            raise ValueError(f"Couldnt't unsubscribe from 0x{grp_id:04x} group")

        app.groups[grp_id].remove_member(self)
