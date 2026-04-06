"""Optional Windows beeps for start/stop."""

from __future__ import annotations

import sys


def play_beep(kind: str) -> None:
    if sys.platform != "win32":
        return
    try:
        import winsound
    except ImportError:
        return
    if kind == "start":
        winsound.MessageBeep(winsound.MB_ICONASTERISK)
    else:
        winsound.MessageBeep(winsound.MB_ICONHAND)
