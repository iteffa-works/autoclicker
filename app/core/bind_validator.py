"""Validate hotkey bindings: no duplicate chords."""

from __future__ import annotations

from app.models.bindings import BindingsConfig, HotkeyChord


def chord_key(ch: HotkeyChord) -> tuple[tuple[str, ...], str]:
    return (tuple(sorted(ch.modifiers)), ch.key.lower())


def validate_bindings(cfg: BindingsConfig) -> list[str]:
    """Return list of error messages (empty if OK)."""
    seen: dict[tuple[tuple[str, ...], str], str] = {}
    errors: list[str] = []
    for name, ch in cfg.all_assigned():
        k = chord_key(ch)
        if k in seen:
            errors.append(
                f"Конфлікт: «{name}» і «{seen[k]}» мають однакову комбінацію ({ch.display_string()})."
            )
        else:
            seen[k] = name
    return errors
