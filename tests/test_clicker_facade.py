from app.core.clicker_facade import UnifiedClickerEngine
from app.core.state import AutoclickState


class _FakeEngine:
    def __init__(self) -> None:
        self.state = AutoclickState.STOPPED
        self.stop_calls = 0

    def stop(self) -> None:
        self.stop_calls += 1
        self.state = AutoclickState.STOPPED

    def set_config(self, cfg) -> None:
        self.cfg = cfg

    def start(self) -> None:
        self.state = AutoclickState.RUNNING

    def start_sequence(self, cfg) -> None:
        self.cfg = cfg
        self.state = AutoclickState.RUNNING

    def start_key_repeat(self, token: str, interval_ms: float, jitter_ms: float) -> None:
        self.cfg = (token, interval_ms, jitter_ms)
        self.state = AutoclickState.RUNNING

    def get_state(self) -> AutoclickState:
        return self.state

    def pause(self) -> None:
        self.state = AutoclickState.PAUSED

    def resume(self) -> None:
        self.state = AutoclickState.RUNNING


def test_active_mode_tracks_real_running_engine() -> None:
    engine = UnifiedClickerEngine()
    engine._simple = _FakeEngine()
    engine._sequence = _FakeEngine()

    engine.start_key_repeat("e", 100.0, 0.0)

    assert engine.get_active_mode() == "key_repeat"
    assert engine.get_active_state() == AutoclickState.RUNNING


def test_active_mode_resets_after_engine_stops() -> None:
    engine = UnifiedClickerEngine()
    engine._simple = _FakeEngine()
    engine._sequence = _FakeEngine()

    engine.start_sequence(object())
    engine._sequence.state = AutoclickState.STOPPED

    assert engine.get_active_mode() is None
    assert engine.get_active_state() == AutoclickState.STOPPED


def test_pause_uses_active_engine_when_mode_not_passed() -> None:
    engine = UnifiedClickerEngine()
    engine._simple = _FakeEngine()
    engine._sequence = _FakeEngine()

    engine.start_simple(object())
    engine.pause()
    assert engine._simple.state == AutoclickState.PAUSED

    engine.pause()
    assert engine._simple.state == AutoclickState.RUNNING
