"""Light/dark QSS: плоский стиль, нейтральні рамки + помірний червоний акцент."""

from __future__ import annotations

import base64

from app.models.settings import ThemeMode


def _svg_check_data_url(stroke: str) -> str:
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16">'
        f'<path fill="none" stroke="{stroke}" stroke-width="2.2" stroke-linecap="round" '
        f'stroke-linejoin="round" d="M3.5 8.2l2.8 2.8 6.2-7.5"/></svg>'
    )
    b = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return f"data:image/svg+xml;base64,{b}"

# Темна тема
_D_BG = "#14161c"
_D_BG_PANEL = "#181c24"
_D_BG_INPUT = "#1e232d"
_D_BG_DEEP = "#0f1117"
_D_BORDER = "#383e4c"
_D_BORDER_STRONG = "#4a5568"
_D_TEXT_MUTED = "#9aa5b0"
_D_ACCENT = "#c62828"
_D_ACCENT_SOFT = "#e57373"
_D_ROSE_TEXT = "#f8bbd0"

# Світла тема
_L_BG = "#f0f2f5"
_L_SURFACE = "#ffffff"
_L_BORDER = "#d8dde5"
_L_BORDER_STRONG = "#c5ccd6"
_L_TEXT_MUTED = "#5c6c76"
_L_ACCENT = "#c62828"
_L_ACCENT_SOFT = "#ad1457"


def stylesheet_for(theme: ThemeMode) -> str:
    chk_dark = _svg_check_data_url("#e57373")
    chk_light = _svg_check_data_url("#c62828")
    if theme == ThemeMode.DARK:
        b = _D_BORDER
        ba = _D_ACCENT
        return f"""
        QWidget {{ background-color: {_D_BG}; color: #eceff1; font-size: 13px; }}
        QMainWindow {{ background-color: {_D_BG}; }}
        QWidget#heroSidebar {{
            background: {_D_BG_DEEP};
            border-right: 1px solid {ba};
            min-width: 268px;
            max-width: 320px;
        }}
        QLabel#heroImage {{ background: transparent; }}
        QLabel#heroTag {{
            color: {_D_ACCENT_SOFT};
            font-size: 10px;
            font-weight: 700;
            letter-spacing: 0.35em;
            padding: 12px 0 8px 0;
            border-top: 1px solid {_D_BORDER_STRONG};
        }}
        QLabel#heroBlurb {{ color: {_D_TEXT_MUTED}; font-size: 11px; padding: 4px 4px 0 4px; }}
        QLabel#heroStudioLine {{ color: #eceff1; font-size: 12px; font-weight: 600; padding-top: 6px; }}
        QLabel#heroLink {{ font-size: 12px; font-weight: 600; padding: 2px; }}
        QLabel#heroMail {{ font-size: 11px; color: #b0bec5; padding: 2px; }}
        QLabel#heroVersion {{ color: {_D_TEXT_MUTED}; font-size: 10px; padding-top: 8px; }}
        QTabBar#mainTabBar {{
            background: {_D_BG_DEEP};
            border-bottom: 1px solid {b};
            padding: 10px 14px 0 14px;
        }}
        QTabBar#mainTabBar::tab {{
            background: {_D_BG_PANEL};
            min-width: 5em;
            padding: 10px 14px;
            margin-right: 4px;
            border-top-left-radius: 6px;
            border-top-right-radius: 6px;
            border: 1px solid {b};
            border-bottom: none;
            color: {_D_TEXT_MUTED};
        }}
        QTabBar#mainTabBar::tab:selected {{
            background: {_D_BG_INPUT};
            font-weight: 600;
            color: {_D_ROSE_TEXT};
            border-color: {ba};
            border-bottom: 2px solid {ba};
        }}
        QTabBar#mainTabBar::tab:hover:!selected {{
            background: #222831;
            color: #eceff1;
            border-color: {_D_BORDER_STRONG};
        }}
        QFrame#mainContentFrame {{
            background: {_D_BG_PANEL};
            border: 1px solid {_D_BORDER_STRONG};
            border-radius: 8px;
        }}
        QStackedWidget#mainStack {{
            border: none;
            border-radius: 4px;
            background: {_D_BG_PANEL};
        }}
        QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
            background: {_D_BG_INPUT};
            border: 1px solid {b};
            padding: 7px 10px;
            border-radius: 6px;
            min-height: 20px;
            color: #eceff1;
            selection-background-color: #7f2a35;
            selection-color: #fff;
        }}
        QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {{
            border: 1px solid {ba};
        }}
        QPushButton {{
            background: #252b36;
            border: 1px solid {b};
            padding: 8px 16px;
            border-radius: 6px;
            color: #eceff1;
        }}
        QPushButton:hover {{ background: #2d3440; border-color: {_D_BORDER_STRONG}; }}
        QPushButton:pressed {{ background: #1a1e26; }}
        QTableWidget {{
            gridline-color: {b};
            border: 1px solid {b};
            border-radius: 6px;
            background: {_D_BG_INPUT};
        }}
        QHeaderView::section {{
            background: #222830;
            padding: 8px 10px;
            border: none;
            border-bottom: 1px solid {b};
            color: {_D_TEXT_MUTED};
            font-weight: 600;
        }}
        QGroupBox {{
            border: 1px solid {b};
            border-radius: 6px;
            margin-top: 14px;
            font-weight: 600;
            padding-top: 12px;
            color: #eceff1;
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 12px;
            padding: 0 8px;
            color: {_D_ACCENT_SOFT};
        }}
        QStatusBar {{
            background: {_D_BG_DEEP};
            border-top: 1px solid {b};
            color: {_D_TEXT_MUTED};
        }}
        QLabel#statusLabel {{ color: {_D_TEXT_MUTED}; font-weight: 500; }}
        QLabel#statusLabel[state="running"] {{ color: #81c784; }}
        QLabel#statusLabel[state="paused"] {{ color: #ffb74d; }}
        QLabel#statusLabel[state="macro"] {{ color: #64b5f6; }}
        QLabel#logSectionTitle {{ color: {_D_TEXT_MUTED}; font-weight: 600; font-size: 12px; padding: 4px 0 2px 0; }}
        QPushButton#acStart[state="on"] {{
            background: #1b3328;
            border: 1px solid #43a047;
            color: #e8f5e9;
        }}
        QPushButton#acPause[state="paused"] {{
            background: #3e3028;
            border: 1px solid #b8860b;
            color: #ffe0b2;
        }}
        QPushButton#acStop[state="danger"] {{
            background: #2d1a1e;
            border: 1px solid {ba};
            color: {_D_ROSE_TEXT};
        }}
        QTextEdit#eventLog {{
            background: {_D_BG_DEEP};
            border: 1px solid {b};
            border-left: 3px solid {ba};
            border-radius: 6px;
            color: #cfd8dc;
        }}
        QListWidget {{
            background: {_D_BG_INPUT};
            border: 1px solid {b};
            border-radius: 6px;
        }}
        QCheckBox {{ spacing: 10px; color: #eceff1; }}
        QCheckBox::indicator {{
            width: 17px;
            height: 17px;
            border: 1px solid {b};
            border-radius: 4px;
            background: {_D_BG_INPUT};
        }}
        QCheckBox::indicator:checked {{
            background: #252a34;
            border: 1px solid {ba};
            image: url({chk_dark});
        }}
        """
    b = _L_BORDER
    ba = _L_ACCENT
    return f"""
        QWidget {{ background-color: {_L_BG}; color: #212121; font-size: 13px; }}
        QMainWindow {{ background-color: {_L_BG}; }}
        QWidget#heroSidebar {{
            background: {_L_SURFACE};
            border-right: 1px solid {ba};
            min-width: 268px;
            max-width: 320px;
        }}
        QLabel#heroImage {{ background: transparent; }}
        QLabel#heroTag {{
            color: {ba};
            font-size: 10px;
            font-weight: 700;
            letter-spacing: 0.35em;
            padding: 12px 0 8px 0;
            border-top: 1px solid {_L_BORDER_STRONG};
        }}
        QLabel#heroBlurb {{ color: {_L_TEXT_MUTED}; font-size: 11px; padding: 4px 4px 0 4px; }}
        QLabel#heroStudioLine {{ color: #263238; font-size: 12px; font-weight: 600; padding-top: 6px; }}
        QLabel#heroLink {{ font-size: 12px; font-weight: 600; padding: 2px; }}
        QLabel#heroMail {{ font-size: 11px; padding: 2px; }}
        QLabel#heroVersion {{ color: {_L_TEXT_MUTED}; font-size: 10px; padding-top: 8px; }}
        QTabBar#mainTabBar {{
            background: {_L_SURFACE};
            border-bottom: 1px solid {b};
            padding: 10px 14px 0 14px;
        }}
        QTabBar#mainTabBar::tab {{
            background: #f5f5f7;
            min-width: 5em;
            padding: 10px 14px;
            margin-right: 4px;
            border-top-left-radius: 6px;
            border-top-right-radius: 6px;
            border: 1px solid {b};
            border-bottom: none;
            color: {_L_TEXT_MUTED};
        }}
        QTabBar#mainTabBar::tab:selected {{
            background: {_L_SURFACE};
            font-weight: 600;
            color: {ba};
            border-color: {ba};
            border-bottom: 2px solid {ba};
        }}
        QTabBar#mainTabBar::tab:hover:!selected {{ background: #fafafa; border-color: {_L_BORDER_STRONG}; }}
        QFrame#mainContentFrame {{
            background: {_L_SURFACE};
            border: 1px solid {_L_BORDER_STRONG};
            border-radius: 8px;
        }}
        QStackedWidget#mainStack {{
            border: none;
            border-radius: 4px;
            background: {_L_SURFACE};
        }}
        QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
            background: {_L_SURFACE};
            border: 1px solid {b};
            padding: 7px 10px;
            border-radius: 6px;
            min-height: 20px;
            selection-background-color: #ffcdd2;
            selection-color: #4a0e16;
        }}
        QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {{
            border: 1px solid {ba};
        }}
        QPushButton {{
            background: {_L_SURFACE};
            border: 1px solid {b};
            padding: 8px 16px;
            border-radius: 6px;
            color: #37474f;
        }}
        QPushButton:hover {{ background: #f5f5f7; border-color: {_L_BORDER_STRONG}; }}
        QPushButton:pressed {{ background: #eceff1; }}
        QTableWidget {{
            gridline-color: #e8eaed;
            border: 1px solid {b};
            border-radius: 6px;
            background: {_L_SURFACE};
        }}
        QHeaderView::section {{
            background: #f5f6f8;
            padding: 8px 10px;
            border: none;
            border-bottom: 1px solid {b};
            color: #455a64;
            font-weight: 600;
        }}
        QGroupBox {{
            border: 1px solid {b};
            border-radius: 6px;
            margin-top: 14px;
            font-weight: 600;
            padding-top: 12px;
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 12px;
            padding: 0 8px;
            color: {_L_ACCENT_SOFT};
        }}
        QStatusBar {{ background: {_L_SURFACE}; border-top: 1px solid {b}; }}
        QLabel#statusLabel {{ color: #5f6368; font-weight: 500; }}
        QLabel#statusLabel[state="running"] {{ color: #137333; }}
        QLabel#statusLabel[state="paused"] {{ color: #b06000; }}
        QLabel#statusLabel[state="macro"] {{ color: #1967d2; }}
        QLabel#logSectionTitle {{ color: {_L_TEXT_MUTED}; font-weight: 600; font-size: 12px; padding: 4px 0 2px 0; }}
        QPushButton#acStart[state="on"] {{
            background: #e8f5e9;
            border: 1px solid #43a047;
            color: #1b5e20;
        }}
        QPushButton#acPause[state="paused"] {{
            background: #fff8e1;
            border: 1px solid #f9a825;
            color: #b06000;
        }}
        QPushButton#acStop[state="danger"] {{
            background: #ffebee;
            border: 1px solid {ba};
            color: {ba};
        }}
        QTextEdit#eventLog {{
            background: {_L_SURFACE};
            border: 1px solid {b};
            border-left: 3px solid {ba};
            border-radius: 6px;
        }}
        QListWidget {{
            background: {_L_SURFACE};
            border: 1px solid {b};
            border-radius: 6px;
        }}
        QCheckBox {{ spacing: 10px; }}
        QCheckBox::indicator {{
            width: 17px;
            height: 17px;
            border: 1px solid {b};
            border-radius: 4px;
            background: {_L_SURFACE};
        }}
        QCheckBox::indicator:checked {{
            background: #fafafa;
            border: 1px solid {ba};
            image: url({chk_light});
        }}
    """


def keyboard_styles(theme: ThemeMode) -> tuple[str, str]:
    """idle, active key QLabel stylesheets."""
    if theme == ThemeMode.DARK:
        idle = (
            "QLabel { border: 1px solid #383e4c; border-radius: 4px; background: #1e232d; "
            "min-width: 26px; min-height: 28px; }"
        )
        active = (
            "QLabel { border: 1px solid #c62828; border-radius: 4px; background: #2d1f24; "
            "color: #f8bbd0; min-width: 26px; min-height: 28px; }"
        )
        return idle, active
    idle = (
        "QLabel { border: 1px solid #d8dde5; border-radius: 4px; background: #ffffff; "
        "min-width: 26px; min-height: 28px; }"
    )
    active = (
        "QLabel { border: 1px solid #c62828; border-radius: 4px; background: #fce4ec; "
        "color: #880e4f; min-width: 26px; min-height: 28px; }"
    )
    return idle, active
