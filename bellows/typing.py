"""Typing helpers for bellows."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import bellows.uart
    import bellows.zigbee.application

    GatewayType = bellows.uart.Gateway
    ControllerApplicationType = bellows.zigbee.application.ControllerApplication
else:
    # pylint: disable=invalid-name
    ControllerApplicationType = "ControllerApplication"
    GatewayType = "Gateway"
