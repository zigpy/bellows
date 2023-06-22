from __future__ import annotations

import dataclasses

import bellows.ezsp.v4.types as types_v4
import bellows.ezsp.v6.types as types_v6
import bellows.types as t


@dataclasses.dataclass(frozen=True)
class RuntimeConfig:
    config_id: t.enum8
    value: int
    minimum: bool = False


DEFAULT_CONFIG_COMMON = [
    RuntimeConfig(
        config_id=types_v4.EzspConfigId.CONFIG_INDIRECT_TRANSMISSION_TIMEOUT,
        value=7680,
    ),
    RuntimeConfig(
        config_id=types_v4.EzspConfigId.CONFIG_STACK_PROFILE,
        value=2,
    ),
    RuntimeConfig(
        config_id=types_v4.EzspConfigId.CONFIG_SUPPORTED_NETWORKS,
        value=1,
        minimum=True,
    ),
    RuntimeConfig(
        config_id=types_v4.EzspConfigId.CONFIG_MULTICAST_TABLE_SIZE,
        value=16,
        minimum=True,
    ),
    RuntimeConfig(
        config_id=types_v4.EzspConfigId.CONFIG_TRUST_CENTER_ADDRESS_CACHE_SIZE,
        value=2,
        minimum=True,
    ),
    RuntimeConfig(
        config_id=types_v4.EzspConfigId.CONFIG_SECURITY_LEVEL,
        value=5,
    ),
    RuntimeConfig(
        config_id=types_v4.EzspConfigId.CONFIG_ADDRESS_TABLE_SIZE,
        value=16,
        minimum=True,
    ),
    RuntimeConfig(
        config_id=types_v4.EzspConfigId.CONFIG_PAN_ID_CONFLICT_REPORT_THRESHOLD,
        value=2,
    ),
    RuntimeConfig(
        config_id=types_v4.EzspConfigId.CONFIG_KEY_TABLE_SIZE,
        value=4,
        minimum=True,
    ),
    RuntimeConfig(
        config_id=types_v4.EzspConfigId.CONFIG_MAX_END_DEVICE_CHILDREN,
        value=32,
        minimum=True,
    ),
    RuntimeConfig(
        config_id=types_v4.EzspConfigId.CONFIG_APPLICATION_ZDO_FLAGS,
        value=(
            t.EmberZdoConfigurationFlags.APP_RECEIVES_SUPPORTED_ZDO_REQUESTS
            | t.EmberZdoConfigurationFlags.APP_HANDLES_UNSUPPORTED_ZDO_REQUESTS
        ),
    ),
    # Must be set last
    RuntimeConfig(types_v4.EzspConfigId.CONFIG_PACKET_BUFFER_COUNT, value=0xFF),
]

DEFAULT_CONFIG_LEGACY = [
    RuntimeConfig(
        config_id=types_v4.EzspConfigId.CONFIG_SOURCE_ROUTE_TABLE_SIZE,
        value=16,
        minimum=True,
    ),
    RuntimeConfig(
        config_id=types_v4.EzspConfigId.CONFIG_END_DEVICE_POLL_TIMEOUT,
        value=60,
    ),
    RuntimeConfig(
        config_id=types_v4.EzspConfigId.CONFIG_END_DEVICE_POLL_TIMEOUT_SHIFT,
        value=8,
    ),
] + DEFAULT_CONFIG_COMMON


DEFAULT_CONFIG_NEW = [
    RuntimeConfig(
        config_id=types_v6.EzspConfigId.CONFIG_SOURCE_ROUTE_TABLE_SIZE,
        value=200,
        minimum=True,
    ),
    RuntimeConfig(
        config_id=types_v6.EzspConfigId.CONFIG_END_DEVICE_POLL_TIMEOUT,
        value=8,
    ),
    RuntimeConfig(
        config_id=(
            types_v6.EzspConfigId.CONFIG_TC_REJOINS_USING_WELL_KNOWN_KEY_TIMEOUT_S
        ),
        value=90,
    ),
] + DEFAULT_CONFIG_COMMON


DEFAULT_CONFIG = {
    4: DEFAULT_CONFIG_LEGACY,
    5: DEFAULT_CONFIG_LEGACY,
    6: DEFAULT_CONFIG_LEGACY,
    7: DEFAULT_CONFIG_NEW,
    8: DEFAULT_CONFIG_NEW,
    9: DEFAULT_CONFIG_NEW,
    10: DEFAULT_CONFIG_NEW,
    11: DEFAULT_CONFIG_NEW,
    12: DEFAULT_CONFIG_NEW,
}
