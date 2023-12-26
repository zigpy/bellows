"""Protocol version 13 specific structs."""

from __future__ import annotations

from bellows.ezsp.v12.types.struct import *  # noqa: F401, F403
from bellows.ezsp.v13.types import named
import bellows.types as t
from bellows.types.struct import EzspStruct


class sl_zb_sec_man_context_t(EzspStruct):
    """Context for Zigbee Security Manager operations."""

    # The type of key being referenced.
    core_key_type: named.sl_zb_sec_man_key_type_t
    # The index of the referenced key.
    key_index: t.uint8_t
    # The type of key derivation operation to perform on a key.
    derived_type: named.sl_zb_sec_man_derived_key_type_t
    # The EUI64 associated with this key.
    eui64: t.EUI64
    # Multi-network index.
    multi_network_index: t.uint8_t
    # Flag bitmask.
    flags: named.sl_zb_sec_man_flags_t
    # Algorithm to use with this key (for PSA APIs)
    psa_key_alg_permission: t.uint32_t


class sl_zb_sec_man_network_key_info_t(EzspStruct):
    """The metadata pertaining to an network key."""

    network_key_set: t.Bool
    alternate_network_key_set: t.Bool
    network_key_sequence_number: t.uint8_t
    alt_network_key_sequence_number: t.uint8_t
    network_key_frame_counter: t.uint32_t
