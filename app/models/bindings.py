"""Hotkey chord representation for binds (serializable)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class HotkeyChord:
    """Normalized modifiers + main key token (lowercase names for letters)."""

    modifiers: tuple[str, ...]  # ctrl, alt, shift, win
    key: str  # e.g. "f1", "a", "space", "escape"

    def to_dict(self) -> dict[str, Any]:
        return {"modifiers": list(self.modifiers), "key": self.key}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> HotkeyChord:
        mods = tuple(str(x).lower() for x in data.get("modifiers", []))
        return cls(modifiers=mods, key=str(data.get("key", "")).lower())

    def display_string(self) -> str:
        order = ("ctrl", "alt", "shift", "win")
        parts = []
        for m in order:
            if m in self.modifiers:
                parts.append(m.capitalize())
        if self.key:
            parts.append(self.key.upper() if len(self.key) == 1 else self.key)
        return "+".join(parts)


def _parse_chord(data: dict[str, Any], key: str) -> HotkeyChord | None:
    raw = data.get(key)
    if not raw:
        return None
    return HotkeyChord.from_dict(raw)


def _migrate_legacy_bindings(data: dict[str, Any]) -> dict[str, Any]:
    """Merge old JSON keys into the current schema."""
    out = dict(data)
    if out.get("toggle_autoclick") is None and data.get("start_autoclick"):
        out["toggle_autoclick"] = data["start_autoclick"]
    if out.get("toggle_macro_play") is None and data.get("play_macro"):
        out["toggle_macro_play"] = data["play_macro"]
    if out.get("toggle_record_macro") is None:
        if data.get("record_macro_start"):
            out["toggle_record_macro"] = data["record_macro_start"]
        elif data.get("record_macro_stop"):
            out["toggle_record_macro"] = data["record_macro_stop"]
        elif data.get("record_macro"):
            out["toggle_record_macro"] = data["record_macro"]
    return out


@dataclass
class BindingsConfig:
    toggle_autoclick: HotkeyChord | None = None
    pause_autoclick: HotkeyChord | None = None
    toggle_macro_play: HotkeyChord | None = None
    toggle_record_macro: HotkeyChord | None = None
    toggle_tray: HotkeyChord | None = None
    emergency_stop: HotkeyChord | None = None

    def to_dict(self) -> dict[str, Any]:
        def opt(c: HotkeyChord | None) -> dict[str, Any] | None:
            return c.to_dict() if c else None

        return {
            "toggle_autoclick": opt(self.toggle_autoclick),
            "pause_autoclick": opt(self.pause_autoclick),
            "toggle_macro_play": opt(self.toggle_macro_play),
            "toggle_record_macro": opt(self.toggle_record_macro),
            "toggle_tray": opt(self.toggle_tray),
            "emergency_stop": opt(self.emergency_stop),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BindingsConfig:
        d = _migrate_legacy_bindings(dict(data))
        return cls(
            toggle_autoclick=_parse_chord(d, "toggle_autoclick"),
            pause_autoclick=_parse_chord(d, "pause_autoclick"),
            toggle_macro_play=_parse_chord(d, "toggle_macro_play"),
            toggle_record_macro=_parse_chord(d, "toggle_record_macro"),
            toggle_tray=_parse_chord(d, "toggle_tray"),
            emergency_stop=_parse_chord(d, "emergency_stop"),
        )

    def all_assigned(self) -> list[tuple[str, HotkeyChord]]:
        out: list[tuple[str, HotkeyChord]] = []
        for name, val in (
            ("toggle_autoclick", self.toggle_autoclick),
            ("pause_autoclick", self.pause_autoclick),
            ("toggle_macro_play", self.toggle_macro_play),
            ("toggle_record_macro", self.toggle_record_macro),
            ("toggle_tray", self.toggle_tray),
            ("emergency_stop", self.emergency_stop),
        ):
            if val is not None:
                out.append((name, val))
        return out
