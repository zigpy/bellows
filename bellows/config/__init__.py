import voluptuous as vol
from zigpy.config import (  # noqa: F401 pylint: disable=unused-import
    CONF_DEVICE,
    CONF_DEVICE_PATH,
    CONFIG_SCHEMA,
    SCHEMA_DEVICE,
    cv_boolean,
)

from .ezsp import EZSP_SCHEMA

CONF_DEVICE_BAUDRATE = "baudrate"
CONF_EZSP_CONFIG = "ezsp_config"
CONF_PARAM_SRC_RTG = "source_routing"

SCHEMA_DEVICE = SCHEMA_DEVICE.extend(
    {vol.Optional(CONF_DEVICE_BAUDRATE, default=57600): int}
)

CONFIG_SCHEMA = CONFIG_SCHEMA.extend(
    {
        vol.Required(CONF_DEVICE): SCHEMA_DEVICE,
        vol.Optional(CONF_PARAM_SRC_RTG, default=False): cv_boolean,
        vol.Optional(CONF_EZSP_CONFIG, default={}): vol.Schema(EZSP_SCHEMA),
    }
)
