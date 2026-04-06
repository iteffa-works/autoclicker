"""Light/dark QSS from design_tokens (slate + indigo)."""

from __future__ import annotations

import base64

from app.models.settings import ThemeMode
from app.ui import design_tokens as T


def _svg_check_data_url(stroke: str) -> str:
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16">'
        f'<path fill="none" stroke="{stroke}" stroke-width="2.2" stroke-linecap="round" '
        f'stroke-linejoin="round" d="M3.5 8.2l2.8 2.8 6.2-7.5"/></svg>'
    )
    b = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return f"data:image/svg+xml;base64,{b}"


def stylesheet_for(theme: ThemeMode) -> str:
    chk_d = _svg_check_data_url(T.D_ACCENT_HOVER)
    chk_l = _svg_check_data_url(T.L_ACCENT)
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
            padding: 6px 10px 8px 10px;
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
            padding: 6px 10px 5px 10px;
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
            font-weight: 600;
            margin: 0;
            padding: 0;
        }}
        QLabel#sectionTitleIcon {{
            min-width: 20px;
            min-height: 20px;
            background: transparent;
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
            width: 0;
            height: 0;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-bottom: 6px solid #94A3B8;
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
            width: 0;
            height: 0;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top: 6px solid #94A3B8;
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
            width: 0;
            height: 0;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 6px solid #94A3B8;
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
        QCheckBox {{ spacing: 10px; color: {tp}; }}
        QCheckBox::indicator {{
            width: 18px;
            height: 18px;
            border: 1px solid {b};
            border-radius: 4px;
            background: {surf2};
        }}
        QCheckBox::indicator:checked {{
            background: rgba(99,102,241,0.2);
            border: 1px solid {ac};
            image: url({chk_d});
        }}
        QCheckBox:disabled {{ color: {td}; }}
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
            padding: 6px 10px 8px 10px;
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
            padding: 6px 10px 5px 10px;
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
            font-weight: 600;
            margin: 0;
            padding: 0;
        }}
        QLabel#sectionTitleIcon {{
            min-width: 20px;
            min-height: 20px;
            background: transparent;
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
            width: 0;
            height: 0;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-bottom: 6px solid #64748B;
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
            width: 0;
            height: 0;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top: 6px solid #64748B;
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
            width: 0;
            height: 0;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 6px solid #64748B;
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
        QCheckBox {{ spacing: 10px; }}
        QCheckBox::indicator {{
            width: 18px;
            height: 18px;
            border: 1px solid {b};
            border-radius: 4px;
            background: {surf};
        }}
        QCheckBox::indicator:checked {{
            background: {sel_bg};
            border: 1px solid {ac};
            image: url({chk_l});
        }}
        """


def keyboard_styles(theme: ThemeMode) -> tuple[str, str]:
    """idle, active key QLabel#kbdKey stylesheets."""
    if theme == ThemeMode.DARK:
        b, bg = T.D_BORDER_SUBTLE, T.D_BG_SURFACE2
        tc = T.D_TEXT_SECONDARY
        idle = (
            f"QLabel#kbdKey {{ border: 1px solid {b}; border-radius: 6px; background: {bg}; "
            f"min-width: 28px; min-height: 32px; color: {tc}; font-size: 11px; }}"
        )
        active = (
            f"QLabel#kbdKey {{ border: 2px solid {T.D_ACCENT}; border-radius: 6px; background: rgba(99,102,241,0.15); "
            f"color: {T.D_ACCENT_HOVER}; min-width: 28px; min-height: 32px; font-weight: 600; }}"
        )
        return idle, active
    b, bg = T.L_BORDER_SUBTLE, T.L_BG_SURFACE
    tc = T.L_TEXT_SECONDARY
    idle = (
        f"QLabel#kbdKey {{ border: 1px solid {b}; border-radius: 6px; background: {bg}; "
        f"min-width: 28px; min-height: 32px; color: {tc}; font-size: 11px; }}"
    )
    active = (
        f"QLabel#kbdKey {{ border: 2px solid {T.L_ACCENT}; border-radius: 6px; background: {T.L_SELECTION_BG}; "
        f"color: {T.L_ACCENT_ACTIVE}; min-width: 28px; min-height: 32px; font-weight: 600; }}"
    )
    return idle, active


def keyboard_frame_style(theme: ThemeMode) -> str:
    """Рамка навколо візуальної клавіатури."""
    if theme == ThemeMode.DARK:
        b, bg = T.D_BORDER_SUBTLE, T.D_BG_ELEVATED
        return f"QWidget#keyboardVisual {{ border: 1px solid {b}; border-radius: 12px; background: {bg}; }}"
    b, bg = T.L_BORDER_SUBTLE, T.L_BG_SURFACE2
    return f"QWidget#keyboardVisual {{ border: 1px solid {b}; border-radius: 12px; background: {bg}; }}"
