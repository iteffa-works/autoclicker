"""Windows: поточна розкладка → символи на фізичних клавішах (ToUnicodeEx)."""

from __future__ import annotations

import ctypes
from ctypes import wintypes

_user32 = ctypes.windll.user32
_user32.MapVirtualKeyExW.argtypes = [wintypes.UINT, wintypes.UINT, wintypes.HANDLE]
_user32.MapVirtualKeyExW.restype = wintypes.UINT


def _hkl_u64(hkl: int) -> int:
    return hkl & 0xFFFFFFFFFFFFFFFF


def current_hkl() -> int:
    return int(_user32.GetKeyboardLayout(0))


def vk_to_display_char(vk: int, hkl: int | None = None) -> str:
    """Символ без Shift для даного VK у вказаній (або поточній) розкладці."""
    if hkl is None:
        hkl = current_hkl()
    h64 = _hkl_u64(hkl)
    handle = wintypes.HANDLE(h64)
    scan = _user32.MapVirtualKeyExW(wintypes.UINT(vk), 0, handle)
    state = (ctypes.c_byte * 256)()
    buf = ctypes.create_unicode_buffer(8)
    n = _user32.ToUnicodeEx(
        wintypes.UINT(vk),
        wintypes.UINT(scan),
        state,
        buf,
        8,
        0,
        handle,
    )
    if n > 0 and buf.value:
        return buf.value[0]
    if n < 0:
        _user32.ToUnicodeEx(
            wintypes.UINT(vk),
            wintypes.UINT(scan),
            state,
            buf,
            8,
            0,
            handle,
        )
    return ""


def display_labels_for_vks(vk_by_key_id: dict[str, int], hkl: int | None = None) -> dict[str, str]:
    """key_id → один символ для відображення (порожній рядок якщо ToUnicode не дав символ)."""
    if hkl is None:
        hkl = current_hkl()
    out: dict[str, str] = {}
    for kid, vk in vk_by_key_id.items():
        ch = vk_to_display_char(vk, hkl)
        if ch and not ch.isspace():
            out[kid] = ch
        elif ch == " ":
            out[kid] = "␣"
        else:
            out[kid] = ""
    return out
