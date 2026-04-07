"""Split JSON persistence: settings / clicker / binds / macros meta + legacy migration."""

from __future__ import annotations

from typing import Any

from app.models.bindings import BindingsConfig
from app.models.settings import AppSettings
from app.utils.json_io import read_json, write_json
from app.utils.paths import binds_config_path, clicker_config_path, macros_meta_path, settings_path

# Keys stored in clicker.json (autoclick domain)
CLICKER_KEYS: frozenset[str] = frozenset(
    {
        "last_cursor_x",
        "last_cursor_y",
        "saved_click_x",
        "saved_click_y",
        "autoclick_work_mode",
        "autoclick_sequence_steps",
        "autoclick_key_repeat_key",
        "sequence_repeat_mode",
        "sequence_step_index",
        "sequence_loop_infinite",
        "ac_humanize_enabled",
        "ac_jitter_gaussian",
        "ac_pause_chance_percent",
        "ac_pause_extra_ms",
        "ac_micro_move_px",
        "ac_pre_click_delay_ms_max",
    }
)


def split_persist_dict(full: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Split flat AppSettings.to_dict() into four file payloads."""
    inner = full.get("bindings") or {}
    bd = BindingsConfig.from_dict(inner if isinstance(inner, dict) else {}).to_dict()
    macro = {"last_selected_macro": str(full.get("macro_last_selected", ""))}
    default_full = AppSettings().to_dict()
    clicker: dict[str, Any] = {}
    for k in CLICKER_KEYS:
        if k in full:
            clicker[k] = full[k]
        else:
            clicker[k] = default_full[k]
    settings = {
        k: v
        for k, v in full.items()
        if k not in CLICKER_KEYS and k != "bindings" and k != "macro_last_selected"
    }
    return settings, clicker, bd, macro


def _write_split(s: AppSettings) -> None:
    settings_d, clicker_d, binds_d, macros_d = split_persist_dict(s.to_dict())
    write_json(settings_path(), settings_d)
    write_json(clicker_config_path(), clicker_d)
    write_json(binds_config_path(), binds_d)
    write_json(macros_meta_path(), macros_d)


def _merge_load(
    sd: dict[str, Any],
    cd: dict[str, Any],
    bd: dict[str, Any],
    md: dict[str, Any],
) -> dict[str, Any]:
    base = AppSettings().to_dict()
    for k, v in sd.items():
        if k != "bindings":
            base[k] = v
    for k, v in cd.items():
        base[k] = v
    if bd:
        base["bindings"] = BindingsConfig.from_dict(bd).to_dict()
    if md:
        base["macro_last_selected"] = str(md.get("last_selected_macro", base.get("macro_last_selected", "")))
    return base


def _migrate_legacy_monolithic(raw: dict[str, Any]) -> AppSettings:
    """One-time split from monolithic settings.json; backs up original to settings.json.bak."""
    s = AppSettings.from_dict(raw)
    backup = settings_path().with_name("settings.json.bak")
    write_json(backup, raw)
    _write_split(s)
    return s


def load_merged_settings() -> AppSettings:
    """Load AppSettings from four files, or migrate legacy monolithic settings.json."""
    settings_p = settings_path()
    clicker_p = clicker_config_path()
    binds_p = binds_config_path()
    macros_p = macros_meta_path()
    raw_settings = read_json(settings_p, {})
    legacy = (not binds_p.exists()) and (raw_settings.get("bindings") is not None)
    if legacy:
        s = _migrate_legacy_monolithic(raw_settings)
    else:
        sd = read_json(settings_p, {})
        cd = read_json(clicker_p, {}) if clicker_p.exists() else {}
        bd = read_json(binds_p, {}) if binds_p.exists() else {}
        md = read_json(macros_p, {}) if macros_p.exists() else {}
        merged = _merge_load(sd, cd, bd, md)
        s = AppSettings.from_dict(merged)
    s.bindings = s.bindings.with_defaults()
    return s


def save_merged_settings(s: AppSettings) -> None:
    _write_split(s)
