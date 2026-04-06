"""Macro recording and playback."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass

from pynput import keyboard, mouse
from pynput.keyboard import Key, KeyCode
from pynput.mouse import Button, Controller as MouseController

from app.core.state import AppRunState
from app.models.bindings import BindingsConfig
from app.models.macro import MacroDefinition, MacroEvent, MacroEventType, MacroSpeedMode
from app.models.recording_profile import RecordingProfile
from app.utils.timing import sleep_until_deadline


def _key_token(vk: Key | KeyCode | None) -> str:
    if vk is None:
        return "unknown"
    if isinstance(vk, Key):
        return vk.name if vk.name else str(vk)
    try:
        if vk.char:
            return vk.char.lower()
    except AttributeError:
        pass
    return f"vk{vk.vk}" if getattr(vk, "vk", None) else str(vk)


def _button_token(b: Button) -> str:
    if b == Button.left:
        return "left"
    if b == Button.right:
        return "right"
    return "middle"


def _normalize_key_token(raw: str) -> str:
    t = raw.lower().strip()
    if t in ("esc",):
        return "escape"
    return t


def _mod_name_from_key(key: Key | KeyCode | None) -> str | None:
    if key == Key.ctrl_l or key == Key.ctrl_r:
        return "ctrl"
    if key == Key.alt_l or key == Key.alt_r:
        return "alt"
    if key == Key.shift_l or key == Key.shift_r:
        return "shift"
    if key == Key.cmd:
        return "win"
    return None


def _matches_bound_chord(mods: set[str], key_token: str, bindings: BindingsConfig) -> bool:
    """True if current mods + key equals any assigned hotkey chord."""
    kt = _normalize_key_token(key_token)
    mods_t = tuple(sorted(mods))
    for _, ch in bindings.all_assigned():
        if tuple(sorted(ch.modifiers)) == mods_t and _normalize_key_token(ch.key) == kt:
            return True
    return False


@dataclass
class MacroPlayConfig:
    repeat_count: int = 1  # -1 = infinite
    speed_mode: MacroSpeedMode = MacroSpeedMode.ORIGINAL
    speed_multiplier: float = 1.0  # used when speed_mode == CUSTOM


def _scale_delay_ms(
    delay_ms: float,
    mode: MacroSpeedMode,
    mult: float,
) -> float:
    if mode == MacroSpeedMode.ORIGINAL:
        return max(0.0, delay_ms)
    if mode == MacroSpeedMode.FAST:
        return max(0.0, delay_ms * 0.5)
    if mode == MacroSpeedMode.SLOW:
        return max(0.0, delay_ms * 2.0)
    m = max(0.05, float(mult))
    return max(0.0, delay_ms / m)


class MacroRecordSession:
    """Captures events with relative delays."""

    def __init__(
        self,
        profile: RecordingProfile,
        bindings: BindingsConfig | None,
    ) -> None:
        self._profile = profile
        self._bindings = bindings
        self._events: list[MacroEvent] = []
        self._last_t = time.perf_counter()
        self._lock = threading.Lock()
        self._mouse = MouseController()
        self._k_listener: keyboard.Listener | None = None
        self._m_listener: mouse.Listener | None = None
        self._mods: set[str] = set()

    def _append(self, ev: MacroEvent) -> None:
        now = time.perf_counter()
        with self._lock:
            delay_ms = (now - self._last_t) * 1000.0
            self._last_t = now
            ev.delay_ms = delay_ms
            self._events.append(ev)

    def _filter_keyboard_event(self, key: Key | KeyCode | None, down: bool) -> bool:
        """Return True if event should be skipped (bound hotkey)."""
        if not self._profile.filter_binding_chords or not self._bindings:
            return False
        mn = _mod_name_from_key(key)
        if mn:
            return False
        tok = _key_token(key)
        if _matches_bound_chord(self._mods, tok, self._bindings):
            return True
        return False

    def _on_press(self, key: Key | KeyCode | None) -> None:
        if not self._profile.record_keyboard:
            return
        mn = _mod_name_from_key(key)
        if mn:
            self._mods.add(mn)
            self._append(
                MacroEvent(kind=MacroEventType.KEY_DOWN, delay_ms=0.0, key=_key_token(key))
            )
            return
        if self._filter_keyboard_event(key, True):
            return
        self._append(
            MacroEvent(kind=MacroEventType.KEY_DOWN, delay_ms=0.0, key=_key_token(key))
        )

    def _on_release(self, key: Key | KeyCode | None) -> None:
        if not self._profile.record_keyboard:
            return
        mn = _mod_name_from_key(key)
        if mn:
            self._mods.discard(mn)
            self._append(
                MacroEvent(kind=MacroEventType.KEY_UP, delay_ms=0.0, key=_key_token(key))
            )
            return
        if self._filter_keyboard_event(key, False):
            return
        self._append(
            MacroEvent(kind=MacroEventType.KEY_UP, delay_ms=0.0, key=_key_token(key))
        )

    def _on_move(self, x: int, y: int) -> None:
        if not self._profile.record_mouse_move:
            return
        self._append(
            MacroEvent(
                kind=MacroEventType.MOUSE_MOVE,
                delay_ms=0.0,
                x=float(x),
                y=float(y),
            )
        )

    def _on_click(self, x: int, y: int, button: Button, pressed: bool) -> None:
        if not self._profile.record_mouse_clicks:
            return
        kind = MacroEventType.MOUSE_DOWN if pressed else MacroEventType.MOUSE_UP
        self._append(
            MacroEvent(
                kind=kind,
                delay_ms=0.0,
                key=_button_token(button),
                x=float(x),
                y=float(y),
            )
        )

    def _on_scroll(self, x: int, y: int, dx: int, dy: int) -> None:
        if not self._profile.record_scroll:
            return
        self._append(
            MacroEvent(
                kind=MacroEventType.MOUSE_SCROLL,
                delay_ms=0.0,
                x=float(x),
                y=float(y),
                scroll_dx=int(dx),
                scroll_dy=int(dy),
            )
        )

    def start(self) -> None:
        self._last_t = time.perf_counter()
        self._mods.clear()
        self._k_listener = None
        self._m_listener = None
        if self._profile.record_keyboard:
            self._k_listener = keyboard.Listener(
                on_press=self._on_press,
                on_release=self._on_release,
            )
        need_mouse = (
            self._profile.record_mouse_move
            or self._profile.record_mouse_clicks
            or self._profile.record_scroll
        )
        if need_mouse:
            self._m_listener = mouse.Listener(
                on_move=self._on_move if self._profile.record_mouse_move else None,
                on_click=self._on_click if self._profile.record_mouse_clicks else None,
                on_scroll=self._on_scroll if self._profile.record_scroll else None,
            )
        if self._k_listener:
            self._k_listener.start()
        if self._m_listener:
            self._m_listener.start()

    def stop(self) -> MacroDefinition:
        if self._k_listener:
            self._k_listener.stop()
        if self._m_listener:
            self._m_listener.stop()
        self._k_listener = None
        self._m_listener = None
        with self._lock:
            name = self._profile.name
            return MacroDefinition(name=name, events=list(self._events))


class MacroEngine:
    """Playback in a worker thread."""

    def __init__(self) -> None:
        self._mouse = MouseController()
        self._kb = keyboard.Controller()
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._state = AppRunState.IDLE

    def get_state(self) -> AppRunState:
        return self._state

    def stop(self) -> None:
        self._stop.set()
        t = self._thread
        if t and t.is_alive():
            t.join(timeout=3.0)
        self._thread = None
        self._state = AppRunState.IDLE

    def play(
        self,
        macro: MacroDefinition,
        cfg: MacroPlayConfig,
        on_finished: object | None = None,
    ) -> None:
        self.stop()
        self._stop.clear()
        self._state = AppRunState.PLAYING_MACRO

        def run() -> None:
            try:
                repeat = cfg.repeat_count
                i = 0
                while not self._stop.is_set():
                    if repeat >= 0 and i >= repeat:
                        break
                    self._play_once(macro, cfg)
                    if self._stop.is_set():
                        break
                    i += 1
            finally:
                self._state = AppRunState.IDLE
                if callable(on_finished):
                    on_finished()

        self._thread = threading.Thread(target=run, name="MacroPlay", daemon=True)
        self._thread.start()

    def _play_once(self, macro: MacroDefinition, cfg: MacroPlayConfig) -> None:
        for ev in macro.events:
            if self._stop.is_set():
                return
            d = _scale_delay_ms(ev.delay_ms, cfg.speed_mode, cfg.speed_multiplier)
            if d > 0:
                deadline = time.perf_counter() + d / 1000.0
                sleep_until_deadline(deadline)
            self._emit_event(ev)

    def _emit_event(self, ev: MacroEvent) -> None:
        if ev.kind == MacroEventType.KEY_DOWN:
            k = self._parse_key(ev.key or "")
            if k is not None:
                self._kb.press(k)
        elif ev.kind == MacroEventType.KEY_UP:
            k = self._parse_key(ev.key or "")
            if k is not None:
                self._kb.release(k)
        elif ev.kind == MacroEventType.MOUSE_MOVE:
            if ev.x is not None and ev.y is not None:
                self._mouse.position = (int(ev.x), int(ev.y))
        elif ev.kind == MacroEventType.MOUSE_DOWN:
            b = self._parse_mouse_button(ev.key or "left")
            if ev.x is not None and ev.y is not None:
                self._mouse.position = (int(ev.x), int(ev.y))
            self._mouse.press(b)
        elif ev.kind == MacroEventType.MOUSE_UP:
            b = self._parse_mouse_button(ev.key or "left")
            if ev.x is not None and ev.y is not None:
                self._mouse.position = (int(ev.x), int(ev.y))
            self._mouse.release(b)
        elif ev.kind == MacroEventType.MOUSE_SCROLL:
            dx = int(ev.scroll_dx or 0)
            dy = int(ev.scroll_dy or 0)
            self._mouse.scroll(dx, dy)

    def _parse_mouse_button(self, name: str) -> Button:
        n = name.lower()
        if n == "right":
            return Button.right
        if n == "middle":
            return Button.middle
        return Button.left

    def _parse_key(self, token: str) -> Key | KeyCode | None:
        t = token.lower().strip()
        named = {
            "space": Key.space,
            "enter": Key.enter,
            "tab": Key.tab,
            "esc": Key.esc,
            "escape": Key.esc,
            "backspace": Key.backspace,
            "shift": Key.shift,
            "shift_l": Key.shift_l,
            "shift_r": Key.shift_r,
            "ctrl": Key.ctrl,
            "ctrl_l": Key.ctrl_l,
            "ctrl_r": Key.ctrl_r,
            "alt": Key.alt,
            "alt_l": Key.alt_l,
            "alt_r": Key.alt_r,
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
        if t.startswith("f") and t[1:].isdigit():
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
