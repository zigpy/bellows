from __future__ import annotations

from typing import Any

import voluptuous as vol
from zigpy.config import (
    CONF_DEVICE as CONF_DEVICE,
    CONF_DEVICE_BAUDRATE as CONF_DEVICE_BAUDRATE,
    CONF_DEVICE_PATH as CONF_DEVICE_PATH,
    CONF_NWK as CONF_NWK,
    CONF_NWK_CHANNEL as CONF_NWK_CHANNEL,
    CONF_NWK_CHANNELS as CONF_NWK_CHANNELS,
    CONF_NWK_EXTENDED_PAN_ID as CONF_NWK_EXTENDED_PAN_ID,
    CONF_NWK_KEY as CONF_NWK_KEY,
    CONF_NWK_PAN_ID as CONF_NWK_PAN_ID,
    CONF_NWK_TC_ADDRESS as CONF_NWK_TC_ADDRESS,
    CONF_NWK_TC_LINK_KEY as CONF_NWK_TC_LINK_KEY,
    CONF_NWK_UPDATE_ID as CONF_NWK_UPDATE_ID,
    CONFIG_SCHEMA as CONFIG_SCHEMA,
)
from zigpy.config.validators import cv_boolean as cv_boolean

CONF_BELLOWS_CONFIG = "bellows_config"
CONF_MANUAL_SOURCE_ROUTING = "manual_source_routing"

CONF_USE_THREAD = "use_thread"
CONF_EZSP_CONFIG = "ezsp_config"
CONF_EZSP_POLICIES = "ezsp_policies"
CONF_PARAM_MAX_WATCHDOG_FAILURES = "max_watchdog_failures"

CONFIG_SCHEMA = CONFIG_SCHEMA.extend(
    {
        vol.Optional(CONF_PARAM_MAX_WATCHDOG_FAILURES, default=4): int,
        vol.Optional(CONF_EZSP_CONFIG, default={}): dict,
        vol.Optional(CONF_EZSP_POLICIES, default={}): vol.Schema(
            {vol.Optional(str): int}
        ),
        vol.Optional(CONF_USE_THREAD, default=True): cv_boolean,
        # The above config really should belong in here
        vol.Optional(CONF_BELLOWS_CONFIG, default={}): vol.Schema(
            {
                vol.Optional(CONF_MANUAL_SOURCE_ROUTING, default=False): bool,
            }
        ),
    }
)

cv_uint16 = vol.All(int, vol.Range(min=0, max=65535))


def cv_optional_int(min: int | None = None, max: int | None = None) -> vol.All:
    """Voluptuous validator to create an optional integer validator."""

    return vol.Maybe(vol.All(int, vol.Range(min=min, max=max)))


def extend_vol_schema(base: dict[Any, Any], changes: dict[Any, Any]) -> dict[Any, Any]:
    """Extend a Voluptuous schema. Simply overriding keys does not work."""

    return {**{k: v for k, v in base.items() if k not in changes}, **changes}
