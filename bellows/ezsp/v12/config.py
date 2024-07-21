import voluptuous as vol

from bellows.config import cv_uint16
from bellows.types import EzspPolicyId

from ..v4.config import EZSP_POLICIES_SHARED
from ..v11 import config as v11_config

EZSP_SCHEMA = {
    **v11_config.EZSP_SCHEMA,
}

EZSP_POLICIES_SCH = {
    **EZSP_POLICIES_SHARED,
    **{vol.Optional(policy.name): cv_uint16 for policy in EzspPolicyId},
}
