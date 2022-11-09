import voluptuous as vol

from bellows.config import cv_optional_int, cv_uint16

from ..v4.config import EZSP_POLICIES_SHARED
from ..v6 import config as v6_config
from .types import EzspConfigId, EzspPolicyId

EZSP_SCHEMA = {
    **v6_config.EZSP_SCHEMA,
    vol.Optional(EzspConfigId.CONFIG_END_DEVICE_POLL_TIMEOUT.name): cv_optional_int(
        min=0, max=14
    ),
}

del EZSP_SCHEMA["CONFIG_END_DEVICE_POLL_TIMEOUT_SHIFT"]

EZSP_POLICIES_SCH = {
    **EZSP_POLICIES_SHARED,
    **{vol.Optional(policy.name): cv_uint16 for policy in EzspPolicyId},
}
