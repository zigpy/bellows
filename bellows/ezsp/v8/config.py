import voluptuous as vol

from bellows.config import cv_optional_int, cv_uint16

from ..v4.config import EZSP_POLICIES_SHARED
from ..v7 import config as v7_config
from .types import EzspConfigId, EzspPolicyId

EZSP_SCHEMA = {
    **v7_config.EZSP_SCHEMA,
    vol.Optional(EzspConfigId.CONFIG_NEIGHBOR_TABLE_SIZE.name): cv_optional_int(
        min=8, max=26
    ),
    vol.Optional(EzspConfigId.CONFIG_MAX_END_DEVICE_CHILDREN.name): cv_optional_int(
        min=0, max=64
    ),
}

EZSP_POLICIES_SCH = {
    **EZSP_POLICIES_SHARED,
    **{vol.Optional(policy.name): cv_uint16 for policy in EzspPolicyId},
}
