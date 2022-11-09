import voluptuous as vol

from bellows.config import cv_uint16

from ..v4.config import EZSP_POLICIES_SHARED
from ..v8 import config as v8_config
from .types import EzspPolicyId

EZSP_SCHEMA = {
    **v8_config.EZSP_SCHEMA,
}

EZSP_POLICIES_SCH = {
    **EZSP_POLICIES_SHARED,
    **{vol.Optional(policy.name): cv_uint16 for policy in EzspPolicyId},
}
