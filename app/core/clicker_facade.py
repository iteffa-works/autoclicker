"""Single entry for simple / sequence / key-repeat autoclick modes."""

from __future__ import annotations

from app.core.autoclicker import AutoclickConfig, AutoclickerEngine
from app.core.event_bus import EventBus
from app.core.sequence_autoclicker import SequenceAutoclickConfig, SequenceAutoclickerEngine
from app.core.state import AutoclickState


class UnifiedClickerEngine:
    """Delegates to AutoclickerEngine or SequenceAutoclickerEngine (only one active)."""

    def __init__(self, event_bus: EventBus | None = None) -> None:
        self._simple = AutoclickerEngine(event_bus)
        self._sequence = SequenceAutoclickerEngine(event_bus)

    def apply_simple_config(self, cfg: AutoclickConfig) -> None:
        self._simple.set_config(cfg)

    def start_simple(self, cfg: AutoclickConfig | None = None) -> None:
        self._sequence.stop()
        if cfg is not None:
            self._simple.set_config(cfg)
        self._simple.start()

    def start_sequence(self, cfg: SequenceAutoclickConfig) -> None:
        self._simple.stop()
        self._sequence.start_sequence(cfg)

    def start_key_repeat(self, token: str, interval_ms: float, jitter_ms: float) -> None:
        self._simple.stop()
        self._sequence.start_key_repeat(token, interval_ms, jitter_ms)

    def pause(self, work_mode: str) -> None:
        if work_mode == "simple":
            st = self._simple.get_state()
            if st == AutoclickState.PAUSED:
                self._simple.resume()
            else:
                self._simple.pause()
        else:
            st = self._sequence.get_state()
            if st == AutoclickState.PAUSED:
                self._sequence.resume()
            else:
                self._sequence.pause()

    def stop_all(self) -> None:
        self._simple.stop()
        self._sequence.stop()

    def get_state(self, work_mode: str) -> AutoclickState:
        if work_mode in ("sequence", "key_repeat"):
            return self._sequence.get_state()
        return self._simple.get_state()

    @property
    def simple_engine(self) -> AutoclickerEngine:
        return self._simple

    @property
    def sequence_engine(self) -> SequenceAutoclickerEngine:
        return self._sequence
