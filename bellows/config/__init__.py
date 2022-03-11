import voluptuous as vol
from zigpy.config import (  # noqa: F401 pylint: disable=unused-import
    CONF_DEVICE,
    CONF_DEVICE_PATH,
    CONFIG_SCHEMA,
    SCHEMA_DEVICE,
    CONF_NWK,
    CONF_NWK_KEY,
    CONF_NWK_PAN_ID,
    CONF_NWK_CHANNEL,
    CONF_NWK_CHANNELS,
    CONF_NWK_UPDATE_ID,
    CONF_NWK_TC_ADDRESS,
    CONF_NWK_TC_LINK_KEY,
    CONF_NWK_EXTENDED_PAN_ID,
    cv_boolean,
)

CONF_DEVICE_BAUDRATE = "baudrate"
CONF_EZSP_CONFIG = "ezsp_config"
CONF_EZSP_POLICIES = "ezsp_policies"
CONF_PARAM_SRC_RTG = "source_routing"
CONF_PARAM_UNK_DEV = "handle_unknown_devices"
CONF_FLOW_CONTROL = "flow_control"
CONF_FLOW_CONTROL_DEFAULT = "software"

SCHEMA_DEVICE = SCHEMA_DEVICE.extend(
    {
        vol.Optional(CONF_DEVICE_BAUDRATE, default=57600): int,
        vol.Optional(CONF_FLOW_CONTROL, default=CONF_FLOW_CONTROL_DEFAULT): vol.In(
            ("hardware", "software")
        ),
    },
)

CONFIG_SCHEMA = CONFIG_SCHEMA.extend(
    {
        vol.Required(CONF_DEVICE): SCHEMA_DEVICE,
        vol.Optional(CONF_PARAM_SRC_RTG, default=False): cv_boolean,
        vol.Optional(CONF_PARAM_UNK_DEV, default=False): cv_boolean,
        vol.Optional(CONF_EZSP_CONFIG, default={}): dict,
        vol.Optional(CONF_EZSP_POLICIES, default={}): vol.Schema(
            {vol.Optional(str): int}
        ),
    }
)

cv_uint16 = vol.All(int, vol.Range(min=0, max=65535))
