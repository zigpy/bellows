"""Implements APS fragmentation reassembly on the EZSP Host side,
mirroring the logic from fragmentation.c in the EmberZNet stack.
"""

from __future__ import annotations

import asyncio
import logging

LOGGER = logging.getLogger(__name__)

# The maximum time (in seconds) we wait for all fragments of a given message.
# If not all fragments arrive within this time, we discard the partial data.
FRAGMENT_TIMEOUT = 10

# store partial data keyed by (sender, aps_sequence, profile_id, cluster_id)
FragmentKey = tuple[int, int, int, int]


class _FragmentEntry:
    def __init__(self, fragment_count: int):
        self.fragment_count = fragment_count
        self.fragments_received = 0
        self.fragment_data = {}

    def add_fragment(self, index: int, data: bytes) -> None:
        if index not in self.fragment_data:
            self.fragment_data[index] = data
            self.fragments_received += 1

    def is_complete(self) -> bool:
        return self.fragments_received == self.fragment_count

    def assemble(self) -> bytes:
        return b"".join(
            self.fragment_data[i] for i in sorted(self.fragment_data.keys())
        )


class FragmentManager:
    def __init__(self):
        self._partial: dict[FragmentKey, _FragmentEntry] = {}
        self._cleanup_timers: dict[FragmentKey, asyncio.TimerHandle] = {}

    def handle_incoming_fragment(
        self,
        sender_nwk: int,
        aps_sequence: int,
        profile_id: int,
        cluster_id: int,
        fragment_count: int,
        fragment_index: int,
        payload: bytes,
    ) -> tuple[bool, bytes | None, int, int]:
        """Handle a newly received fragment.

        :param sender_nwk: NWK address or the short ID of the sender.
        :param aps_sequence: The APS sequence from the incoming APS frame.
        :param profile_id: The APS frame's profileId.
        :param cluster_id: The APS frame's clusterId.
        :param fragment_count: The total number of expected message fragments.
        :param fragment_index: The index of the current fragment being processed.
        :param payload: The fragment of data for this message.
        :return: (complete, reassembled_data, fragment_count, fragment_index)
                 complete = True if we have all fragments now, else False
                 reassembled_data = the final complete payload (bytes) if complete is True
                 fragment_coutn = the total number of fragments holding the complete packet
                 fragment_index = the index of the current received fragment
        """

        key: FragmentKey = (sender_nwk, aps_sequence, profile_id, cluster_id)

        # If we have never seen this message, create a reassembly entry.
        if key not in self._partial:
            entry = _FragmentEntry(fragment_count)
            self._partial[key] = entry
        else:
            entry = self._partial[key]

        LOGGER.debug(
            "Received fragment %d/%d from %s (APS seq=%d, cluster=0x%04X)",
            fragment_index + 1,
            fragment_count,
            sender_nwk,
            aps_sequence,
            cluster_id,
        )

        entry.add_fragment(fragment_index, payload)

        loop = asyncio.get_running_loop()
        self._cleanup_timers[key] = loop.call_later(
            FRAGMENT_TIMEOUT, self.cleanup_partial, key
        )

        if entry.is_complete():
            reassembled = entry.assemble()
            del self._partial[key]
            timer = self._cleanup_timers.pop(key, None)
            if timer:
                timer.cancel()
            LOGGER.debug(
                "Message reassembly complete. Total length=%d", len(reassembled)
            )
            return (True, reassembled, fragment_count, fragment_index)
        else:
            return (False, None, fragment_count, fragment_index)

    def cleanup_partial(self, key: FragmentKey):
        # Called when FRAGMENT_TIMEOUT passes with no new fragments for that key.
        LOGGER.debug(
            "Timeout for partial reassembly of fragmented message, discarding key=%s",
            key,
        )
        self._partial.pop(key, None)
        self._cleanup_timers.pop(key, None)
