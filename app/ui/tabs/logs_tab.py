"""Logs tab (layout only)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from app.i18n import normalize_ui_language, tr

if TYPE_CHECKING:
    from app.ui.main_window import MainWindow


def build_logs_tab(main: MainWindow) -> QWidget:
    w = QWidget()
    lay = QVBoxLayout(w)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(6)
    head = QHBoxLayout()
    head.setSpacing(8)
    _log_icon = QLabel()
    _log_icon.setObjectName("sectionTitleIcon")
    main._register_icon_widget(_log_icon, "section_logs", "section")
    _log_title = QLabel(tr(normalize_ui_language(main._settings.ui_language), "logs.title"))
    _log_title.setObjectName("logSectionTitle")
    head.addWidget(_log_icon, 0, Qt.AlignmentFlag.AlignVCenter)
    head.addWidget(_log_title, 0, Qt.AlignmentFlag.AlignVCenter)
    head.addStretch(1)
    lay.addLayout(head)
    lay.addWidget(main._log_edit, 1)
    return w
