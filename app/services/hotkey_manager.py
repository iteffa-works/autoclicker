"""Registers global hotkeys (Win32 or pynput); UI does not touch WM_* directly."""

from __future__ import annotations

import logging
import sys
from collections.abc import Callable

from app.models.bindings import BindingsConfig
from app.models.settings import HotkeyBackend
from app.services.hotkey_service import HotkeyService
from app.services.win_hotkey_service import Win32HotkeyRegistry


class HotkeyManager:
    def __init__(self) -> None:
        self._pynput = HotkeyService()
        self._win32 = Win32HotkeyRegistry()

    def stop(self) -> None:
        self._pynput.stop()
        self._win32.stop()

    def apply(
        self,
        *,
        backend: HotkeyBackend,
        hwnd: int,
        bindings: BindingsConfig,
        callbacks: dict[str, Callable[[], None]],
        log: logging.Logger | None = None,
    ) -> None:
        lg = log or logging.getLogger(__name__)

        def wrap(fn: Callable[[], None]) -> Callable[[], None]:
            def inner() -> None:
                try:
                    fn()
                except Exception:
                    lg.exception("Hotkey callback")

            return inner

        cb = {k: wrap(v) for k, v in callbacks.items()}
        self.stop()
        be = backend
        if sys.platform == "win32" and hwnd:
            if be in (HotkeyBackend.AUTO, HotkeyBackend.WIN32):
                ok, errs = self._win32.register_all(hwnd, bindings, cb)
                if ok:
                    lg.info("Глобальні клавіші: Win32 RegisterHotKey")
                    return
                for msg in errs:
                    lg.warning("%s", msg)
                if be == HotkeyBackend.WIN32:
                    lg.error("Win32 не вдалося; перевірте бинди")
                    return
        self._pynput.start(bindings, cb)
        lg.info("Глобальні клавіші: pynput")

    def dispatch_win32_hotkey(self, wparam: int) -> None:
        self._win32.dispatch(wparam)
