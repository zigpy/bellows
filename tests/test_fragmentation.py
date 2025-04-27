from unittest.mock import MagicMock

import pytest

from bellows.ezsp.fragmentation import FragmentManager


async def test_single_fragment_complete():
    """
    If we receive a single-fragment message (fragment_count=1, fragment_index=0),
    the manager should immediately report completion.
    """
    frag_manager = FragmentManager()

    key = (0x1234, 0xAB, 0x1234, 0x5678)
    fragment_count = 1
    fragment_index = 0
    payload = b"Hello single fragment"

    (
        complete,
        reassembled,
        returned_frag_count,
        returned_frag_index,
    ) = frag_manager.handle_incoming_fragment(
        sender_nwk=key[0],
        aps_sequence=key[1],
        profile_id=key[2],
        cluster_id=key[3],
        fragment_count=fragment_count,
        fragment_index=fragment_index,
        payload=payload,
    )

    assert complete is True
    assert reassembled == payload
    assert returned_frag_count == fragment_count
    assert returned_frag_index == fragment_index
    # Make sure it's no longer tracked as partial
    assert key not in frag_manager._partial
    assert key not in frag_manager._cleanup_timers


async def test_two_fragments_in_order():
    """
    A two-fragment message should remain partial until we've received both pieces.
    """
    frag_manager = FragmentManager()

    key = (0x1111, 0x01, 0x9999, 0x2222)
    fragment_count = 2

    # First fragment
    (
        complete,
        reassembled,
        returned_frag_count,
        returned_frag_index,
    ) = frag_manager.handle_incoming_fragment(
        sender_nwk=key[0],
        aps_sequence=key[1],
        profile_id=key[2],
        cluster_id=key[3],
        fragment_count=fragment_count,
        fragment_index=0,
        payload=b"Frag0-",
    )
    assert complete is False
    assert reassembled is None
    assert key in frag_manager._partial
    assert frag_manager._partial[key].fragments_received == 1

    # Second fragment
    (
        complete,
        reassembled,
        returned_frag_count,
        returned_frag_index,
    ) = frag_manager.handle_incoming_fragment(
        sender_nwk=key[0],
        aps_sequence=key[1],
        profile_id=key[2],
        cluster_id=key[3],
        fragment_count=fragment_count,
        fragment_index=1,
        payload=b"Frag1",
    )
    assert complete is True
    assert reassembled == b"Frag0-Frag1"
    # It's removed from partials after completion
    assert key not in frag_manager._partial
    assert key not in frag_manager._cleanup_timers


async def test_out_of_order_fragments():
    """
    Receiving fragments in reverse order should still produce the correct reassembly once all arrive.
    """
    frag_manager = FragmentManager()

    key = (0x9999, 0xCD, 0x1234, 0xABCD)
    fragment_count = 2

    # Second fragment arrives first
    (
        complete,
        reassembled,
        returned_frag_count,
        returned_frag_index,
    ) = frag_manager.handle_incoming_fragment(
        sender_nwk=key[0],
        aps_sequence=key[1],
        profile_id=key[2],
        cluster_id=key[3],
        fragment_count=fragment_count,
        fragment_index=1,
        payload=b"World",
    )
    assert not complete
    assert reassembled is None

    # Then the first fragment
    (
        complete,
        reassembled,
        returned_frag_count,
        returned_frag_index,
    ) = frag_manager.handle_incoming_fragment(
        sender_nwk=key[0],
        aps_sequence=key[1],
        profile_id=key[2],
        cluster_id=key[3],
        fragment_count=fragment_count,
        fragment_index=0,
        payload=b"Hello ",
    )
    assert complete
    assert reassembled == b"Hello World"


async def test_repeated_fragments_ignored():
    """
    Ensure repeated arrivals of the same fragment index do not double-count or break the logic.
    """
    frag_manager = FragmentManager()

    key = (0xAAA, 0xBB, 0xCCC, 0xDDD)
    fragment_count = 2

    # First fragment
    (
        complete,
        reassembled,
        returned_frag_count,
        returned_frag_index,
    ) = frag_manager.handle_incoming_fragment(
        sender_nwk=key[0],
        aps_sequence=key[1],
        profile_id=key[2],
        cluster_id=key[3],
        fragment_count=fragment_count,
        fragment_index=0,
        payload=b"first",
    )
    assert not complete
    assert frag_manager._partial[key].fragments_received == 1

    # Repeat the same fragment index
    (
        complete,
        reassembled,
        returned_frag_count,
        returned_frag_index,
    ) = frag_manager.handle_incoming_fragment(
        sender_nwk=key[0],
        aps_sequence=key[1],
        profile_id=key[2],
        cluster_id=key[3],
        fragment_count=fragment_count,
        fragment_index=0,
        payload=b"first",
    )
    assert not complete
    assert frag_manager._partial[key].fragments_received == 1, "Should not increment"

    # Second fragment completes
    (
        complete,
        reassembled,
        returned_frag_count,
        returned_frag_index,
    ) = frag_manager.handle_incoming_fragment(
        sender_nwk=key[0],
        aps_sequence=key[1],
        profile_id=key[2],
        cluster_id=key[3],
        fragment_count=fragment_count,
        fragment_index=1,
        payload=b"second",
    )
    assert complete
    assert reassembled == b"firstsecond"


async def test_cleanup_partial(caplog):
    frag_manager = FragmentManager()

    key = (0x1234, 0xAB, 0x1234, 0x5678)

    frag_manager._partial[key] = MagicMock()
    frag_manager._cleanup_timers[key] = MagicMock()
    frag_manager.cleanup_partial(key)

    assert key not in frag_manager._partial
    assert key not in frag_manager._cleanup_timers
