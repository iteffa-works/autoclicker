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
