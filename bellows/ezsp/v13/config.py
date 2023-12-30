import voluptuous as vol

from bellows.config import cv_uint16

from ..v4.config import EZSP_POLICIES_SHARED
from ..v12 import config as v12_config
from .types import EzspPolicyId

EZSP_SCHEMA = {
    **v12_config.EZSP_SCHEMA,
}

EZSP_POLICIES_SCH = {
    **EZSP_POLICIES_SHARED,
    **{vol.Optional(policy.name): cv_uint16 for policy in EzspPolicyId},
}
