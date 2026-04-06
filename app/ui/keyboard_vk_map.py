"""Windows virtual-key → physical key_id (US QWERTY position) for keyboard test."""

from __future__ import annotations

# Physical letter keys: VK (winuser) → key_id used by KeyboardTestPanel
_VK_LETTERS: dict[int, str] = {
    0x51: "q",
    0x57: "w",
    0x45: "e",
    0x52: "r",
    0x54: "t",
    0x59: "y",
    0x55: "u",
    0x49: "i",
    0x4F: "o",
    0x50: "p",
    0x41: "a",
    0x53: "s",
    0x44: "d",
    0x46: "f",
    0x47: "g",
    0x48: "h",
    0x4A: "j",
    0x4B: "k",
    0x4C: "l",
    0x5A: "z",
    0x58: "x",
    0x43: "c",
    0x56: "v",
    0x42: "b",
    0x4E: "n",
    0x4D: "m",
}

VK_TO_KEY_ID: dict[int, str] = {
    0x1B: "escape",
    0xC0: "`",
    0x31: "1",
    0x32: "2",
    0x33: "3",
    0x34: "4",
    0x35: "5",
    0x36: "6",
    0x37: "7",
    0x38: "8",
    0x39: "9",
    0x30: "0",
    0xBD: "-",
    0xBB: "=",
    0x08: "backspace",
    0x09: "tab",
    0xDB: "[",
    0xDD: "]",
    0xDC: "\\",
    0x14: "caps_lock",
    0x0D: "enter",
    0x10: "shift",
    0xA0: "shift",
    0xA1: "shift_r",
    0xBA: ";",
    0xDE: "'",
    0xBC: ",",
    0xBE: ".",
    0xBF: "/",
    0x20: "space",
    0xA2: "ctrl_l",
    0xA3: "ctrl_r",
    0xA4: "alt",
    0xA5: "alt_r",
    0x5B: "cmd",
    0x5C: "cmd_r",
    0x5D: "apps",
    0x25: "left",
    0x26: "up",
    0x27: "right",
    0x28: "down",
    0x2D: "insert",
    0x24: "home",
    0x21: "page_up",
    0x2E: "delete",
    0x23: "end",
    0x22: "page_down",
    0x2C: "print_screen",
    0x91: "scroll_lock",
    0x13: "pause",
    0x90: "num_lock",
    0x60: "numpad0",
    0x61: "numpad1",
    0x62: "numpad2",
    0x63: "numpad3",
    0x64: "numpad4",
    0x65: "numpad5",
    0x66: "numpad6",
    0x67: "numpad7",
    0x68: "numpad8",
    0x69: "numpad9",
    0x6E: "decimal",
    0x6F: "numpad_divide",
    0x6A: "numpad_multiply",
    0x6D: "numpad_subtract",
    0x6B: "numpad_add",
}
VK_TO_KEY_ID.update(_VK_LETTERS)

for _fi in range(12):
    VK_TO_KEY_ID[0x70 + _fi] = f"f{_fi + 1}"

# key_id → VK (для ToUnicode / підписів); без 0x10 (дублікат shift)
KEY_ID_TO_VK: dict[str, int] = {v: k for k, v in VK_TO_KEY_ID.items() if k != 0x10}

_FIXED_LABEL_KEYS = frozenset(
    {
        "shift",
        "shift_r",
        "ctrl_l",
        "ctrl_r",
        "alt",
        "alt_r",
        "cmd",
        "cmd_r",
        "apps",
        "tab",
        "caps_lock",
        "enter",
        "backspace",
        "space",
        "left",
        "up",
        "right",
        "down",
        "escape",
        "insert",
        "home",
        "page_up",
        "delete",
        "end",
        "page_down",
        "print_screen",
        "scroll_lock",
        "pause",
        "num_lock",
        "numpad_divide",
        "numpad_multiply",
        "numpad_subtract",
        "numpad_add",
    }
    | {f"f{i}" for i in range(1, 13)}
)

KEY_ID_TO_VK_LAYOUT_ONLY: dict[str, int] = {
    k: v for k, v in KEY_ID_TO_VK.items() if k not in _FIXED_LABEL_KEYS
}


def vk_to_key_id(vk: int) -> str | None:
    """Return panel key_id for a Windows VK, or None if unmapped."""
    if vk in VK_TO_KEY_ID:
        return VK_TO_KEY_ID[vk]
    if vk == 0x11:
        return "ctrl_l"
    if vk == 0x12:
        return "alt"
    return None
