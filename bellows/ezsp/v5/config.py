import voluptuous as vol

from bellows.config import cv_uint16, extend_vol_schema
from bellows.types import EzspConfigId, EzspPolicyId  # noqa: F401

from ..v4 import config as v4_config
from ..v4.config import EZSP_POLICIES_SHARED

EZSP_SCHEMA = extend_vol_schema(v4_config.EZSP_SCHEMA, {})

del EZSP_SCHEMA[v4_config.EzspConfigId.CONFIG_BROADCAST_ALARM_DATA_SIZE.name]
del EZSP_SCHEMA[v4_config.EzspConfigId.CONFIG_UNICAST_ALARM_DATA_SIZE.name]

EZSP_POLICIES_SCH = {
    **EZSP_POLICIES_SHARED,
    **{vol.Optional(policy.name): cv_uint16 for policy in EzspPolicyId},
}
