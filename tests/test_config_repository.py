from app.models.settings import AppSettings
from app.services.config_repository import CLICKER_KEYS, split_persist_dict


def test_split_roundtrip_preserves_bindings_and_clicker() -> None:
    s = AppSettings()
    s.saved_click_x = 42
    s.bindings.emergency_stop = None
    full = s.to_dict()
    settings_d, clicker_d, binds_d, macro_d = split_persist_dict(full)
    assert "bindings" not in settings_d
    assert "saved_click_x" not in settings_d
    assert clicker_d.get("saved_click_x") == 42
    assert "toggle_autoclick" in binds_d
    assert "last_selected_macro" in macro_d


def test_clicker_keys_cover_autoclick_domain() -> None:
    assert "autoclick_work_mode" in CLICKER_KEYS
    assert "theme" not in CLICKER_KEYS


def test_app_settings_from_dict_falls_back_for_invalid_enums() -> None:
    settings = AppSettings.from_dict({"theme": "broken", "log_level": "broken"})

    assert settings.theme.value == "dark"
    assert settings.log_level.value == "INFO"


def test_bindings_with_defaults_fills_missing_hotkeys() -> None:
    settings = AppSettings.from_dict({"bindings": {"emergency_stop": None}})
    settings.bindings = settings.bindings.with_defaults()

    assert settings.bindings.toggle_autoclick is not None
    assert settings.bindings.toggle_autoclick.key == "f6"
    assert settings.bindings.pause_autoclick is not None
    assert settings.bindings.pause_autoclick.key == "f7"
    assert settings.bindings.toggle_macro_play is not None
    assert settings.bindings.toggle_macro_play.key == "f8"
    assert settings.bindings.toggle_record_macro is not None
    assert settings.bindings.toggle_record_macro.key == "f9"
    assert settings.bindings.toggle_tray is not None
    assert settings.bindings.toggle_tray.key == "f10"
    assert settings.bindings.emergency_stop is not None
    assert settings.bindings.emergency_stop.key == "escape"
