import voluptuous as vol

from bellows.config import cv_optional_int, cv_uint16, extend_vol_schema
from bellows.types import EzspConfigId, EzspDecisionBitmask, EzspPolicyId

from ..v4 import config as v4_config
from ..v7 import config as v7_config

# EZSPv8 replaces the trust center decisions with a decision bitmask
EZSP_POLICIES_SHARED = {
    **{
        key: value
        for key, value in v4_config.EZSP_POLICIES_SHARED.items()
        if key != EzspPolicyId.TRUST_CENTER_POLICY.name
    },
    # Same as the NCP's boot default and the SDK host framework. Trust Center rejoins
    # are always accepted. New joins still need permit joining and the well-known
    # transient key, which only exists while joins are allowed.
    vol.Optional(
        EzspPolicyId.TRUST_CENTER_POLICY.name,
        default=(
            EzspDecisionBitmask.ALLOW_JOINS
            | EzspDecisionBitmask.ALLOW_UNSECURED_REJOINS
        ),
    ): cv_uint16,
}

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
            EzspConfigId.CONFIG_TC_REJOINS_USING_WELL_KNOWN_KEY_TIMEOUT_S.name
        ): cv_optional_int(min=0),
    },
)

EZSP_POLICIES_SCH = {
    **EZSP_POLICIES_SHARED,
    **{vol.Optional(policy.name): cv_uint16 for policy in EzspPolicyId},
}
