"""Persistence: boxes live in a single JSON file."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, Iterator, List

from .model import Box, BoxError

ENV_VAR = "BOX_REMAINING_DATA"
DEFAULT_PATH = Path.home() / ".box-remaining" / "boxes.json"


def default_data_path() -> Path:
    override = os.environ.get(ENV_VAR)
    return Path(override).expanduser() if override else DEFAULT_PATH


class BoxStore:
    """A collection of named boxes backed by a JSON file."""

    def __init__(self, path: Path, boxes: Dict[str, Box]):
        self.path = path
        self._boxes = boxes

    # -- loading / saving -------------------------------------------------

    @classmethod
    def load(cls, path: Path | None = None) -> "BoxStore":
        path = Path(path) if path is not None else default_data_path()
        if not path.exists():
            return cls(path, {})
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise BoxError(f"{path} is not valid JSON: {exc}") from exc
        records = raw.get("boxes", []) if isinstance(raw, dict) else raw
        if not isinstance(records, list):
            raise BoxError(f"{path}: expected a list of boxes, got {type(records).__name__}")
        boxes: Dict[str, Box] = {}
        for record in records:
            box = Box.from_dict(record)
            if box.name in boxes:
                raise BoxError(f"{path}: duplicate box {box.name!r}")
            boxes[box.name] = box
        return cls(path, boxes)

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"boxes": [box.to_dict() for box in self]}
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        tmp.replace(self.path)

    # -- collection access ------------------------------------------------

    def __iter__(self) -> Iterator[Box]:
        return iter(sorted(self._boxes.values(), key=lambda b: b.name))

    def __len__(self) -> int:
        return len(self._boxes)

    def __contains__(self, name: object) -> bool:
        return name in self._boxes

    def names(self) -> List[str]:
        return [box.name for box in self]

    def get(self, name: str) -> Box:
        try:
            return self._boxes[name]
        except KeyError:
            known = ", ".join(self.names()) or "none yet"
            raise BoxError(f"no box named {name!r} (known boxes: {known})") from None

    def add(self, name: str, capacity: int) -> Box:
        if name in self._boxes:
            raise BoxError(f"box {name!r} already exists")
        box = Box(name=name, capacity=capacity)
        self._boxes[name] = box
        return box

    def remove(self, name: str) -> Box:
        box = self.get(name)
        del self._boxes[name]
        return box

    # -- aggregates -------------------------------------------------------

    @property
    def total_capacity(self) -> int:
        return sum(box.capacity for box in self._boxes.values())

    @property
    def total_used(self) -> int:
        return sum(box.used for box in self._boxes.values())

    @property
    def total_remaining(self) -> int:
        return self.total_capacity - self.total_used
