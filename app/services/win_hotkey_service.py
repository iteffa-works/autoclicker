"""Windows RegisterHotKey / WM_HOTKEY for reliable global hotkeys."""

from __future__ import annotations

import ctypes
import logging
from collections.abc import Callable
from ctypes import wintypes

from app.models.bindings import BindingsConfig, HotkeyChord

user32 = ctypes.WinDLL("user32", use_last_error=True)

user32.RegisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_uint, ctypes.c_uint]
user32.RegisterHotKey.restype = wintypes.BOOL
user32.UnregisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int]
user32.UnregisterHotKey.restype = wintypes.BOOL

MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008

WM_HOTKEY = 0x0312

# Virtual key codes (subset); F1=0x70 .. F12=0x7B
VK_ESCAPE = 0x1B
VK_SPACE = 0x20
VK_TAB = 0x09
VK_RETURN = 0x0D
VK_BACK = 0x08
VK_INSERT = 0x2D
VK_DELETE = 0x2E
VK_HOME = 0x24
VK_END = 0x23
VK_PRIOR = 0x21
VK_NEXT = 0x22
VK_LEFT = 0x25
VK_UP = 0x26
VK_RIGHT = 0x27
VK_DOWN = 0x28
VK_NUMPAD0 = 0x60


def _modifiers_to_fs(ch: HotkeyChord) -> int:
    fs = 0
    for m in ch.modifiers:
        if m == "ctrl":
            fs |= MOD_CONTROL
        elif m == "alt":
            fs |= MOD_ALT
        elif m == "shift":
            fs |= MOD_SHIFT
        elif m == "win":
            fs |= MOD_WIN
    return fs


def _key_to_vk(ch: HotkeyChord) -> int | None:
    k = ch.key.lower().strip()
    if len(k) == 1 and k.isalpha():
        return ord(k.upper())
    if len(k) == 1 and k.isdigit():
        return ord(k)
    if k in {f"f{i}" for i in range(1, 13)}:
        n = int(k[1:])
        return 0x6F + n
    if k in ("esc", "escape"):
        return VK_ESCAPE
    if k == "space":
        return VK_SPACE
    if k == "tab":
        return VK_TAB
    if k in ("enter", "return"):
        return VK_RETURN
    if k == "backspace":
        return VK_BACK
    if k == "insert":
        return VK_INSERT
    if k == "delete":
        return VK_DELETE
    if k == "home":
        return VK_HOME
    if k == "end":
        return VK_END
    if k == "page_up":
        return VK_PRIOR
    if k == "page_down":
        return VK_NEXT
    if k == "left":
        return VK_LEFT
    if k == "up":
        return VK_UP
    if k == "right":
        return VK_RIGHT
    if k == "down":
        return VK_DOWN
    if k.startswith("numpad"):
        rest = k.replace("numpad", "").strip()
        if rest.isdigit():
            n = int(rest)
            if 0 <= n <= 9:
                return VK_NUMPAD0 + n
    if k.startswith("vk") and k[2:].isdigit():
        return int(k[2:])
    return None


class Win32HotkeyRegistry:
    """RegisterHotKey on a HWND; map hotkey id -> action name."""

    def __init__(self) -> None:
        self._hwnd: int | None = None
        self._id_to_action: dict[int, str] = {}
        self._callbacks: dict[str, Callable[[], None]] = {}
        self._next_id = 1

    def clear(self) -> None:
        if self._hwnd:
            for hid in list(self._id_to_action.keys()):
                try:
                    user32.UnregisterHotKey(self._hwnd, hid)
                except Exception:
                    pass
        self._id_to_action.clear()
        self._next_id = 1

    def register_all(
        self,
        hwnd: int,
        cfg: BindingsConfig,
        callbacks: dict[str, Callable[[], None]],
    ) -> tuple[bool, list[str]]:
        """Returns (all_ok, error_messages)."""
        self.clear()
        self._hwnd = hwnd
        self._callbacks = dict(callbacks)
        errors: list[str] = []
        pending: list[tuple[int, int, int, str]] = []
        for name, ch in cfg.all_assigned():
            cb = callbacks.get(name)
            if cb is None:
                continue
            vk = _key_to_vk(ch)
            if vk is None:
                errors.append(f"{name}: не підтримується Win32 ({ch.display_string()})")
                self.clear()
                return False, errors
            fs = _modifiers_to_fs(ch)
            hid = self._next_id
            self._next_id += 1
            pending.append((hid, fs, vk, name))
        for hid, fs, vk, name in pending:
            ok = user32.RegisterHotKey(hwnd, hid, fs, vk)
            if not ok:
                err = ctypes.get_last_error()
                errors.append(f"{name}: RegisterHotKey failed ({err})")
                self.clear()
                return False, errors
            self._id_to_action[hid] = name
        return True, []

    def dispatch(self, hotkey_id: int) -> None:
        name = self._id_to_action.get(int(hotkey_id))
        if not name:
            return
        cb = self._callbacks.get(name)
        if cb:
            try:
                cb()
            except Exception:
                logging.getLogger(__name__).exception("Win32 hotkey %s", name)

    def stop(self) -> None:
        self.clear()
        self._hwnd = None
        self._callbacks.clear()
