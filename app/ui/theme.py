"""Light/dark palette via QSS."""

from __future__ import annotations

from app.models.settings import ThemeMode


def stylesheet_for(theme: ThemeMode) -> str:
    if theme == ThemeMode.DARK:
        return """
        QWidget { background-color: #1a1d23; color: #e8eaed; font-size: 13px; }
        QMainWindow { background-color: #1a1d23; }
        QTabWidget::pane { border: 1px solid #353a45; border-radius: 6px; top: -1px; }
        QTabBar::tab { background: #252a33; padding: 10px 16px; margin-right: 2px; border-top-left-radius: 6px; border-top-right-radius: 6px; }
        QTabBar::tab:selected { background: #2d3440; font-weight: 600; }
        QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
            background: #252a33; border: 1px solid #404854; padding: 6px 8px; border-radius: 6px; min-height: 20px;
        }
        QPushButton {
            background: #343b48; border: 1px solid #4a5364; padding: 8px 14px; border-radius: 6px;
        }
        QPushButton:hover { background: #3d4555; }
        QPushButton:pressed { background: #2a303a; }
        QTableWidget { gridline-color: #353a45; border: 1px solid #353a45; border-radius: 6px; }
        QHeaderView::section { background: #252a33; padding: 8px; border: none; border-bottom: 1px solid #353a45; }
        QGroupBox { border: 1px solid #353a45; border-radius: 8px; margin-top: 12px; font-weight: 600; padding-top: 8px; }
        QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; }
        QStatusBar { background: #14171c; border-top: 1px solid #353a45; }
        QLabel#statusLabel { color: #9aa0a6; font-weight: 500; }
        QLabel#statusLabel[state="running"] { color: #81c784; }
        QLabel#statusLabel[state="paused"] { color: #ffb74d; }
        QLabel#statusLabel[state="macro"] { color: #64b5f6; }
        QPushButton#acStart[state="on"] { background: #1b4332; border-color: #2d6a4f; color: #d8f3dc; }
        QPushButton#acPause[state="paused"] { background: #5c4033; border-color: #8d6e63; color: #ffe0b2; }
        QPushButton#acStop[state="danger"] { background: #4a1c1c; border-color: #7f1d1d; color: #fecaca; }
        QTextEdit { background: #12151a; border: 1px solid #353a45; border-radius: 6px; }
        QListWidget { background: #12151a; border: 1px solid #353a45; border-radius: 6px; }
        """
    return """
        QWidget { background-color: #f0f2f5; color: #1a1a1a; font-size: 13px; }
        QMainWindow { background-color: #f0f2f5; }
        QTabWidget::pane { border: 1px solid #d0d4dc; border-radius: 6px; }
        QTabBar::tab { background: #e4e7ec; padding: 10px 16px; margin-right: 2px; border-top-left-radius: 6px; border-top-right-radius: 6px; }
        QTabBar::tab:selected { background: #ffffff; font-weight: 600; }
        QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
            background: #fff; border: 1px solid #c5cad3; padding: 6px 8px; border-radius: 6px; min-height: 20px;
        }
        QPushButton {
            background: #e8ebf0; border: 1px solid #c5cad3; padding: 8px 14px; border-radius: 6px;
        }
        QPushButton:hover { background: #dde1e8; }
        QPushButton:pressed { background: #cfd4dd; }
        QTableWidget { gridline-color: #d0d4dc; border: 1px solid #d0d4dc; border-radius: 6px; }
        QHeaderView::section { background: #e8ebf0; padding: 8px; border: none; border-bottom: 1px solid #d0d4dc; }
        QGroupBox { border: 1px solid #d0d4dc; border-radius: 8px; margin-top: 12px; font-weight: 600; padding-top: 8px; }
        QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; }
        QStatusBar { background: #e4e7ec; border-top: 1px solid #d0d4dc; }
        QLabel#statusLabel { color: #5f6368; font-weight: 500; }
        QLabel#statusLabel[state="running"] { color: #137333; }
        QLabel#statusLabel[state="paused"] { color: #b06000; }
        QLabel#statusLabel[state="macro"] { color: #1967d2; }
        QPushButton#acStart[state="on"] { background: #e6f4ea; border-color: #137333; color: #137333; }
        QPushButton#acPause[state="paused"] { background: #fef7e0; border-color: #f9ab00; color: #b06000; }
        QPushButton#acStop[state="danger"] { background: #fce8e6; border-color: #c5221f; color: #c5221f; }
        QTextEdit { background: #fff; border: 1px solid #d0d4dc; border-radius: 6px; }
        QListWidget { background: #fff; border: 1px solid #d0d4dc; border-radius: 6px; }
    """


def keyboard_styles(theme: ThemeMode) -> tuple[str, str]:
    """idle, active key QLabel stylesheets."""
    if theme == ThemeMode.DARK:
        idle = "QLabel { border: 1px solid #4a5364; border-radius: 4px; background: #252a33; min-width: 26px; min-height: 28px; }"
        active = "QLabel { border: 1px solid #2d6a4f; border-radius: 4px; background: #1b4332; color: #d8f3dc; min-width: 26px; min-height: 28px; }"
        return idle, active
    idle = "QLabel { border: 1px solid #c5cad3; border-radius: 4px; background: #fff; min-width: 26px; min-height: 28px; }"
    active = "QLabel { border: 1px solid #137333; border-radius: 4px; background: #e6f4ea; color: #137333; min-width: 26px; min-height: 28px; }"
    return idle, active
