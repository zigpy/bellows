import asyncio

import pytest
import zigpy.endpoint
import zigpy.types as t
import zigpy.zdo.types as zdo_t

from bellows.zigbee.device import EZSPCoordinator, EZSPEndpoint

from tests.async_mock import AsyncMock
from tests.test_application import app, ezsp_mock


@pytest.fixture
def app_and_coordinator(app):
    app.state.node_info.ieee = t.EUI64.convert("aa:bb:cc:dd:ee:ff:00:11")
    app.state.node_info.nwk = t.NWK(0x0000)

    coordinator = EZSPCoordinator(
        application=app,
        ieee=app.state.node_info.ieee,
        nwk=app.state.node_info.nwk,
    )
    coordinator.node_desc = zdo_t.NodeDescriptor()

    app.devices[app.state.node_info.ieee] = coordinator

    # The coordinator device does not respond to attribute reads
    coordinator.endpoints[1] = EZSPEndpoint(coordinator, 1)
    coordinator.endpoints[1].status = zigpy.endpoint.Status.ZDO_INIT

    return app, coordinator


@pytest.mark.parametrize(
    "scan_results",
    [
        # Normal
        [
            -39,
            -30,
            -26,
            -33,
            -23,
            -53,
            -42,
            -46,
            -69,
            -75,
            -49,
            -67,
            -57,
            -81,
            -29,
            -40,
        ],
        # Maximum
        [1] * (26 - 11),
        # Minimum
        [-200] * (26 - 11),
    ],
)
async def test_energy_scanning(app_and_coordinator, scan_results):
    app, coordinator = app_and_coordinator

    app._ezsp.startScan = AsyncMock(
        return_value=list(zip(range(11, 26 + 1), scan_results))
    )

    _, scanned_channels, *_, energy_values = await coordinator.zdo.Mgmt_NWK_Update_req(
        zdo_t.NwkUpdate(
            ScanChannels=t.Channels.ALL_CHANNELS,
            ScanDuration=0x02,
            ScanCount=1,
        )
    )

    assert scanned_channels == t.Channels.ALL_CHANNELS
    assert len(energy_values) == len(scan_results)
