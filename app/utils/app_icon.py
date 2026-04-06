"""Load application window/tray icon from bundled assets."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtGui import QIcon

from app.utils.paths import assets_dir


def load_app_icon() -> QIcon:
    """Return QIcon from assets/icons/favicon.png, or empty QIcon if missing."""
    path = assets_dir() / "icons" / "favicon.png"
    if path.is_file():
        icon = QIcon(str(path))
        if not icon.isNull():
            return icon
    return QIcon()
