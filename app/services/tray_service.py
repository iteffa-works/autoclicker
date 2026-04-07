"""System tray icon and menu."""

from __future__ import annotations

from typing import Callable

from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QMenu, QSystemTrayIcon, QWidget


class TrayService:
    def __init__(self, parent: QWidget) -> None:
        self._parent = parent
        self._tray: QSystemTrayIcon | None = None

    def setup(
        self,
        on_show: Callable[[], None],
        on_quit: Callable[[], None],
        tooltip: str,
        icon: QIcon,
    ) -> None:
        self._tray = QSystemTrayIcon(self._parent)
        self._tray.setIcon(icon)
        self._tray.setToolTip(tooltip)
        menu = QMenu()
        act_show = QAction("Показати", self._parent)
        act_show.triggered.connect(on_show)
        act_quit = QAction("Вихід", self._parent)
        act_quit.triggered.connect(on_quit)
        menu.addAction(act_show)
        menu.addAction(act_quit)
        self._tray.setContextMenu(menu)
        self._tray.activated.connect(self._on_activated)

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self._parent.showNormal()
            self._parent.raise_()
            self._parent.activateWindow()

    def ensure_visible(self) -> None:
        if self._tray is None:
            return
        self._tray.setVisible(True)
        self._tray.show()

    def show(self) -> None:
        if self._tray:
            self._tray.show()

    def hide(self) -> None:
        if self._tray:
            self._tray.hide()

    def set_tooltip(self, text: str) -> None:
        if self._tray:
            self._tray.setToolTip(text)
