"""Small always-on-top overlay when app is minimized to tray while automation runs."""

from __future__ import annotations

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget

from app.branding import WINDOW_TITLE


class ActivityOverlay(QWidget):
    """Shows status and bind hints; emergency stop."""

    def __init__(self) -> None:
        super().__init__(
            None,
            Qt.WindowType.Tool
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint,
        )
        self.setWindowTitle(WINDOW_TITLE)
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

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self.reposition_right()
