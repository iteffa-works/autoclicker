"""Light/dark QSS from design_tokens (slate + indigo)."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from app.models.settings import ThemeMode
from app.ui import design_tokens as T

# QSS `image:` — pixmap з qtawesome пишемо у тимчасовий PNG (один файл на процес, перезапис при зміні теми).
_chk_qta_png: Path | None = None


def _checkbox_checked_qta_url(theme: ThemeMode) -> str:
    from app.ui.app_icons import checkbox_checked_pixmap

    global _chk_qta_png
    pm = checkbox_checked_pixmap(theme)
    if _chk_qta_png is None:
        _chk_qta_png = Path(tempfile.gettempdir()) / f"autoclicker_chk_{os.getpid()}.png"
    pm.save(str(_chk_qta_png), "PNG")
    return _chk_qta_png.resolve().as_uri()


# QSpinBox/QComboBox: border-трикутники (width:0) на Windows часто стають квадратами — PNG у image:.
_SPIN_UP_DARK = "iVBORw0KGgoAAAANSUhEUgAAAAwAAAAICAYAAADN5B7xAAAAL0lEQVR4nGNgGDAwZfGO/9jEmfApxqYJQwO6InQ+VhvwARQNuNyNLA7XgEsxujwAGf4aaYb1sjsAAAAASUVORK5CYII="
_SPIN_DOWN_DARK = "iVBORw0KGgoAAAANSUhEUgAAAAwAAAAICAYAAADN5B7xAAAAOUlEQVR4nGNgIBEwwhhTFu/4T0hxTqwHIxMyh5BiBgYGBrgGfJqQxVE0EAMwNKDbQsipcEBMIBAFAPzrDWSBzvGzAAAAAElFTkSuQmCC"
_SPIN_UP_LIGHT = "iVBORw0KGgoAAAANSUhEUgAAAAwAAAAICAYAAADN5B7xAAAAL0lEQVR4nGNgGDCQUtL9H5s4Ez7F2DRhaEBXhM7HagM+gKIBl7uRxeEacClGlwcAdcYVfaJFF3sAAAAASUVORK5CYII="
_SPIN_DOWN_LIGHT = "iVBORw0KGgoAAAANSUhEUgAAAAwAAAAICAYAAADN5B7xAAAAOUlEQVR4nGNgIBEwwhgpJd3/CSme01PKyITMIaSYgYGBAa4BnyZkcRQNxAAMDei2EHIqHBATCEQBAFsXECDnr5qNAAAAAElFTkSuQmCC"


def _check_indicator_data_url(png_b64: str) -> str:
    return f"data:image/png;base64,{png_b64}"


def stylesheet_for(theme: ThemeMode) -> str:
    chk_on = _checkbox_checked_qta_url(theme)
    spin_u_d = _check_indicator_data_url(_SPIN_UP_DARK)
    spin_d_d = _check_indicator_data_url(_SPIN_DOWN_DARK)
    spin_u_l = _check_indicator_data_url(_SPIN_UP_LIGHT)
    spin_d_l = _check_indicator_data_url(_SPIN_DOWN_LIGHT)
    if theme == ThemeMode.DARK:
        bg = T.D_BG_APP
        surf = T.D_BG_SURFACE
        surf2 = T.D_BG_SURFACE2
        b = T.D_BORDER_SUBTLE
        bf = T.D_BORDER_FOCUS
        tp = T.D_TEXT_PRIMARY
        ts = T.D_TEXT_SECONDARY
        td = T.D_TEXT_DISABLED
        ac = T.D_ACCENT
        ach = T.D_ACCENT_HOVER
        aca = T.D_ACCENT_ACTIVE
        err = T.D_STATE_ERROR
        ok = T.D_STATE_SUCCESS
        warn = T.D_STATE_WARNING
        sel_bg = T.D_SELECTION_BG
        sel_fg = T.D_SELECTION_FG
        return f"""
        QWidget {{ background-color: {bg}; color: {tp}; font-size: 13px; }}
        QMainWindow {{ background-color: {bg}; }}
        QWidget#headerBar {{
            background: {T.D_BG_ELEVATED};
            border-bottom: 1px solid {b};
            min-height: 48px;
        }}
        QPushButton#headerNavButton {{
            background: transparent;
            border: none;
            border-radius: 6px;
            icon-size: 16px;
            padding: 6px 6px 8px 6px;
            margin: 0px 1px;
            font-size: 11px;
            font-weight: 500;
            color: {ts};
        }}
        QPushButton#headerNavButton:hover {{
            background: rgba(148,163,184,0.1);
            color: {tp};
        }}
        QPushButton#headerNavButton:checked {{
            background: rgba(99,102,241,0.15);
            color: {tp};
            border-bottom: 3px solid {ac};
            padding: 6px 6px 5px 6px;
        }}
        QPushButton#headerActionButton {{
            padding: 4px 8px 5px 6px;
            font-size: 11px;
            font-weight: 500;
            border-radius: 8px;
            icon-size: 16px;
        }}
        QPushButton#acStart, QPushButton#acPause, QPushButton#acStop {{
            padding: 4px 8px 5px 6px;
            font-size: 11px;
            icon-size: 16px;
        }}
        QPushButton#macroSideButton {{
            text-align: left;
            padding: 4px 6px 5px 6px;
            font-size: 10px;
            icon-size: 16px;
        }}
        QLabel#headerTitle {{ color: {tp}; font-size: 15px; font-weight: 600; }}
        QWidget#appFooter {{
            background: #0A0F18;
            border-top: 1px solid #DC2626;
            min-height: 34px;
        }}
        QLabel#footerSecondary {{
            color: {td};
            font-size: 11px;
        }}
        QLabel#footerStatusLabel {{
            color: {ts};
            font-size: 13px;
            font-weight: 500;
            padding: 4px 12px;
            border-radius: 6px;
            background: {surf2};
        }}
        QLabel#footerStatusLabel[state="running"] {{ color: {ok}; background: rgba(34,197,94,0.12); }}
        QLabel#footerStatusLabel[state="paused"] {{ color: {warn}; background: rgba(245,158,11,0.12); }}
        QLabel#footerStatusLabel[state="macro"] {{ color: {ach}; background: rgba(99,102,241,0.15); }}
        QWidget#brandingPanel {{
            background: #0A0F18;
        }}
        QFrame#sidebarVerticalDivider {{
            border: none;
            background: #DC2626;
            max-width: 2px;
            min-width: 2px;
        }}
        QLabel#sidebarCharacter {{
            background: #000000;
        }}
        QFrame#brandDivider {{
            border: none;
            background: #DC2626;
            max-height: 2px;
        }}
        QLabel#brandTitle {{
            color: #EF4444;
            font-size: 18px;
            font-weight: 700;
            letter-spacing: 0.02em;
        }}
        QLabel#brandProductSubtitle {{
            color: {tp};
            font-size: 12px;
            font-weight: 600;
            line-height: 1.3;
        }}
        QLabel#brandBlurb {{
            color: {ts};
            font-size: 11px;
            line-height: 1.45;
        }}
        QLabel#brandTagline {{
            color: {ts};
            font-size: 11px;
            line-height: 1.35;
        }}
        QLabel#brandAuthor {{
            color: {tp};
            font-size: 13px;
        }}
        QLabel#brandSectionTitle {{
            color: {td};
            font-size: 10px;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }}
        QLabel#brandFeaturesList {{
            color: {ts};
            font-size: 11px;
            line-height: 1.5;
        }}
        QLabel#brandHint {{
            color: {td};
            font-size: 10px;
            line-height: 1.45;
            font-style: italic;
        }}
        QFrame#brandInfoCard {{
            background: rgba(15, 23, 42, 0.72);
            border: 1px solid {b};
            border-radius: 10px;
        }}
        QLabel#brandLink {{
            font-size: 12px;
        }}
        QLabel#brandVersion {{
            color: {td};
            font-size: 11px;
            margin-top: 2px;
        }}
        QWidget#contentArea {{ background: {bg}; }}
        QScrollArea {{ border: none; background: transparent; }}
        QScrollArea > QWidget > QWidget {{ background: transparent; }}
        QFrame#settingsSectionDivider {{
            border: none;
            background: {b};
            max-height: 1px;
            min-height: 1px;
        }}
        QFrame#contentCard {{
            background: {surf};
            border: 1px solid {b};
            border-radius: 8px;
        }}
        QLabel#sectionTitle {{
            color: {tp};
            font-size: 13px;
            font-weight: 700;
            margin: 0;
            padding: 0;
            background: transparent;
            border: none;
        }}
        QLabel#sectionTitleIcon {{
            min-width: 20px;
            min-height: 20px;
            background: transparent;
            border: none;
        }}
        QLabel#formFieldLabel {{
            color: {ts};
            font-size: 11px;
            font-weight: 600;
            padding: 3px 5px;
            background: rgba(15,23,42,0.55);
            border: 1px solid {b};
            border-radius: 6px;
        }}
        QLabel#formHint {{
            color: {td};
            font-size: 11px;
            padding-top: 1px;
        }}
        QLabel#formInlineLabel {{
            color: {ts};
            font-size: 12px;
            font-weight: 500;
            padding: 4px 4px 4px 0;
        }}
        QLabel#settingsFieldLabel {{
            color: {ts};
            font-size: 10px;
            font-weight: 600;
            padding: 1px 4px;
            background: rgba(15,23,42,0.45);
            border: 1px solid {b};
            border-radius: 4px;
        }}
        QLabel#settingsSectionTitle {{
            color: {tp};
            font-size: 12px;
            font-weight: 600;
            margin: 0;
            padding: 0;
        }}
        QStackedWidget#mainStack {{
            border: none;
            background: transparent;
        }}
        QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
            background: {surf2};
            border: 1px solid {b};
            border-radius: 8px;
            min-height: 28px;
            color: {tp};
            selection-background-color: {sel_bg};
            selection-color: {sel_fg};
        }}
        QLineEdit {{
            padding: 6px 8px;
        }}
        QLineEdit:focus {{
            border: 1px solid {bf};
            background: {surf2};
        }}
        QSpinBox, QDoubleSpinBox {{
            padding: 5px 8px;
            padding-right: 30px;
        }}
        QSpinBox:focus, QDoubleSpinBox:focus {{
            border: 1px solid {bf};
            background: {surf2};
        }}
        QSpinBox::up-button, QDoubleSpinBox::up-button {{
            subcontrol-origin: border;
            subcontrol-position: top right;
            width: 28px;
            border-left: 1px solid {b};
            border-top-right-radius: 7px;
            background: #111827;
        }}
        QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover {{
            background: #334155;
        }}
        QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {{
            image: url({spin_u_d});
            width: 12px;
            height: 8px;
            margin-right: 8px;
            margin-bottom: 2px;
        }}
        QSpinBox::down-button, QDoubleSpinBox::down-button {{
            subcontrol-origin: border;
            subcontrol-position: bottom right;
            width: 28px;
            border-left: 1px solid {b};
            border-bottom-right-radius: 7px;
            background: #111827;
        }}
        QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {{
            background: #334155;
        }}
        QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {{
            image: url({spin_d_d});
            width: 12px;
            height: 8px;
            margin-right: 8px;
            margin-top: 2px;
        }}
        QComboBox {{
            padding: 5px 8px;
            padding-right: 30px;
        }}
        QComboBox:focus {{
            border: 1px solid {bf};
            background: {surf2};
        }}
        QComboBox::drop-down {{
            subcontrol-origin: padding;
            subcontrol-position: top right;
            width: 32px;
            border-left: 1px solid {b};
            border-top-right-radius: 7px;
            border-bottom-right-radius: 7px;
            background: #111827;
        }}
        QComboBox::drop-down:hover {{
            background: #334155;
        }}
        QComboBox::down-arrow {{
            image: url({spin_d_d});
            width: 12px;
            height: 8px;
            margin-right: 10px;
        }}
        QComboBox QAbstractItemView {{
            background: {surf2};
            border: 1px solid {b};
            selection-background-color: {sel_bg};
            selection-color: {sel_fg};
            padding: 4px;
        }}
        QPushButton {{
            background: {surf2};
            border: 1px solid {b};
            padding: 7px 12px;
            border-radius: 8px;
            min-height: 18px;
            color: {tp};
        }}
        QPushButton:hover {{ background: #273549; border-color: #475569; }}
        QPushButton:pressed {{ background: {surf}; }}
        QPushButton:disabled {{ color: {td}; background: {surf}; border-color: {b}; }}
        QTableWidget {{
            gridline-color: {b};
            border: 1px solid {b};
            border-radius: 8px;
            background: {surf2};
            alternate-background-color: rgba(15,23,42,0.55);
        }}
        QTableWidget::item {{
            padding: 4px 6px;
        }}
        QTableWidget::item:selected {{
            background: rgba(99,102,241,0.2);
            color: {tp};
        }}
        QTableWidget QLineEdit,
        QTableWidget QLineEdit:focus,
        QAbstractItemView QLineEdit,
        QAbstractItemView QLineEdit:focus {{
            background: {surf2};
            border: 1px solid {bf};
            border-radius: 4px;
            padding: 3px 6px;
            color: {tp};
            selection-background-color: {sel_bg};
            selection-color: {sel_fg};
        }}
        QHeaderView::section {{
            background: {surf};
            padding: 6px 8px;
            border: none;
            border-right: 1px solid {b};
            border-bottom: 1px solid {b};
            color: {tp};
            font-weight: 600;
            font-size: 11px;
        }}
        QHeaderView::section:last {{
            border-right: none;
        }}
        QPushButton#seqRowButton {{
            padding: 5px 10px;
            font-size: 11px;
            font-weight: 500;
        }}
        QGroupBox {{
            border: 1px solid {b};
            border-radius: 8px;
            margin-top: 8px;
            font-weight: 600;
            padding-top: 16px;
            color: {tp};
            background: {surf};
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 16px;
            padding: 0 8px;
            color: {ts};
        }}
        QLabel#logSectionTitle {{ color: {ts}; font-weight: 600; font-size: 10px; padding: 0; }}
        QPushButton#acStart[state="on"] {{
            background: rgba(34,197,94,0.15);
            border: 1px solid {ok};
            color: #86EFAC;
        }}
        QPushButton#acPause[state="paused"] {{
            background: rgba(245,158,11,0.12);
            border: 1px solid {warn};
            color: #FCD34D;
        }}
        QPushButton#acStop[state="danger"] {{
            background: rgba(239,68,68,0.12);
            border: 1px solid {err};
            color: #FCA5A5;
        }}
        QTextEdit#eventLog {{
            background: {T.D_BG_ELEVATED};
            border: 1px solid {b};
            border-radius: 8px;
            color: {tp};
            font-size: 11px;
            padding: 4px 8px;
        }}
        QListWidget {{
            background: {surf2};
            border: 1px solid {b};
            border-radius: 8px;
        }}
        QListWidget#macroFileList {{
            padding: 2px;
            border-radius: 6px;
        }}
        QCheckBox {{ spacing: 10px; color: {tp}; }}
        QCheckBox::indicator {{
            width: 18px;
            height: 18px;
            border: 1px solid {b};
            border-radius: 4px;
            background: {surf2};
        }}
        QCheckBox::indicator:checked {{
            border: none;
            background: transparent;
            image: url({chk_on});
        }}
        QCheckBox:disabled {{ color: {td}; }}
        QWidget#settingsTabRoot QCheckBox {{ spacing: 6px; }}
        QWidget#settingsTabRoot QLineEdit,
        QWidget#settingsTabRoot QSpinBox,
        QWidget#settingsTabRoot QDoubleSpinBox,
        QWidget#settingsTabRoot QComboBox {{
            min-height: 24px;
            border-radius: 6px;
        }}
        QWidget#settingsTabRoot QLineEdit {{
            padding: 0 4px;
        }}
        QWidget#settingsTabRoot QSpinBox,
        QWidget#settingsTabRoot QDoubleSpinBox {{
            padding: 4px 8px;
            padding-right: 26px;
        }}
        QWidget#settingsTabRoot QComboBox {{
            padding: 4px 8px;
            padding-right: 26px;
        }}
        QWidget#settingsTabRoot QComboBox::drop-down {{
            width: 26px;
        }}
        QWidget#settingsTabRoot QSpinBox::up-button, QWidget#settingsTabRoot QDoubleSpinBox::up-button {{
            width: 22px;
        }}
        QWidget#settingsTabRoot QSpinBox::down-button, QWidget#settingsTabRoot QDoubleSpinBox::down-button {{
            width: 22px;
        }}
        QWidget#settingsTabRoot QPushButton {{
            padding: 5px 10px;
            margin: 0px;
            min-height: 16px;
            border-radius: 6px;
        }}
        QWidget#settingsTabRoot QLabel#formInlineLabel {{
            font-size: 11px;
            padding: 0px 4px 0px 0px;
        }}
        """
    # Light
    bg = T.L_BG_APP
    surf = T.L_BG_SURFACE
    surf2 = T.L_BG_SURFACE2
    b = T.L_BORDER_SUBTLE
    bs = T.L_BORDER_STRONG
    bf = T.L_BORDER_FOCUS
    tp = T.L_TEXT_PRIMARY
    ts = T.L_TEXT_SECONDARY
    td = T.L_TEXT_DISABLED
    ac = T.L_ACCENT
    ach = T.L_ACCENT_HOVER
    err = T.D_STATE_ERROR
    ok = T.D_STATE_SUCCESS
    warn = T.D_STATE_WARNING
    sel_bg = T.L_SELECTION_BG
    sel_fg = T.L_SELECTION_FG
    return f"""
        QWidget {{ background-color: {bg}; color: {tp}; font-size: 13px; }}
        QMainWindow {{ background-color: {bg}; }}
        QWidget#headerBar {{
            background: {surf};
            border-bottom: 1px solid {b};
            min-height: 48px;
        }}
        QPushButton#headerNavButton {{
            background: transparent;
            border: none;
            border-radius: 6px;
            icon-size: 16px;
            padding: 6px 6px 8px 6px;
            margin: 0px 1px;
            font-size: 11px;
            font-weight: 500;
            color: {ts};
        }}
        QPushButton#headerNavButton:hover {{
            background: #F1F5F9;
            color: {tp};
        }}
        QPushButton#headerNavButton:checked {{
            background: {sel_bg};
            color: {ac};
            border-bottom: 3px solid {ac};
            padding: 6px 6px 5px 6px;
        }}
        QPushButton#headerActionButton {{
            padding: 4px 8px 5px 6px;
            font-size: 11px;
            font-weight: 500;
            border-radius: 8px;
            icon-size: 16px;
        }}
        QPushButton#acStart, QPushButton#acPause, QPushButton#acStop {{
            padding: 4px 8px 5px 6px;
            font-size: 11px;
            icon-size: 16px;
        }}
        QPushButton#macroSideButton {{
            text-align: left;
            padding: 4px 6px 5px 6px;
            font-size: 10px;
            icon-size: 16px;
        }}
        QLabel#headerTitle {{ color: {tp}; font-size: 15px; font-weight: 600; }}
        QWidget#appFooter {{
            background: {surf2};
            border-top: 1px solid #DC2626;
            min-height: 34px;
        }}
        QLabel#footerSecondary {{
            color: {ts};
            font-size: 11px;
        }}
        QLabel#footerStatusLabel {{
            color: {ts};
            font-size: 13px;
            font-weight: 500;
            padding: 4px 12px;
            border-radius: 6px;
            background: {surf};
        }}
        QLabel#footerStatusLabel[state="running"] {{ color: #15803D; background: #DCFCE7; }}
        QLabel#footerStatusLabel[state="paused"] {{ color: #B45309; background: #FEF3C7; }}
        QLabel#footerStatusLabel[state="macro"] {{ color: {ac}; background: {sel_bg}; }}
        QWidget#brandingPanel {{
            background: #F8FAFC;
        }}
        QFrame#sidebarVerticalDivider {{
            border: none;
            background: #DC2626;
            max-width: 2px;
            min-width: 2px;
        }}
        QLabel#sidebarCharacter {{
            background: #000000;
        }}
        QFrame#brandDivider {{
            border: none;
            background: #DC2626;
            max-height: 2px;
        }}
        QLabel#brandTitle {{
            color: #DC2626;
            font-size: 18px;
            font-weight: 700;
            letter-spacing: 0.02em;
        }}
        QLabel#brandProductSubtitle {{
            color: {tp};
            font-size: 12px;
            font-weight: 600;
            line-height: 1.3;
        }}
        QLabel#brandBlurb {{
            color: {ts};
            font-size: 11px;
            line-height: 1.45;
        }}
        QLabel#brandTagline {{
            color: {ts};
            font-size: 11px;
            line-height: 1.35;
        }}
        QLabel#brandAuthor {{
            color: {tp};
            font-size: 13px;
        }}
        QLabel#brandSectionTitle {{
            color: {td};
            font-size: 10px;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }}
        QLabel#brandFeaturesList {{
            color: {ts};
            font-size: 11px;
            line-height: 1.5;
        }}
        QLabel#brandHint {{
            color: {td};
            font-size: 10px;
            line-height: 1.45;
            font-style: italic;
        }}
        QFrame#brandInfoCard {{
            background: rgba(255, 255, 255, 0.85);
            border: 1px solid {b};
            border-radius: 10px;
        }}
        QLabel#brandLink {{
            font-size: 12px;
        }}
        QLabel#brandVersion {{
            color: {td};
            font-size: 11px;
            margin-top: 2px;
        }}
        QWidget#contentArea {{ background: {bg}; }}
        QScrollArea {{ border: none; background: transparent; }}
        QFrame#settingsSectionDivider {{
            border: none;
            background: {b};
            max-height: 1px;
            min-height: 1px;
        }}
        QFrame#contentCard {{
            background: {surf};
            border: 1px solid {b};
            border-radius: 8px;
        }}
        QLabel#sectionTitle {{
            color: {tp};
            font-size: 13px;
            font-weight: 700;
            margin: 0;
            padding: 0;
            background: transparent;
            border: none;
        }}
        QLabel#sectionTitleIcon {{
            min-width: 20px;
            min-height: 20px;
            background: transparent;
            border: none;
        }}
        QLabel#formFieldLabel {{
            color: {ts};
            font-size: 11px;
            font-weight: 600;
            padding: 3px 5px;
            background: {surf2};
            border: 1px solid {b};
            border-radius: 6px;
        }}
        QLabel#formHint {{
            color: {td};
            font-size: 11px;
            padding-top: 1px;
        }}
        QLabel#formInlineLabel {{
            color: {ts};
            font-size: 12px;
            font-weight: 500;
            padding: 4px 4px 4px 0;
        }}
        QLabel#settingsFieldLabel {{
            color: {ts};
            font-size: 10px;
            font-weight: 600;
            padding: 1px 4px;
            background: {surf2};
            border: 1px solid {b};
            border-radius: 4px;
        }}
        QLabel#settingsSectionTitle {{
            color: {tp};
            font-size: 12px;
            font-weight: 600;
            margin: 0;
            padding: 0;
        }}
        QStackedWidget#mainStack {{
            border: none;
            background: transparent;
        }}
        QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
            background: {surf};
            border: 1px solid {b};
            border-radius: 8px;
            min-height: 28px;
            color: {tp};
            selection-background-color: {sel_bg};
            selection-color: {sel_fg};
        }}
        QLineEdit {{
            padding: 6px 8px;
        }}
        QLineEdit:focus {{
            border: 1px solid {bf};
            background: {sel_bg};
        }}
        QSpinBox, QDoubleSpinBox {{
            padding: 5px 8px;
            padding-right: 30px;
        }}
        QSpinBox:focus, QDoubleSpinBox:focus {{
            border: 1px solid {bf};
            background: {sel_bg};
        }}
        QSpinBox::up-button, QDoubleSpinBox::up-button {{
            subcontrol-origin: border;
            subcontrol-position: top right;
            width: 28px;
            border-left: 1px solid {b};
            border-top-right-radius: 7px;
            background: {surf2};
        }}
        QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover {{
            background: #E2E8F0;
        }}
        QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {{
            image: url({spin_u_l});
            width: 12px;
            height: 8px;
            margin-right: 8px;
            margin-bottom: 2px;
        }}
        QSpinBox::down-button, QDoubleSpinBox::down-button {{
            subcontrol-origin: border;
            subcontrol-position: bottom right;
            width: 28px;
            border-left: 1px solid {b};
            border-bottom-right-radius: 7px;
            background: {surf2};
        }}
        QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {{
            background: #E2E8F0;
        }}
        QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {{
            image: url({spin_d_l});
            width: 12px;
            height: 8px;
            margin-right: 8px;
            margin-top: 2px;
        }}
        QComboBox {{
            padding: 5px 8px;
            padding-right: 30px;
        }}
        QComboBox:focus {{
            border: 1px solid {bf};
            background: {sel_bg};
        }}
        QComboBox::drop-down {{
            subcontrol-origin: padding;
            subcontrol-position: top right;
            width: 32px;
            border-left: 1px solid {b};
            border-top-right-radius: 7px;
            border-bottom-right-radius: 7px;
            background: {surf2};
        }}
        QComboBox::drop-down:hover {{
            background: #E2E8F0;
        }}
        QComboBox::down-arrow {{
            image: url({spin_d_l});
            width: 12px;
            height: 8px;
            margin-right: 10px;
        }}
        QComboBox QAbstractItemView {{
            background: {surf};
            border: 1px solid {b};
            selection-background-color: {sel_bg};
            selection-color: {sel_fg};
            padding: 4px;
        }}
        QPushButton {{
            background: {surf};
            border: 1px solid {b};
            padding: 7px 12px;
            border-radius: 8px;
            min-height: 18px;
            color: {tp};
        }}
        QPushButton:hover {{ background: {surf2}; border-color: {bs}; }}
        QPushButton:pressed {{ background: #E2E8F0; }}
        QPushButton:disabled {{ color: {td}; background: #F8FAFC; }}
        QTableWidget {{
            gridline-color: {b};
            border: 1px solid {b};
            border-radius: 8px;
            background: {surf};
            alternate-background-color: #F1F5F9;
        }}
        QTableWidget::item {{
            padding: 4px 6px;
        }}
        QTableWidget::item:selected {{
            background: {sel_bg};
            color: {tp};
        }}
        QTableWidget QLineEdit,
        QTableWidget QLineEdit:focus,
        QAbstractItemView QLineEdit,
        QAbstractItemView QLineEdit:focus {{
            background: {surf2};
            border: 1px solid {bf};
            border-radius: 4px;
            padding: 3px 6px;
            color: {tp};
            selection-background-color: {sel_bg};
            selection-color: {sel_fg};
        }}
        QHeaderView::section {{
            background: {surf2};
            padding: 6px 8px;
            border: none;
            border-right: 1px solid {b};
            border-bottom: 1px solid {b};
            color: {tp};
            font-weight: 600;
            font-size: 11px;
        }}
        QHeaderView::section:last {{
            border-right: none;
        }}
        QPushButton#seqRowButton {{
            padding: 5px 10px;
            font-size: 11px;
            font-weight: 500;
        }}
        QGroupBox {{
            border: 1px solid {b};
            border-radius: 8px;
            margin-top: 8px;
            font-weight: 600;
            padding-top: 16px;
            color: {tp};
            background: {surf};
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 16px;
            padding: 0 8px;
            color: {ts};
        }}
        QLabel#logSectionTitle {{ color: {ts}; font-weight: 600; font-size: 10px; padding: 0; }}
        QPushButton#acStart[state="on"] {{
            background: #DCFCE7;
            border: 1px solid {ok};
            color: #14532D;
        }}
        QPushButton#acPause[state="paused"] {{
            background: #FEF3C7;
            border: 1px solid {warn};
            color: #92400E;
        }}
        QPushButton#acStop[state="danger"] {{
            background: #FEE2E2;
            border: 1px solid {err};
            color: #B91C1C;
        }}
        QTextEdit#eventLog {{
            background: {surf2};
            border: 1px solid {b};
            border-radius: 8px;
            color: {tp};
            font-size: 11px;
            padding: 4px 8px;
        }}
        QListWidget {{
            background: {surf};
            border: 1px solid {b};
            border-radius: 8px;
        }}
        QListWidget#macroFileList {{
            padding: 2px;
            border-radius: 6px;
        }}
        QCheckBox {{ spacing: 10px; }}
        QCheckBox::indicator {{
            width: 18px;
            height: 18px;
            border: 1px solid {b};
            border-radius: 4px;
            background: {surf};
        }}
        QCheckBox::indicator:checked {{
            border: none;
            background: transparent;
            image: url({chk_on});
        }}
        QWidget#settingsTabRoot QCheckBox {{ spacing: 6px; }}
        QWidget#settingsTabRoot QLineEdit,
        QWidget#settingsTabRoot QSpinBox,
        QWidget#settingsTabRoot QDoubleSpinBox,
        QWidget#settingsTabRoot QComboBox {{
            min-height: 24px;
            border-radius: 6px;
        }}
        QWidget#settingsTabRoot QLineEdit {{
            padding: 0 4px;
        }}
        QWidget#settingsTabRoot QSpinBox,
        QWidget#settingsTabRoot QDoubleSpinBox {{
            padding: 4px 8px;
            padding-right: 26px;
        }}
        QWidget#settingsTabRoot QComboBox {{
            padding: 4px 8px;
            padding-right: 26px;
        }}
        QWidget#settingsTabRoot QComboBox::drop-down {{
            width: 26px;
        }}
        QWidget#settingsTabRoot QSpinBox::up-button, QWidget#settingsTabRoot QDoubleSpinBox::up-button {{
            width: 22px;
        }}
        QWidget#settingsTabRoot QSpinBox::down-button, QWidget#settingsTabRoot QDoubleSpinBox::down-button {{
            width: 22px;
        }}
        QWidget#settingsTabRoot QPushButton {{
            padding: 5px 10px;
            margin: 0px;
            min-height: 16px;
            border-radius: 6px;
        }}
        QWidget#settingsTabRoot QLabel#formInlineLabel {{
            font-size: 11px;
            padding: 0px 4px 0px 0px;
        }}
        """


def keyboard_styles(theme: ThemeMode) -> tuple[str, str]:
    """Щільні клавіші на єдиній темній підкладці."""
    if theme == ThemeMode.DARK:
        face = "#18181b"
        edge_t, edge_b = "#3f3f46", "#09090b"
        tc = "#fafafa"
        idle = (
            f"QLabel#kbdKey {{ border: none; border-radius: 4px; color: {tc}; font-size: 8px; font-weight: 500; "
            f"background: {face}; "
            f"border-top: 1px solid {edge_t}; border-left: 1px solid {edge_t}; "
            f"border-right: 1px solid {edge_b}; border-bottom: 1px solid #000; "
            f"min-width: 0px; min-height: 22px; padding: 1px 2px; }}"
        )
        active = (
            f"QLabel#kbdKey {{ border: none; border-radius: 4px; color: {T.D_ACCENT_HOVER}; font-size: 8px; font-weight: 600; "
            f"background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #27272a, stop:1 #18181b); "
            f"border-top: 1px solid {T.D_ACCENT}; border-left: 1px solid {T.D_ACCENT}; "
            f"border-right: 1px solid #312e81; border-bottom: 1px solid #1e1b4b; "
            f"min-width: 0px; min-height: 22px; padding: 1px 2px; }}"
        )
        return idle, active
    hi, lo = "#FFFFFF", "#E2E8F0"
    edge_t, edge_b = "#FFFFFF", "#94A3B8"
    tc = T.L_TEXT_SECONDARY
    idle = (
        f"QLabel#kbdKey {{ border: none; border-radius: 4px; color: {tc}; font-size: 8px; font-weight: 500; "
        f"background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 {hi}, stop:1 {lo}); "
        f"border-top: 1px solid {edge_t}; border-left: 1px solid {edge_t}; "
        f"border-right: 1px solid #CBD5E1; border-bottom: 1px solid {edge_b}; "
        f"min-width: 0px; min-height: 22px; padding: 1px 2px; }}"
    )
    active = (
        f"QLabel#kbdKey {{ border: none; border-radius: 4px; color: {T.L_ACCENT_ACTIVE}; font-size: 8px; font-weight: 600; "
        f"background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #EEF2FF, stop:1 #C7D2FE); "
        f"border-top: 1px solid {T.L_ACCENT}; border-left: 1px solid {T.L_ACCENT}; "
        f"border-right: 1px solid #A5B4FC; border-bottom: 1px solid #6366F1; "
        f"min-width: 0px; min-height: 22px; padding: 1px 2px; }}"
    )
    return idle, active


def keyboard_fn_key_style(theme: ThemeMode) -> str:
    """Клавіша Fn — синій текст."""
    if theme == ThemeMode.DARK:
        face = "#18181b"
        return (
            f"QLabel#kbdKeyFn {{ border: none; border-radius: 4px; color: #5886a6; font-size: 8px; font-weight: 600; "
            f"background: {face}; "
            f"border-top: 1px solid #3f3f46; border-left: 1px solid #3f3f46; "
            f"border-right: 1px solid #09090b; border-bottom: 1px solid #000; "
            f"min-width: 0px; min-height: 22px; padding: 1px 2px; }}"
        )
    return (
        f"QLabel#kbdKeyFn {{ border: none; border-radius: 4px; color: #2563EB; font-size: 8px; font-weight: 600; "
        f"background: #F8FAFC; border-top: 1px solid #fff; border-left: 1px solid #fff; "
        f"border-right: 1px solid #CBD5E1; border-bottom: 1px solid #94A3B8; "
        f"min-width: 0px; min-height: 22px; padding: 1px 2px; }}"
    )


def mouse_test_card_style(theme: ThemeMode) -> str:
    """Компактна картка «Миша»."""
    if theme == ThemeMode.DARK:
        return (
            f"QFrame#mouseTestCard {{ background: {T.D_BG_SURFACE}; border: 1px solid {T.D_BORDER_SUBTLE}; "
            f"border-radius: 10px; }}"
            f"QLabel#mouseTestTitle {{ color: {T.D_TEXT_PRIMARY}; font-size: 12px; font-weight: 600; }}"
            f"QLabel#mouseTestCoords {{ color: {T.D_ACCENT_HOVER}; font-size: 14px; font-weight: 600; "
            f"font-family: 'Cascadia Mono', 'Consolas', 'Courier New', monospace; padding: 2px 0 6px 0; }}"
            f"QLabel#mouseTestLbl {{ color: {T.D_TEXT_SECONDARY}; font-size: 10px; min-width: 36px; }}"
            f"QLabel#mouseTestScroll {{ color: {T.D_TEXT_PRIMARY}; font-size: 10px; }}"
        )
    return (
        f"QFrame#mouseTestCard {{ background: {T.L_BG_SURFACE}; border: 1px solid {T.L_BORDER_SUBTLE}; "
        f"border-radius: 10px; }}"
        f"QLabel#mouseTestTitle {{ color: {T.L_TEXT_PRIMARY}; font-size: 12px; font-weight: 600; }}"
        f"QLabel#mouseTestCoords {{ color: {T.L_ACCENT_ACTIVE}; font-size: 14px; font-weight: 600; "
        f"font-family: 'Cascadia Mono', 'Consolas', 'Courier New', monospace; padding: 2px 0 6px 0; }}"
        f"QLabel#mouseTestLbl {{ color: {T.L_TEXT_SECONDARY}; font-size: 10px; min-width: 36px; }}"
        f"QLabel#mouseTestScroll {{ color: {T.L_TEXT_PRIMARY}; font-size: 10px; }}"
    )


def mouse_test_pill_style(theme: ThemeMode, down: bool) -> str:
    """Стиль «пігулки» стану кнопки миші."""
    if theme == ThemeMode.DARK:
        if down:
            return (
                f"QLabel#mouseTestPill {{ border-radius: 4px; padding: 2px 6px; font-size: 10px; font-weight: 600; "
                f"background: rgba(99,102,241,0.22); color: {T.D_ACCENT_HOVER}; border: 1px solid {T.D_ACCENT}; }}"
            )
        return (
            f"QLabel#mouseTestPill {{ border-radius: 4px; padding: 2px 6px; font-size: 10px; font-weight: 500; "
            f"background: {T.D_BG_SURFACE2}; color: {T.D_TEXT_SECONDARY}; border: 1px solid {T.D_BORDER_SUBTLE}; }}"
        )
    if down:
        return (
            f"QLabel#mouseTestPill {{ border-radius: 4px; padding: 2px 6px; font-size: 10px; font-weight: 600; "
            f"background: {T.L_SELECTION_BG}; color: {T.L_ACCENT_ACTIVE}; border: 1px solid {T.L_ACCENT}; }}"
        )
    return (
        f"QLabel#mouseTestPill {{ border-radius: 4px; padding: 2px 6px; font-size: 10px; font-weight: 500; "
        f"background: {T.L_BG_SURFACE2}; color: {T.L_TEXT_SECONDARY}; border: 1px solid {T.L_BORDER_SUBTLE}; }}"
    )


def keyboard_frame_style(theme: ThemeMode) -> str:
    """Єдиний блок клавіатури + numpad без «сірої плями»."""
    if theme == ThemeMode.DARK:
        plate = "#27272a"
        b = "#3f3f46"
        tc = T.D_TEXT_SECONDARY
        return (
            f"QWidget#keyboardVisual {{ border: 1px solid {b}; border-radius: 8px; background: {plate}; "
            f"padding: 0px; }} "
            f"QGroupBox#kbdNumpadGroup {{ color: {tc}; font-size: 8px; font-weight: 600; border: none; "
            f"border-left: 1px solid {b}; border-radius: 0px; margin-top: 0px; padding-top: 4px; padding-left: 4px; "
            f"background: transparent; }}"
            f"QGroupBox#kbdNumpadGroup::title {{ subcontrol-origin: margin; left: 2px; padding: 0 4px; color: {tc}; }}"
        )
    b = T.L_BORDER_SUBTLE
    plate, tc = "#f1f5f9", T.L_TEXT_SECONDARY
    return (
        f"QWidget#keyboardVisual {{ border: 1px solid {b}; border-radius: 8px; background: {plate}; padding: 0px; }} "
        f"QGroupBox#kbdNumpadGroup {{ color: {tc}; font-size: 8px; font-weight: 600; border: none; "
        f"border-left: 1px solid {b}; border-radius: 0px; margin-top: 0px; padding-top: 4px; padding-left: 4px; "
        f"background: transparent; }}"
        f"QGroupBox#kbdNumpadGroup::title {{ subcontrol-origin: margin; left: 2px; padding: 0 4px; color: {tc}; }}"
    )
