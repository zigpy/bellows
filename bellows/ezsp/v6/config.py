import voluptuous as vol

from bellows.config import cv_optional_int, cv_uint16, extend_vol_schema
from bellows.types import EzspConfigId, EzspPolicyId

from ..v4.config import EZSP_POLICIES_SHARED
from ..v5 import config as v5_config

EZSP_SCHEMA = extend_vol_schema(
    v5_config.EZSP_SCHEMA,
    {
        vol.Optional(EzspConfigId.CONFIG_RETRY_QUEUE_SIZE.name): cv_optional_int(min=0),
        vol.Optional(
            EzspConfigId.CONFIG_NEW_BROADCAST_ENTRY_THRESHOLD.name
        ): cv_optional_int(min=0),
        vol.Optional(
            EzspConfigId.CONFIG_BROADCAST_MIN_ACKS_NEEDED.name
        ): cv_optional_int(min=0),
        vol.Optional(
            EzspConfigId.CONFIG_TC_REJOINS_USING_WELL_KNOWN_KEY_TIMEOUT_S.name
        ): cv_optional_int(min=0),
    },
)

del EZSP_SCHEMA[v5_config.EzspConfigId.CONFIG_MOBILE_NODE_POLL_TIMEOUT.name]
del EZSP_SCHEMA[v5_config.EzspConfigId.CONFIG_RESERVED_MOBILE_CHILD_ENTRIES.name]
del EZSP_SCHEMA[v5_config.EzspConfigId.CONFIG_RF4CE_PAIRING_TABLE_SIZE.name]
del EZSP_SCHEMA[
    v5_config.EzspConfigId.CONFIG_RF4CE_PENDING_OUTGOING_PACKET_TABLE_SIZE.name
]

EZSP_POLICIES_SCH = {
    **EZSP_POLICIES_SHARED,
    **{vol.Optional(policy.name): cv_uint16 for policy in EzspPolicyId},
}
