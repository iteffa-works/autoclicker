"""Load/save application settings."""

from __future__ import annotations

from app.models.bindings import HotkeyChord
from app.models.settings import AppSettings
from app.utils.json_io import read_json, write_json
from app.utils.paths import settings_path


def load_settings() -> AppSettings:
    path = settings_path()
    raw = read_json(path, {})
    if not raw:
        s = AppSettings()
        s.bindings.emergency_stop = HotkeyChord((), "escape")
        return s
    s = AppSettings.from_dict(raw)
    if s.bindings.emergency_stop is None:
        s.bindings.emergency_stop = HotkeyChord((), "escape")
    return s


def save_settings(settings: AppSettings) -> None:
    write_json(settings_path(), settings.to_dict())
