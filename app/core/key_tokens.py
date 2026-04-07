"""Shared helpers for pynput key token parsing/normalization."""

from __future__ import annotations

from pynput.keyboard import Key, KeyCode


def key_token_from_pynput(vk: Key | KeyCode | None) -> str:
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


def normalize_key_token(raw: str) -> str:
    t = raw.lower().strip()
    if t == "esc":
        return "escape"
    return t


def mod_name_from_key(key: Key | KeyCode | None) -> str | None:
    if key == Key.ctrl_l or key == Key.ctrl_r:
        return "ctrl"
    if key == Key.alt_l or key == Key.alt_r:
        return "alt"
    if key == Key.shift_l or key == Key.shift_r:
        return "shift"
    if key == Key.cmd:
        return "win"
    return None


def parse_key_token(token: str) -> Key | KeyCode | None:
    t = normalize_key_token(token)
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
    if t.startswith("f") and len(t) > 1 and t[1:].isdigit():
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
        return fs.get(int(t[1:]))
    if len(t) == 1:
        return KeyCode.from_char(t)
    if t.startswith("vk") and t[2:].isdigit():
        return KeyCode.from_vk(int(t[2:]))
    return None
