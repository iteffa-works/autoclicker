"""Low-traffic listeners for keyboard/mouse test tab (optional activation)."""

from __future__ import annotations

from pynput import keyboard, mouse
from PySide6.QtCore import QObject, Signal


class KeyboardTestHooks(QObject):
    """Emits signals for UI; start/stop when test tab is active."""

    key_event = Signal(str, bool)
    mouse_button = Signal(str, bool)
    mouse_position = Signal(int, int)
    scroll_event = Signal(int, int)

    def __init__(self) -> None:
        super().__init__()
        self._k: keyboard.Listener | None = None
        self._m: mouse.Listener | None = None

    def start(self) -> None:
        self.stop()

        def on_press(key: keyboard.Key | keyboard.KeyCode | None) -> None:
            self._emit_key(key, True)

        def on_release(key: keyboard.Key | keyboard.KeyCode | None) -> None:
            self._emit_key(key, False)

        def on_click(x: int, y: int, button: mouse.Button, pressed: bool) -> None:
            name = "left"
            if button == mouse.Button.right:
                name = "right"
            elif button == mouse.Button.middle:
                name = "middle"
            self.mouse_button.emit(name, pressed)
            self.mouse_position.emit(int(x), int(y))

        def on_move(x: int, y: int) -> None:
            self.mouse_position.emit(int(x), int(y))

        def on_scroll(x: int, y: int, dx: int, dy: int) -> None:
            self.scroll_event.emit(int(dx), int(dy))

        self._k = keyboard.Listener(on_press=on_press, on_release=on_release)
        self._m = mouse.Listener(
            on_click=on_click,
            on_move=on_move,
            on_scroll=on_scroll,
        )
        self._k.start()
        self._m.start()

    def _emit_key(self, key: keyboard.Key | keyboard.KeyCode | None, down: bool) -> None:
        if isinstance(key, keyboard.Key):
            name = key.name or str(key)
        else:
            try:
                name = key.char if key and getattr(key, "char", None) else f"vk{key.vk}"
            except Exception:
                name = "unknown"
        self.key_event.emit(str(name), down)

    def stop(self) -> None:
        for lst in (self._k, self._m):
            if lst:
                try:
                    lst.stop()
                except Exception:
                    pass
        self._k = None
        self._m = None
