"""Оверлей статусу при згортанні / поверх ігор (Win32 topmost)."""

from __future__ import annotations

import sys

import ctypes

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget


class ActivityOverlay(QWidget):
    """Shows status and bind hints; emergency stop."""

    def __init__(self) -> None:
        super().__init__(
            None,
            Qt.WindowType.Tool
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint,
        )
        self.setWindowTitle("Flowaxy")
        lay = QVBoxLayout(self)
        self._title = QLabel()
        self._title.setWordWrap(True)
        self._binds = QLabel()
        self._binds.setWordWrap(True)
        self._btn_stop = QPushButton("Зупинити все")
        lay.addWidget(self._title)
        lay.addWidget(self._binds)
        lay.addWidget(self._btn_stop)
        self.setMinimumWidth(220)
        self._btn_stop.clicked.connect(self._on_stop_clicked)
        self._stop_cb = None
        self._opacity = 0.92

    def set_opacity(self, v: float) -> None:
        self._opacity = max(0.3, min(1.0, v))
        self.setWindowOpacity(self._opacity)

    def set_stop_callback(self, cb) -> None:
        self._stop_cb = cb

    def _on_stop_clicked(self) -> None:
        if callable(self._stop_cb):
            self._stop_cb()

    def set_text(self, title: str, binds_html: str) -> None:
        self._title.setText(title)
        self._binds.setText(binds_html)

    def reposition_right(self) -> None:
        screen = QGuiApplication.primaryScreen()
        if not screen:
            return
        g = screen.availableGeometry()
        self.adjustSize()
        m = self.frameGeometry()
        x = g.right() - m.width() - 12
        y = g.top() + 80
        self.move(QPoint(x, y))

    def ensure_topmost_win32(self) -> None:
        """Поверх повноекранних вікон (borderless); exclusive fullscreen може перекривати ОС."""
        if sys.platform != "win32":
            return
        try:
            hwnd = int(self.winId())
        except (AttributeError, TypeError, ValueError):
            return
        if not hwnd:
            return
        HWND_TOPMOST = -1
        SWP_NOMOVE = 0x0002
        SWP_NOSIZE = 0x0001
        SWP_NOACTIVATE = 0x0010
        SWP_SHOWWINDOW = 0x0040
        flags = SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW | SWP_NOACTIVATE
        ctypes.windll.user32.SetWindowPos(hwnd, HWND_TOPMOST, 0, 0, 0, 0, flags)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self.reposition_right()
        self.ensure_topmost_win32()
