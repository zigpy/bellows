import asyncio
import logging

import zigpy.device
import zigpy.endpoint
import zigpy.zdo
import zigpy.zdo.types as zdo_t

import bellows.types as t

# Test tone at 8dBm power level produced a max RSSI of -3dB
# -21dB corresponds to 100% LQI on the ZZH!
RSSI_MAX = -21

# Grounded antenna and then shielded produced a min RSSI of -92
# -89dB corresponds to 0% LQI on the ZZH!
RSSI_MIN = -89

SCAN_RETRIES = 3
SCAN_FAILURE_DELAY = 1.0  # seconds

ZDO_PROFILE = 0x0000
ZDO_ENDPOINT = 0

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

    def _send_loopback_reply(
        self, command_id: zdo_t.ZDOCmd, *, tsn: t.uint8_t, **kwargs
    ):
        """
        Constructs and sends back a loopback ZDO response.
        """

        message = t.uint8_t(tsn).serialize() + self._serialize(
            command_id, *kwargs.values()
        )

        LOGGER.debug("Sending loopback reply %s (%s), tsn=%s", command_id, kwargs, tsn)

        self.app.handle_message(
            sender=self.app._device,
            profile=ZDO_PROFILE,
            cluster=command_id,
            src_ep=ZDO_ENDPOINT,
            dst_ep=ZDO_ENDPOINT,
            message=message,
        )

    def handle_mgmt_nwk_update_req(
        self, hdr: zdo_t.ZDOHeader, NwkUpdate: zdo_t.NwkUpdate, *, dst_addressing
    ):
        """
        Handles ZDO `Mgmt_NWK_Update_req` sent to the coordinator.
        """

        self.create_catching_task(
            self.async_handle_mgmt_nwk_update_req(
                hdr, NwkUpdate, dst_addressing=dst_addressing
            )
        )

    async def async_handle_mgmt_nwk_update_req(
        self, hdr: zdo_t.ZDOHeader, NwkUpdate: zdo_t.NwkUpdate, *, dst_addressing
    ):
        if NwkUpdate.ScanDuration == zdo_t.NwkUpdate.CHANNEL_CHANGE_REQ:
            return
        elif (
            NwkUpdate.ScanDuration
            == zdo_t.NwkUpdate.CHANNEL_MASK_MANAGER_ADDR_CHANGE_REQ
        ):
            return

        # XXX: EmberZNet bug causes every other scan to:
        # 1. Immediately fail because a scan is already running (one shouldn't be).
        # 2. Actually start a scan.
        # 3. Never send the "scan completed" command, just the intermediate values.
        for i in range(SCAN_RETRIES):
            try:
                results = await self.app._ezsp.startScan(
                    t.EzspNetworkScanType.ENERGY_SCAN,
                    NwkUpdate.ScanChannels,
                    NwkUpdate.ScanDuration,
                )
                break
            except Exception:
                await asyncio.sleep(SCAN_FAILURE_DELAY)
        else:
            raise RuntimeError("Failed to scan")

        # Linearly remap RSSI to LQI
        rescaled_values = [
            int(100 * (clamp(v, RSSI_MIN, RSSI_MAX) - RSSI_MIN) / (RSSI_MAX - RSSI_MIN))
            for _, v in results
        ]

        self._send_loopback_reply(
            zdo_t.ZDOCmd.Mgmt_NWK_Update_rsp,
            Status=zdo_t.Status.SUCCESS,
            ScannedChannels=NwkUpdate.ScanChannels,
            TotalTransmissions=0,
            TransmissionFailures=0,
            EnergyValues=rescaled_values,
            tsn=hdr.tsn,
        )


class EZSPCoordinator(zigpy.device.Device):
    """Zigpy Device representing Coordinator."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        assert hasattr(self, "zdo")
        self.zdo = EZSPZDOEndpoint(self)
        self.endpoints[0] = self.zdo
