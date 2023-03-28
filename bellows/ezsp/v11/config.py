import voluptuous as vol

from bellows.config import cv_uint16

from ..v4.config import EZSP_POLICIES_SHARED
from ..v9 import config as v9_config
from .types import EzspPolicyId

EZSP_SCHEMA = {
    **v9_config.EZSP_SCHEMA,
}

EZSP_POLICIES_SCH = {
    **EZSP_POLICIES_SHARED,
    **{vol.Optional(policy.name): cv_uint16 for policy in EzspPolicyId},
}
