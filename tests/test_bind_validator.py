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
