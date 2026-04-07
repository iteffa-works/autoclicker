"""Application settings and profile."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from app.models.autoclick_sequence import SequenceRepeatMode
from app.models.bindings import BindingsConfig
from app.models.recording_profile import RecordingProfile, default_profiles


class ThemeMode(str, Enum):
    LIGHT = "light"
    DARK = "dark"


class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class HotkeyBackend(str, Enum):
    AUTO = "auto"
    WIN32 = "win32"
    PYNPUT = "pynput"


@dataclass
class AppSettings:
    theme: ThemeMode = ThemeMode.DARK
    ui_language: str = "uk"  # en | uk | ru (see app/i18n)
    always_on_top: bool = False
    sound_on_start_stop: bool = False
    minimize_to_tray: bool = True
    close_to_tray: bool = False
    hotkey_backend: HotkeyBackend = HotkeyBackend.AUTO
    overlay_opacity: float = 0.92
    autosave_macros: bool = True
    autosave_interval_sec: int = 30
    macros_folder: str = ""  # empty = default data/macros
    log_level: LogLevel = LogLevel.INFO
    log_to_file: bool = False
    jitter_percent: float = 10.0  # 0..50
    timing_precision_ms: float = 1.0
    last_cursor_x: int = 0
    last_cursor_y: int = 0
    saved_click_x: int = 0
    saved_click_y: int = 0
    profile_name: str = "default"
    recording_profiles: list[RecordingProfile] = field(default_factory=lambda: list(default_profiles()))
    active_recording_profile_id: str = "default"
    bindings: BindingsConfig = field(default_factory=BindingsConfig)
    infinite_loop_confirmed: bool = False
    autoclick_work_mode: str = "simple"
    autoclick_sequence_steps: list[dict[str, Any]] = field(default_factory=list)
    autoclick_key_repeat_key: str = "e"
    sequence_repeat_mode: str = SequenceRepeatMode.FULL.value
    sequence_step_index: int = 0
    sequence_loop_infinite: bool = True
    ac_humanize_enabled: bool = False
    ac_jitter_gaussian: bool = False
    ac_pause_chance_percent: float = 0.0
    ac_pause_extra_ms: float = 220.0
    ac_micro_move_px: int = 0
    ac_pre_click_delay_ms_max: float = 0.0
    macro_last_selected: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "theme": self.theme.value,
            "ui_language": self.ui_language,
            "always_on_top": self.always_on_top,
            "sound_on_start_stop": self.sound_on_start_stop,
            "minimize_to_tray": self.minimize_to_tray,
            "close_to_tray": self.close_to_tray,
            "hotkey_backend": self.hotkey_backend.value,
            "overlay_opacity": self.overlay_opacity,
            "autosave_macros": self.autosave_macros,
            "autosave_interval_sec": self.autosave_interval_sec,
            "macros_folder": self.macros_folder,
            "log_level": self.log_level.value,
            "log_to_file": self.log_to_file,
            "jitter_percent": self.jitter_percent,
            "timing_precision_ms": self.timing_precision_ms,
            "last_cursor_x": self.last_cursor_x,
            "last_cursor_y": self.last_cursor_y,
            "saved_click_x": self.saved_click_x,
            "saved_click_y": self.saved_click_y,
            "profile_name": self.profile_name,
            "recording_profiles": [p.to_dict() for p in self.recording_profiles],
            "active_recording_profile_id": self.active_recording_profile_id,
            "bindings": self.bindings.to_dict(),
            "infinite_loop_confirmed": self.infinite_loop_confirmed,
            "autoclick_work_mode": self.autoclick_work_mode,
            "autoclick_sequence_steps": list(self.autoclick_sequence_steps),
            "autoclick_key_repeat_key": self.autoclick_key_repeat_key,
            "sequence_repeat_mode": self.sequence_repeat_mode,
            "sequence_step_index": self.sequence_step_index,
            "sequence_loop_infinite": self.sequence_loop_infinite,
            "ac_humanize_enabled": self.ac_humanize_enabled,
            "ac_jitter_gaussian": self.ac_jitter_gaussian,
            "ac_pause_chance_percent": self.ac_pause_chance_percent,
            "ac_pause_extra_ms": self.ac_pause_extra_ms,
            "ac_micro_move_px": self.ac_micro_move_px,
            "ac_pre_click_delay_ms_max": self.ac_pre_click_delay_ms_max,
            "macro_last_selected": self.macro_last_selected,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AppSettings:
        b = BindingsConfig.from_dict(data.get("bindings") or {})
        try:
            theme = ThemeMode(data.get("theme", ThemeMode.DARK.value))
        except ValueError:
            theme = ThemeMode.DARK
        try:
            log_level = LogLevel(data.get("log_level", LogLevel.INFO.value))
        except ValueError:
            log_level = LogLevel.INFO
        hb_raw = data.get("hotkey_backend", HotkeyBackend.AUTO.value)
        try:
            hotkey_backend = HotkeyBackend(hb_raw)
        except ValueError:
            hotkey_backend = HotkeyBackend.AUTO
        rp_raw = data.get("recording_profiles")
        if rp_raw:
            recording_profiles = [RecordingProfile.from_dict(x) for x in rp_raw]
        else:
            recording_profiles = list(default_profiles())
        return cls(
            theme=theme,
            ui_language=str(data.get("ui_language", "uk")),
            always_on_top=bool(data.get("always_on_top", False)),
            sound_on_start_stop=bool(data.get("sound_on_start_stop", False)),
            minimize_to_tray=bool(data.get("minimize_to_tray", True)),
            close_to_tray=bool(data.get("close_to_tray", False)),
            hotkey_backend=hotkey_backend,
            overlay_opacity=float(data.get("overlay_opacity", 0.92)),
            autosave_macros=bool(data.get("autosave_macros", True)),
            autosave_interval_sec=int(data.get("autosave_interval_sec", 30)),
            macros_folder=str(data.get("macros_folder", "")),
            log_level=log_level,
            log_to_file=bool(data.get("log_to_file", False)),
            jitter_percent=float(data.get("jitter_percent", 10.0)),
            timing_precision_ms=float(data.get("timing_precision_ms", 1.0)),
            last_cursor_x=int(data.get("last_cursor_x", 0)),
            last_cursor_y=int(data.get("last_cursor_y", 0)),
            saved_click_x=int(data.get("saved_click_x", 0)),
            saved_click_y=int(data.get("saved_click_y", 0)),
            profile_name=str(data.get("profile_name", "default")),
            recording_profiles=recording_profiles,
            active_recording_profile_id=str(data.get("active_recording_profile_id", "default")),
            bindings=b,
            infinite_loop_confirmed=bool(data.get("infinite_loop_confirmed", False)),
            autoclick_work_mode=str(data.get("autoclick_work_mode", "simple")),
            autoclick_sequence_steps=list(data.get("autoclick_sequence_steps") or []),
            autoclick_key_repeat_key=str(data.get("autoclick_key_repeat_key", "e")),
            sequence_repeat_mode=str(data.get("sequence_repeat_mode", SequenceRepeatMode.FULL.value)),
            sequence_step_index=int(data.get("sequence_step_index", 0)),
            sequence_loop_infinite=bool(data.get("sequence_loop_infinite", True)),
            ac_humanize_enabled=bool(data.get("ac_humanize_enabled", False)),
            ac_jitter_gaussian=bool(data.get("ac_jitter_gaussian", False)),
            ac_pause_chance_percent=float(data.get("ac_pause_chance_percent", 0.0)),
            ac_pause_extra_ms=float(data.get("ac_pause_extra_ms", 220.0)),
            ac_micro_move_px=int(data.get("ac_micro_move_px", 0)),
            ac_pre_click_delay_ms_max=float(data.get("ac_pre_click_delay_ms_max", 0.0)),
            macro_last_selected=str(data.get("macro_last_selected", "")),
        )
