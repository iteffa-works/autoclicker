"""Autoclicker timing loop (runs in worker thread; controlled via flags)."""

from __future__ import annotations

import random
import threading
import time
from dataclasses import dataclass
from enum import Enum, auto

from pynput.mouse import Button, Controller as MouseController

from app.core.state import AutoclickState
from app.utils.timing import monotonic_now, sleep_until_deadline


class MouseButtonChoice(Enum):
    LEFT = auto()
    RIGHT = auto()
    MIDDLE = auto()


class ClickMode(Enum):
    SINGLE = auto()
    DOUBLE = auto()
    HOLD = auto()


@dataclass
class AutoclickConfig:
    button: MouseButtonChoice = MouseButtonChoice.LEFT
    mode: ClickMode = ClickMode.SINGLE
    use_interval_ms: bool = True  # False = CPS
    interval_ms: float = 100.0
    cps: float = 5.0
    jitter_ms: float = 5.0
    use_saved_position: bool = False
    saved_x: int = 0
    saved_y: int = 0


def _button_to_pynput(b: MouseButtonChoice) -> Button:
    if b == MouseButtonChoice.LEFT:
        return Button.left
    if b == MouseButtonChoice.RIGHT:
        return Button.right
    return Button.middle


class AutoclickerEngine:
    """Worker thread that performs clicks until stopped."""

    def __init__(self) -> None:
        self._mouse = MouseController()
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._pause = threading.Event()
        self._pause.set()
        self._state = AutoclickState.STOPPED
        self._lock = threading.Lock()
        self._config = AutoclickConfig()
        self._rng = random.Random()
        self._hold_button: Button | None = None

    def get_state(self) -> AutoclickState:
        with self._lock:
            return self._state

    def set_config(self, cfg: AutoclickConfig) -> None:
        with self._lock:
            self._config = cfg

    def start(self) -> None:
        with self._lock:
            if self._thread and self._thread.is_alive():
                self._pause.set()
                self._state = AutoclickState.RUNNING
                return
            self._stop.clear()
            self._pause.set()
            self._state = AutoclickState.RUNNING
            self._thread = threading.Thread(target=self._run, name="AutoclickerEngine", daemon=True)
            self._thread.start()

    def pause(self) -> None:
        with self._lock:
            self._pause.clear()
            self._state = AutoclickState.PAUSED

    def resume(self) -> None:
        with self._lock:
            self._pause.set()
            self._state = AutoclickState.RUNNING

    def stop(self) -> None:
        with self._lock:
            self._stop.set()
            self._pause.set()
            self._state = AutoclickState.STOPPED
            hb = self._hold_button
            self._hold_button = None
        if hb is not None:
            try:
                self._mouse.release(hb)
            except Exception:
                pass
        t = self._thread
        if t and t.is_alive():
            t.join(timeout=2.0)
        self._thread = None

    def _next_delay_sec(self, cfg: AutoclickConfig) -> float:
        if cfg.use_interval_ms:
            base = max(1.0, float(cfg.interval_ms))
        else:
            cps = max(0.1, float(cfg.cps))
            base = 1000.0 / cps
        j = max(0.0, float(cfg.jitter_ms))
        if j > 0:
            base += self._rng.uniform(-j, j)
        return max(0.0, base) / 1000.0

    def _run(self) -> None:
        with self._lock:
            cfg0 = self._config
        btn = _button_to_pynput(cfg0.button)
        if cfg0.mode == ClickMode.HOLD:
            try:
                if cfg0.use_saved_position:
                    self._mouse.position = (int(cfg0.saved_x), int(cfg0.saved_y))
                self._mouse.press(btn)
                with self._lock:
                    self._hold_button = btn
            except Exception:
                pass
        while not self._stop.is_set():
            self._pause.wait()
            if self._stop.is_set():
                break
            with self._lock:
                cfg = self._config
            if cfg.mode == ClickMode.HOLD:
                delay = self._next_delay_sec(cfg)
                deadline = monotonic_now() + delay
                sleep_until_deadline(deadline)
                continue
            delay = self._next_delay_sec(cfg)
            deadline = monotonic_now() + delay
            sleep_until_deadline(deadline)
            if self._stop.is_set():
                break
            self._pause.wait()
            if self._stop.is_set():
                break
            try:
                self._perform_click(cfg, btn)
            except Exception:
                time.sleep(0.01)
        with self._lock:
            hb = self._hold_button
            self._hold_button = None
        if hb is not None:
            try:
                self._mouse.release(hb)
            except Exception:
                pass

    def _perform_click(self, cfg: AutoclickConfig, btn: Button) -> None:
        if cfg.use_saved_position:
            self._mouse.position = (int(cfg.saved_x), int(cfg.saved_y))
        if cfg.mode == ClickMode.SINGLE:
            self._mouse.click(btn, 1)
        elif cfg.mode == ClickMode.DOUBLE:
            self._mouse.click(btn, 2)
