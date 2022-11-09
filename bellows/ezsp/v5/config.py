import voluptuous as vol

from bellows.config import cv_uint16

from ..v4 import config as v4_config, types

EZSP_SCHEMA = {
    **v4_config.EZSP_SCHEMA,
}

del EZSP_SCHEMA["CONFIG_BROADCAST_ALARM_DATA_SIZE"]
del EZSP_SCHEMA["CONFIG_UNICAST_ALARM_DATA_SIZE"]

EZSP_POLICIES_SCH = {
    **v4_config.EZSP_POLICIES_SHARED,
    **{vol.Optional(policy.name): cv_uint16 for policy in types.EzspPolicyId},
}
