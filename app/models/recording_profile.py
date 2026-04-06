"""Recording profile: what to capture during macro recording."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass
class RecordingProfile:
    """Named preset for macro recording."""

    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = "Стандарт"
    record_mouse_move: bool = False
    record_keyboard: bool = True
    record_mouse_clicks: bool = True
    record_scroll: bool = True
    filter_binding_chords: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "record_mouse_move": self.record_mouse_move,
            "record_keyboard": self.record_keyboard,
            "record_mouse_clicks": self.record_mouse_clicks,
            "record_scroll": self.record_scroll,
            "filter_binding_chords": self.filter_binding_chords,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RecordingProfile:
        return cls(
            id=str(data.get("id") or uuid.uuid4().hex[:8]),
            name=str(data.get("name", "Профіль")),
            record_mouse_move=bool(data.get("record_mouse_move", False)),
            record_keyboard=bool(data.get("record_keyboard", True)),
            record_mouse_clicks=bool(data.get("record_mouse_clicks", True)),
            record_scroll=bool(data.get("record_scroll", True)),
            filter_binding_chords=bool(data.get("filter_binding_chords", True)),
        )


def default_profiles() -> list[RecordingProfile]:
    return [
        RecordingProfile(
            id="default",
            name="Повний (клавіатура + миша)",
            record_mouse_move=False,
            record_keyboard=True,
            record_mouse_clicks=True,
            record_scroll=True,
            filter_binding_chords=True,
        ),
        RecordingProfile(
            id="keys_only",
            name="Лише клавіатура",
            record_mouse_move=False,
            record_keyboard=True,
            record_mouse_clicks=False,
            record_scroll=False,
            filter_binding_chords=True,
        ),
    ]
