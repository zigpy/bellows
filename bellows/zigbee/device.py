from __future__ import annotations

import logging
import typing

import zigpy.device
import zigpy.endpoint
import zigpy.util
import zigpy.zdo
import zigpy.zdo.types as zdo_t

import bellows.types as t

if typing.TYPE_CHECKING:
    import zigpy.application  # pragma: no cover

# Test tone at 8dBm power level produced a max RSSI of -3dB
# -21dB corresponds to 100% LQI on the ZZH!
RSSI_MAX = -21

# Grounded antenna and then shielded produced a min RSSI of -92
# -89dB corresponds to 0% LQI on the ZZH!
RSSI_MIN = -89

LOGGER = logging.getLogger(__name__)


def clamp(v: float, minimum: float, maximum: float) -> float:
    """
    Restricts `v` to be between `minimum` and `maximum`.
    """

    return min(max(minimum, v), maximum)


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


class EZSPZDOEndpoint(zigpy.zdo.ZDO):
    @property
    def app(self) -> zigpy.application.ControllerApplication:
        return self.device.application

    def make_zdo_reply(self, cmd: zdo_t.ZDOCmd, **kwargs):
        """
        Provides a way to create ZDO commands with schemas. Currently does nothing.
        """
        return list(kwargs.values())

    @zigpy.util.retryable_request
    async def request(self, command, *args, use_ieee=False):
        if (
            command == zdo_t.ZDOCmd.Mgmt_NWK_Update_req
            and args[0].ScanDuration < zdo_t.NwkUpdate.CHANNEL_CHANGE_REQ
        ):
            return await self._ezsp_energy_scan(*args)

        return await super().request(command, *args, use_ieee=use_ieee)

    async def _ezsp_energy_scan(self, NwkUpdate: zdo_t.NwkUpdate):
        results = await self.app._ezsp.startScan(
            t.EzspNetworkScanType.ENERGY_SCAN,
            NwkUpdate.ScanChannels,
            NwkUpdate.ScanDuration,
        )

        # Linearly remap RSSI to LQI
        rescaled_values = [
            int(100 * (clamp(v, RSSI_MIN, RSSI_MAX) - RSSI_MIN) / (RSSI_MAX - RSSI_MIN))
            for _, v in results
        ]

        return self.make_zdo_reply(
            cmd=zdo_t.ZDOCmd.Mgmt_NWK_Update_rsp,
            Status=zdo_t.Status.SUCCESS,
            ScannedChannels=NwkUpdate.ScanChannels,
            TotalTransmissions=0,
            TransmissionFailures=0,
            EnergyValues=rescaled_values,
        )


class EZSPCoordinator(zigpy.device.Device):
    """Zigpy Device representing Coordinator."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        assert hasattr(self, "zdo")
        self.zdo = EZSPZDOEndpoint(self)
        self.endpoints[0] = self.zdo
