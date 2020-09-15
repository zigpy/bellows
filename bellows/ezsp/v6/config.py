import voluptuous as vol

from bellows.config import cv_uint16

from ..v4.config import EZSP_POLICIES_SHARED
from ..v5 import config as v5_config
from .types import EzspConfigId, EzspPolicyId

_deletions = (
    "CONFIG_MOBILE_NODE_POLL_TIMEOUT",
    "CONFIG_RESERVED_MOBILE_CHILD_ENTRIES",
    "CONFIG_RF4CE_PAIRING_TABLE_SIZE",
    "CONFIG_RF4CE_PENDING_OUTGOING_PACKET_TABLE_SIZE",
)

EZSP_SCHEMA = {
    **{k: v for k, v in v5_config.EZSP_SCHEMA.items() if k not in _deletions},
    vol.Optional(EzspConfigId.CONFIG_RETRY_QUEUE_SIZE.name): vol.All(
        int, vol.Range(min=0)
    ),
    vol.Optional(EzspConfigId.CONFIG_NEW_BROADCAST_ENTRY_THRESHOLD.name): vol.All(
        int, vol.Range(min=0)
    ),
    vol.Optional(EzspConfigId.CONFIG_BROADCAST_MIN_ACKS_NEEDED.name): vol.All(
        int, vol.Range(min=0)
    ),
    vol.Optional(
        EzspConfigId.CONFIG_TC_REJOINS_USING_WELL_KNOWN_KEY_TIMEOUT_S.name
    ): vol.All(int, vol.Range(min=0)),
}

del _deletions

EZSP_POLICIES_SCH = {
    **EZSP_POLICIES_SHARED,
    **{vol.Optional(policy.name): cv_uint16 for policy in EzspPolicyId},
}
