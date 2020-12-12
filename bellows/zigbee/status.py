"""Classes to implement status of the application controller."""

from dataclasses import dataclass, field
import functools
from typing import Iterable, List, Optional

import zigpy.types as t
import zigpy.zdo.types as zdo_t


@dataclass
class NodeInfo:
    """Controller Application network Node information."""

    nwk: t.NWK = field(default_factory=t.NWK)
    ieee: t.EUI64 = field(default_factory=t.EUI64)
    logical_type: zdo_t.LogicalType = field(default_factory=zdo_t.LogicalType)


@dataclass
class NetworkInformation:
    """Network information."""

    extended_pan_id: Optional[t.ExtendedPanId] = None
    pan_id: Optional[t.PanId] = None
    nwk_update_id: Optional[t.uint8_t] = None
    nwk_manager_id: Optional[t.NWK] = None
    channel: t.Optional[t.uint8_t] = None


@dataclass
class Counter:
    """Ever increasing Counter representation."""

    name: str
    raw_value: int = field(default=0)
    clear_count: int = field(init=False, default=0)
    _last_reset: int = field(init=False, default=0)

    @property
    def value(self) -> int:
        """Current value of the counter."""

        return self._last_reset + self.raw_value

    def __str__(self) -> str:
        """String representation."""
        return f"{self.name} = {self.value}"

    def update(self, new_value: int) -> None:
        """Update counter value."""

        diff = new_value - self.raw_value
        if diff < 0:  # Roll over or reset
            self.clear_and_update(new_value)
            return

        self.raw_value = new_value

    def clear_and_update(self, value: int) -> None:
        """Clear (rollover event) and optionally update."""

        self._last_reset = self.value
        self.raw_value = value
        self.clear_count += 1

    clear = functools.partialmethod(clear_and_update, 0)


class Counters:
    """Named collection of counters."""

    def __init__(self, names: Optional[Iterable[str]]) -> None:
        """Initialize instance."""

        self._counters = {name: Counter for name in names}

    @property
    def list(self) -> List[Counter]:
        """Return list of counters."""

        return [counter for counter in self._counters.values()]

    def clear(self) -> None:
        """Clear and rollover counters."""

        for counter in self._counters.values():
            counter.clear()


@dataclass
class State:
    node_information: field(default_factory=NodeInfo)
    network_information: NetworkInformation
    counters: Counters
