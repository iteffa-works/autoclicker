"""Global hotkeys via pynput (dedicated thread)."""

from __future__ import annotations

import threading
import time
from collections.abc import Callable
from typing import Any

from pynput import keyboard

from app.models.bindings import BindingsConfig, HotkeyChord


def chord_to_pynput_string(ch: HotkeyChord) -> str:
    """Build pynput GlobalHotKeys combo string."""
    order = ("ctrl", "alt", "shift", "win")
    parts: list[str] = []
    for m in order:
        if m in ch.modifiers:
            if m == "win":
                parts.append("<cmd>")
            else:
                parts.append(f"<{m}>")
    key = ch.key.lower().strip()
    if len(key) == 1 and (key.isalpha() or key.isdigit()):
        parts.append(key)
    elif key in {f"f{i}" for i in range(1, 13)}:
        parts.append(key)
    elif key in ("esc", "escape"):
        parts.append("<esc>")
    elif key in (
        "space",
        "tab",
        "enter",
        "backspace",
        "insert",
        "delete",
        "home",
        "end",
        "page_up",
        "page_down",
        "up",
        "down",
        "left",
        "right",
    ):
        parts.append(f"<{key}>")
    elif key.startswith("numpad"):
        parts.append(f"<{key}>")
    else:
        parts.append(key)
    return "+".join(parts)


class HotkeyService:
    """Registers global hotkeys; call stop() on application exit."""

    def __init__(self) -> None:
        self._listener: keyboard.GlobalHotKeys | None = None
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()

    def start(
        self,
        cfg: BindingsConfig,
        callbacks: dict[str, Callable[[], None]],
    ) -> None:
        self.stop()
        mapping: dict[str, Callable[[], None]] = {}
        for name, ch in cfg.all_assigned():
            cb = callbacks.get(name)
            if cb is None:
                continue
            try:
                s = chord_to_pynput_string(ch)
                mapping[s] = cb
            except Exception:
                continue
        if not mapping:
            return

        def run() -> None:
            try:
                self._listener = keyboard.GlobalHotKeys(mapping)
                self._listener.run()
            except Exception:
                self._listener = None

        self._thread = threading.Thread(target=run, name="GlobalHotKeys", daemon=True)
        self._thread.start()
        time.sleep(0.05)

    def stop(self) -> None:
        with self._lock:
            lst = self._listener
            self._listener = None
        if lst is not None:
            try:
                lst.stop()
            except Exception:
                pass
        t = self._thread
        self._thread = None
        if t and t.is_alive():
            t.join(timeout=2.0)


class ChordCaptureSession:
    """One-shot capture of modifiers + key for UI binding."""

    def __init__(self, on_captured: Callable[[HotkeyChord], None]) -> None:
        self._on_captured = on_captured
        self._mods: set[str] = set()
        self._listener: keyboard.Listener | None = None

    def _name_mod(self, key: keyboard.Key | keyboard.KeyCode | None) -> str | None:
        if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
            return "ctrl"
        if key == keyboard.Key.alt_l or key == keyboard.Key.alt_r:
            return "alt"
        if key == keyboard.Key.shift_l or key == keyboard.Key.shift_r:
            return "shift"
        if key == keyboard.Key.cmd:
            return "win"
        return None

    def _token_key(self, key: keyboard.Key | keyboard.KeyCode | None) -> str | None:
        if isinstance(key, keyboard.Key):
            if key == keyboard.Key.space:
                return "space"
            if hasattr(key, "name") and key.name:
                return key.name.lower()
            return None
        try:
            if key and getattr(key, "char", None):
                return str(key.char).lower()
        except Exception:
            pass
        if key and getattr(key, "vk", None):
            return f"vk{key.vk}"
        return None

    def _on_press(self, key: keyboard.Key | keyboard.KeyCode | None) -> None:
        mod = self._name_mod(key)
        if mod:
            self._mods.add(mod)
            return
        tok = self._token_key(key)
        if not tok:
            return
        mods = tuple(sorted(self._mods))
        chord = HotkeyChord(modifiers=mods, key=tok)
        self.stop()
        self._on_captured(chord)

    def _on_release(self, key: keyboard.Key | keyboard.KeyCode | None) -> None:
        mod = self._name_mod(key)
        if mod and mod in self._mods:
            self._mods.discard(mod)

    def start(self) -> None:
        self._listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release,
        )
        self._listener.start()

    def stop(self) -> None:
        if self._listener:
            try:
                self._listener.stop()
            except Exception:
                pass
        self._listener = None
