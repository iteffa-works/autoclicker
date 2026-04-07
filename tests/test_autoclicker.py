from app.core.autoclicker import AutoclickConfig, AutoclickerEngine


def test_next_delay_uses_interval_ms() -> None:
    engine = AutoclickerEngine()
    cfg = AutoclickConfig(use_interval_ms=True, interval_ms=250.0, jitter_ms=0.0)

    assert engine._next_delay_sec(cfg) == 0.25


def test_next_delay_uses_cps_when_interval_disabled() -> None:
    engine = AutoclickerEngine()
    cfg = AutoclickConfig(use_interval_ms=False, cps=4.0, jitter_ms=0.0)

    assert engine._next_delay_sec(cfg) == 0.25


def test_next_delay_never_negative() -> None:
    engine = AutoclickerEngine()
    cfg = AutoclickConfig(use_interval_ms=True, interval_ms=1.0, jitter_ms=500.0)
    engine._rng.seed(1)

    assert engine._next_delay_sec(cfg) >= 0.0
