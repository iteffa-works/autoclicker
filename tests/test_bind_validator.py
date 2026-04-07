from app.core.bind_validator import validate_bindings
from app.models.bindings import BindingsConfig, HotkeyChord


def test_bindings_conflict_detected() -> None:
    ch = HotkeyChord(("ctrl",), "a")
    cfg = BindingsConfig(toggle_autoclick=ch, pause_autoclick=ch)
    errs = validate_bindings(cfg)
    assert len(errs) == 1


def test_bindings_ok() -> None:
    cfg = BindingsConfig(
        toggle_autoclick=HotkeyChord(("ctrl",), "a"),
        pause_autoclick=HotkeyChord(("ctrl",), "b"),
    )
    assert validate_bindings(cfg) == []


def test_bindings_ignore_none_values() -> None:
    cfg = BindingsConfig(toggle_autoclick=None, pause_autoclick=HotkeyChord(("ctrl",), "b"))

    assert validate_bindings(cfg) == []


def test_bindings_detect_duplicates_with_unsorted_modifiers() -> None:
    cfg = BindingsConfig(
        toggle_autoclick=HotkeyChord(("shift", "ctrl"), "a"),
        pause_autoclick=HotkeyChord(("ctrl", "shift"), "a"),
    )

    errs = validate_bindings(cfg)
    assert len(errs) == 1
