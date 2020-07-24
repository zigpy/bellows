from . import types
from ..v4 import config as v4_config

c = types.EzspConfigId
zdo_flags = types.EmberZdoConfigurationFlags

_deletions = (
    "EZSP_CONFIG_BROADCAST_ALARM_DATA_SIZE",
    "EZSP_CONFIG_UNICAST_ALARM_DATA_SIZE",
)

EZSP_SCHEMA = {
    **{k: v for k, v in v4_config.EZSP_SCHEMA.items() if k not in _deletions}
}

del _deletions
