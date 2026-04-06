"""Autoclicker: sequence of keyboard/mouse steps or single-key repeat."""

from __future__ import annotations

import random
import threading
import time
from dataclasses import dataclass

from pynput.keyboard import Key, KeyCode
from pynput.keyboard import Controller as KeyboardController
from pynput.mouse import Button, Controller as MouseController

from app.core.state import AutoclickState
from app.models.autoclick_sequence import AutoclickSequenceStep, AutoclickSequenceStepType, SequenceRepeatMode
from app.utils.timing import monotonic_now, sleep_until_deadline


def _parse_key(token: str) -> Key | KeyCode | None:
    t = token.lower().strip()
    named = {
        "space": Key.space,
        "enter": Key.enter,
        "tab": Key.tab,
        "esc": Key.esc,
        "escape": Key.esc,
        "backspace": Key.backspace,
        "shift": Key.shift,
        "ctrl": Key.ctrl,
        "alt": Key.alt,
        "up": Key.up,
        "down": Key.down,
        "left": Key.left,
        "right": Key.right,
        "home": Key.home,
        "end": Key.end,
        "page_up": Key.page_up,
        "page_down": Key.page_down,
        "insert": Key.insert,
        "delete": Key.delete,
    }
    if t in named:
        return named[t]
    if t.startswith("f") and len(t) > 1 and t[1:].isdigit():
        n = int(t[1:])
        fs = {
            1: Key.f1,
            2: Key.f2,
            3: Key.f3,
            4: Key.f4,
            5: Key.f5,
            6: Key.f6,
            7: Key.f7,
            8: Key.f8,
            9: Key.f9,
            10: Key.f10,
            11: Key.f11,
            12: Key.f12,
        }
        return fs.get(n)
    if len(t) == 1:
        return KeyCode.from_char(t)
    if t.startswith("vk") and t[2:].isdigit():
        return KeyCode.from_vk(int(t[2:]))
    return None


def _mouse_btn(name: str) -> Button:
    n = name.lower()
    if n == "right":
        return Button.right
    if n == "middle":
        return Button.middle
    return Button.left


@dataclass
class SequenceAutoclickConfig:
    steps: list[AutoclickSequenceStep]
    repeat_mode: SequenceRepeatMode
    step_index: int
    loop_infinite: bool
    interval_ms: float
    jitter_ms: float
    key_repeat_token: str


class SequenceAutoclickerEngine:
    def __init__(self) -> None:
        self._mouse = MouseController()
        self._kb = KeyboardController()
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._pause = threading.Event()
        self._pause.set()
        self._state = AutoclickState.STOPPED
        self._lock = threading.Lock()
        self._config = SequenceAutoclickConfig(
            steps=[],
            repeat_mode=SequenceRepeatMode.FULL,
            step_index=0,
            loop_infinite=True,
            interval_ms=100.0,
            jitter_ms=0.0,
            key_repeat_token="e",
        )
        self._rng = random.Random()

    def get_state(self) -> AutoclickState:
        with self._lock:
            return self._state

    def set_config(self, cfg: SequenceAutoclickConfig) -> None:
        with self._lock:
            self._config = cfg

    def start_key_repeat(self, token: str, interval_ms: float, jitter_ms: float) -> None:
        cfg = SequenceAutoclickConfig(
            steps=[],
            repeat_mode=SequenceRepeatMode.FULL,
            step_index=0,
            loop_infinite=True,
            interval_ms=float(interval_ms),
            jitter_ms=float(jitter_ms),
            key_repeat_token=token,
        )
        self.set_config(cfg)
        self._start_inner(mode="key_repeat")

    def start_sequence(self, cfg: SequenceAutoclickConfig) -> None:
        self.set_config(cfg)
        self._start_inner(mode="sequence")

    def _start_inner(self, mode: str) -> None:
        with self._lock:
            if self._thread and self._thread.is_alive():
                self._pause.set()
                self._state = AutoclickState.RUNNING
                return
            self._stop.clear()
            self._pause.set()
            self._state = AutoclickState.RUNNING
            self._thread = threading.Thread(
                target=self._run_key_repeat if mode == "key_repeat" else self._run_sequence,
                name="SequenceAutoclicker",
                daemon=True,
            )
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
        t = self._thread
        if t and t.is_alive():
            t.join(timeout=2.0)
        self._thread = None

    def _between_delay(self, cfg: SequenceAutoclickConfig) -> None:
        base = max(0.0, float(cfg.interval_ms))
        j = max(0.0, float(cfg.jitter_ms))
        if j > 0:
            base += self._rng.uniform(-j, j)
        sec = max(0.0, base) / 1000.0
        if sec <= 0:
            return
        deadline = monotonic_now() + sec
        sleep_until_deadline(deadline)

    def _run_key_repeat(self) -> None:
        try:
            while not self._stop.is_set():
                self._pause.wait()
                if self._stop.is_set():
                    break
                with self._lock:
                    cfg = self._config
                token = cfg.key_repeat_token.strip()
                k = _parse_key(token) if token else None
                if k is not None:
                    try:
                        self._kb.press(k)
                        self._kb.release(k)
                    except Exception:
                        time.sleep(0.01)
                self._between_delay(cfg)
        finally:
            with self._lock:
                self._state = AutoclickState.STOPPED

    def _run_sequence(self) -> None:
        try:
            while not self._stop.is_set():
                with self._lock:
                    cfg = self._config
                steps = list(cfg.steps)
                if not steps:
                    break
                if cfg.repeat_mode == SequenceRepeatMode.SINGLE_STEP:
                    idx = max(0, min(len(steps) - 1, int(cfg.step_index)))
                    chunk = [steps[idx]]
                else:
                    chunk = steps
                for st in chunk:
                    self._pause.wait()
                    if self._stop.is_set():
                        break
                    self._exec_step(st)
                    self._between_delay(cfg)
                if self._stop.is_set():
                    break
                if not cfg.loop_infinite:
                    break
        finally:
            with self._lock:
                self._state = AutoclickState.STOPPED

    def _exec_step(self, st: AutoclickSequenceStep) -> None:
        if st.type == AutoclickSequenceStepType.DELAY:
            ms = max(0.0, float(st.delay_ms))
            if ms > 0:
                deadline = monotonic_now() + ms / 1000.0
                sleep_until_deadline(deadline)
        elif st.type == AutoclickSequenceStepType.KEY_DOWN:
            k = _parse_key(st.key or "")
            if k is not None:
                try:
                    self._kb.press(k)
                except Exception:
                    pass
        elif st.type == AutoclickSequenceStepType.KEY_UP:
            k = _parse_key(st.key or "")
            if k is not None:
                try:
                    self._kb.release(k)
                except Exception:
                    pass
        elif st.type == AutoclickSequenceStepType.MOUSE_CLICK:
            b = _mouse_btn(st.button or "left")
            try:
                self._mouse.click(b, 1)
            except Exception:
                pass
