from ..v4 import config as v4_config

_deletions = ("CONFIG_BROADCAST_ALARM_DATA_SIZE", "CONFIG_UNICAST_ALARM_DATA_SIZE")

EZSP_SCHEMA = {k: v for k, v in v4_config.EZSP_SCHEMA.items() if k not in _deletions}

del _deletions
