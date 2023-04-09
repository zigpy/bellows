import pytest
import zigpy.endpoint
import zigpy.types as t
import zigpy.zdo.types as zdo_t

from bellows.zigbee.device import EZSPCoordinator, EZSPEndpoint

from tests.async_mock import AsyncMock
from tests.test_application import app, ezsp_mock, make_app


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
