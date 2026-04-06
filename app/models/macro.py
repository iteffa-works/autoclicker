"""Macro events and macro file model."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class MacroEventType(str, Enum):
    KEY_DOWN = "key_down"
    KEY_UP = "key_up"
    MOUSE_DOWN = "mouse_down"
    MOUSE_UP = "mouse_up"
    MOUSE_MOVE = "mouse_move"
    MOUSE_SCROLL = "mouse_scroll"


class MacroSpeedMode(str, Enum):
    ORIGINAL = "original"
    FAST = "fast"
    SLOW = "slow"
    CUSTOM = "custom"


@dataclass
class MacroEvent:
    """Single recorded or edited step."""

    kind: MacroEventType
    delay_ms: float  # delay before this event from previous
    key: str | None = None  # keyboard token or mouse button name
    x: float | None = None
    y: float | None = None
    scroll_dx: int | None = None
    scroll_dy: int | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "kind": self.kind.value,
            "delay_ms": self.delay_ms,
        }
        if self.key is not None:
            d["key"] = self.key
        if self.x is not None:
            d["x"] = self.x
        if self.y is not None:
            d["y"] = self.y
        if self.scroll_dx is not None:
            d["scroll_dx"] = self.scroll_dx
        if self.scroll_dy is not None:
            d["scroll_dy"] = self.scroll_dy
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MacroEvent:
        return cls(
            kind=MacroEventType(data["kind"]),
            delay_ms=float(data.get("delay_ms", 0)),
            key=data.get("key"),
            x=data.get("x"),
            y=data.get("y"),
            scroll_dx=data.get("scroll_dx"),
            scroll_dy=data.get("scroll_dy"),
        )


@dataclass
class MacroDefinition:
    name: str
    events: list[MacroEvent] = field(default_factory=list)
    schema_version: int = 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "name": self.name,
            "events": [e.to_dict() for e in self.events],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MacroDefinition:
        evs = [MacroEvent.from_dict(x) for x in data.get("events", [])]
        return cls(
            name=str(data.get("name", "macro")),
            events=evs,
            schema_version=int(data.get("schema_version", 1)),
        )
