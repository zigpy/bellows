import voluptuous as vol

from bellows.config import cv_uint16

from ..v4 import config as v4_config, types

_deletions = ("CONFIG_BROADCAST_ALARM_DATA_SIZE", "CONFIG_UNICAST_ALARM_DATA_SIZE")

EZSP_SCHEMA = {k: v for k, v in v4_config.EZSP_SCHEMA.items() if k not in _deletions}

del _deletions

EZSP_POLICIES_SCH = {
    **v4_config.EZSP_POLICIES_SHARED,
    **{vol.Optional(policy.name): cv_uint16 for policy in types.EzspPolicyId},
}
