"""Protocol version 12 specific structs."""

from __future__ import annotations

from bellows.ezsp.v12.types import named
import bellows.types as t
from bellows.types.struct import EzspStruct


class SecurityManagerContext(EzspStruct):
    """Context for Zigbee Security Manager operations."""

    # The type of key being referenced.
    core_key_type: named.SecurityManagerKeyType
    # The index of the referenced key.
    key_index: t.uint8_t
    # The type of key derivation operation to perform on a key.
    derived_type: named.SecurityManagerDerivedKeyType
    # The EUI64 associated with this key.
    eui64: t.EUI64
    # Multi-network index.
    multi_network_index: t.uint8_t
    # Flag bitmask.
    flags: named.SecurityManagerContextFlags
    # Algorithm to use with this key (for PSA APIs)
    psa_key_alg_permission: t.uint32_t


class SecurityManagerAPSKeyMetadata(EzspStruct):
    """Metadata for APS link keys."""

    # Bitmask of key properties
    bitmask: t.EmberKeyStructBitmask
    # Outgoing frame counter.
    outgoing_frame_counter: t.uint32_t
    # Incoming frame counter.
    incoming_frame_counter: t.uint32_t
    # Remaining lifetime (for transient keys).
    ttl_in_seconds: t.uint16_t


class SecurityManagerNetworkKeyInfo(EzspStruct):
    """The metadata pertaining to an network key."""

    network_key_set: t.Bool
    alternate_network_key_set: t.Bool
    network_key_sequence_number: t.uint8_t
    alt_network_key_sequence_number: t.uint8_t
