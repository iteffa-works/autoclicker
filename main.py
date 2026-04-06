"""Application entry point."""

from __future__ import annotations

import logging
import sys

from PySide6.QtWidgets import QApplication, QStyleFactory
from PySide6.QtWidgets import QSystemTrayIcon

from app.branding import APP_NAME, WINDOW_TITLE
from app.single_instance import SingleInstanceGuard
from app.ui.main_window import MainWindow
from app.utils.app_icon import load_app_icon


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationDisplayName(WINDOW_TITLE)
    app.setQuitOnLastWindowClosed(False)
    app.setStyle(QStyleFactory.create("Fusion"))

    guard = SingleInstanceGuard()
    if not guard.try_acquire():
        return 0

    if not QSystemTrayIcon.isSystemTrayAvailable():
        logging.getLogger(__name__).warning("Системний трей недоступний; згортання в трей може не працювати.")

    icon = load_app_icon()
    if icon.isNull():
        from PySide6.QtWidgets import QStyle

        icon = app.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
    app.setWindowIcon(icon)
    w = MainWindow()
    w.setWindowIcon(icon)
    w.setup_tray(icon)
    guard.activate_requested.connect(w.bring_to_front)
    w.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
