from ..v5 import config as v5_config

_deletions = ()

EZSP_SCHEMA = {k: v for k, v in v5_config.EZSP_SCHEMA.items() if k not in _deletions}

del _deletions
