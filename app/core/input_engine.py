"""Facade for low-level mouse/keyboard input (pynput)."""

from __future__ import annotations

from pynput.mouse import Controller as MouseController


class InputEngine:
    """Mouse position and future keyboard helpers; keeps pynput out of UI code."""

    def __init__(self) -> None:
        self._mouse = MouseController()

    def get_mouse_position(self) -> tuple[int, int]:
        p = self._mouse.position
        return int(p[0]), int(p[1])

    def set_mouse_position(self, x: int, y: int) -> None:
        self._mouse.position = (int(x), int(y))
