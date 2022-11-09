import voluptuous as vol

from bellows.config import cv_optional_int, cv_uint16, extend_vol_schema

from ..v4.config import EZSP_POLICIES_SHARED
from ..v7 import config as v7_config
from .types import EzspConfigId, EzspPolicyId

EZSP_SCHEMA = extend_vol_schema(
    v7_config.EZSP_SCHEMA,
    {
        vol.Optional(EzspConfigId.CONFIG_NEIGHBOR_TABLE_SIZE.name): cv_optional_int(
            min=8, max=26
        ),
        vol.Optional(EzspConfigId.CONFIG_MAX_END_DEVICE_CHILDREN.name): cv_optional_int(
            min=0, max=64
        ),
        vol.Optional(
            EzspConfigId.CONFIG_END_DEVICE_POLL_TIMEOUT.name, default=8
        ): cv_optional_int(min=0, max=14),
        vol.Optional(EzspConfigId.CONFIG_KEY_TABLE_SIZE.name): cv_optional_int(min=0),
        vol.Optional(
            EzspConfigId.CONFIG_TC_REJOINS_USING_WELL_KNOWN_KEY_TIMEOUT_S.name,
            default=90,
        ): cv_optional_int(min=0),
    },
)

EZSP_POLICIES_SCH = {
    **EZSP_POLICIES_SHARED,
    **{vol.Optional(policy.name): cv_uint16 for policy in EzspPolicyId},
}
