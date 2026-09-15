"""Core data model: a box holds counted items up to a fixed capacity."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Mapping


class BoxError(Exception):
    """Raised when an operation would leave a box in an invalid state."""


@dataclass
class Box:
    name: str
    capacity: int
    items: Dict[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise BoxError("box name must not be empty")
        if self.capacity < 0:
            raise BoxError(f"capacity must not be negative: {self.capacity}")
        for item, count in self.items.items():
            if count < 0:
                raise BoxError(f"{self.name}: count for {item!r} must not be negative")
        if self.used > self.capacity:
            raise BoxError(
                f"{self.name}: contents ({self.used}) exceed capacity ({self.capacity})"
            )

    @property
    def used(self) -> int:
        return sum(self.items.values())

    @property
    def remaining(self) -> int:
        return self.capacity - self.used

    @property
    def is_full(self) -> bool:
        return self.remaining == 0

    def put(self, item: str, count: int = 1) -> None:
        """Add `count` of `item`, refusing to overflow the box."""
        if count <= 0:
            raise BoxError(f"count must be positive: {count}")
        if count > self.remaining:
            raise BoxError(
                f"{self.name}: cannot fit {count} more "
                f"(only {self.remaining} of {self.capacity} left)"
            )
        self.items[item] = self.items.get(item, 0) + count

    def take(self, item: str, count: int = 1) -> None:
        """Remove `count` of `item`, refusing to take more than is present."""
        if count <= 0:
            raise BoxError(f"count must be positive: {count}")
        held = self.items.get(item, 0)
        if count > held:
            raise BoxError(f"{self.name}: only {held} of {item!r} in the box")
        if count == held:
            del self.items[item]
        else:
            self.items[item] = held - count

    def to_dict(self) -> dict:
        return {"name": self.name, "capacity": self.capacity, "items": dict(self.items)}

    @classmethod
    def from_dict(cls, data: Mapping) -> "Box":
        try:
            name = data["name"]
            capacity = data["capacity"]
        except (KeyError, TypeError) as exc:
            raise BoxError(f"malformed box record: {data!r}") from exc
        items = data.get("items") or {}
        if not isinstance(items, Mapping):
            raise BoxError(f"malformed items for box {name!r}: {items!r}")
        return cls(name=name, capacity=capacity, items=dict(items))
