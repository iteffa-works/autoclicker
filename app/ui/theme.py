"""Light/dark QSS from design_tokens (slate + indigo)."""

from __future__ import annotations

import base64

from PySide6.QtCore import QByteArray, QBuffer, QIODevice

from app.models.settings import ThemeMode
from app.ui import design_tokens as T


def _pixmap_to_data_url(pm) -> str:
    """PNG → data:image/png;base64,... для QSS."""
    ba = QByteArray()
    buf = QBuffer(ba)
    buf.open(QIODevice.OpenModeFlag.WriteOnly)
    try:
        if not pm.save(buf, "PNG"):
            return ""
    finally:
        buf.close()
    return _check_indicator_data_url(base64.b64encode(ba.data()).decode("ascii"))


def _checkbox_checked_image_urls(theme: ThemeMode) -> dict[str, str]:
    from app.ui.app_icons import checkbox_checked_state_pixmaps

    return {k: _pixmap_to_data_url(v) for k, v in checkbox_checked_state_pixmaps(theme).items()}


def _qcheckbox_stylesheet(theme: ThemeMode) -> str:
    """QCheckBox: усі стани індикатора; галочка — растр (image: url)."""
    u = _checkbox_checked_image_urls(theme)
    c = u["checked"]
    ch = u["checked_hover"]
    cp = u["checked_pressed"]
    cd = u["checked_disabled"]
    if theme == ThemeMode.DARK:
        tp, td = T.D_TEXT_PRIMARY, T.D_TEXT_DISABLED
        b, surf2 = T.D_BORDER_SUBTLE, T.D_BG_SURFACE2
        return f"""
        QCheckBox {{ spacing: 10px; color: {tp}; }}
        QCheckBox::indicator {{
            width: 18px;
            height: 18px;
            border: 1px solid {b};
            border-radius: 5px;
            background: {surf2};
        }}
        QCheckBox::indicator:hover {{
            background: #334155;
            border: 1px solid #475569;
        }}
        QCheckBox::indicator:pressed {{
            background: #1e293b;
            border: 1px solid {b};
        }}
        QCheckBox::indicator:checked {{
            width: 18px;
            height: 18px;
            border: none;
            background: transparent;
            image: url("{c}");
        }}
        QCheckBox::indicator:checked:hover {{
            image: url("{ch}");
        }}
        QCheckBox::indicator:checked:pressed {{
            image: url("{cp}");
        }}
        QCheckBox::indicator:disabled {{
            background: #293548;
            border: 1px solid #475569;
        }}
        QCheckBox::indicator:checked:disabled {{
            border: none;
            background: transparent;
            image: url("{cd}");
        }}
        QCheckBox:disabled {{ color: {td}; }}
        QWidget#settingsTabRoot QCheckBox {{ spacing: 3px; }}
        """
    tp, td = T.L_TEXT_PRIMARY, T.L_TEXT_DISABLED
    b, surf = T.L_BORDER_SUBTLE, T.L_BG_SURFACE
    return f"""
        QCheckBox {{ spacing: 10px; color: {tp}; }}
        QCheckBox::indicator {{
            width: 18px;
            height: 18px;
            border: 1px solid {b};
            border-radius: 5px;
            background: {surf};
        }}
        QCheckBox::indicator:hover {{
            background: #F1F5F9;
            border: 1px solid #CBD5E1;
        }}
        QCheckBox::indicator:pressed {{
            background: #E2E8F0;
            border: 1px solid {b};
        }}
        QCheckBox::indicator:checked {{
            width: 18px;
            height: 18px;
            border: none;
            background: transparent;
            image: url("{c}");
        }}
        QCheckBox::indicator:checked:hover {{
            image: url("{ch}");
        }}
        QCheckBox::indicator:checked:pressed {{
            image: url("{cp}");
        }}
        QCheckBox::indicator:disabled {{
            background: #F1F5F9;
            border: 1px solid #E2E8F0;
        }}
        QCheckBox::indicator:checked:disabled {{
            border: none;
            background: transparent;
            image: url("{cd}");
        }}
        QCheckBox:disabled {{ color: {td}; }}
        QWidget#settingsTabRoot QCheckBox {{ spacing: 3px; }}
        """


# QSpinBox/QComboBox: border-трикутники (width:0) на Windows часто стають квадратами — PNG у image:.
_SPIN_UP_DARK = "iVBORw0KGgoAAAANSUhEUgAAAAwAAAAICAYAAADN5B7xAAAAL0lEQVR4nGNgGDAwZfGO/9jEmfApxqYJQwO6InQ+VhvwARQNuNyNLA7XgEsxujwAGf4aaYb1sjsAAAAASUVORK5CYII="
_SPIN_DOWN_DARK = "iVBORw0KGgoAAAANSUhEUgAAAAwAAAAICAYAAADN5B7xAAAAOUlEQVR4nGNgIBEwwhhTFu/4T0hxTqwHIxMyh5BiBgYGBrgGfJqQxVE0EAMwNKDbQsipcEBMIBAFAPzrDWSBzvGzAAAAAElFTkSuQmCC"
_SPIN_UP_LIGHT = "iVBORw0KGgoAAAANSUhEUgAAAAwAAAAICAYAAADN5B7xAAAAL0lEQVR4nGNgGDCQUtL9H5s4Ez7F2DRhaEBXhM7HagM+gKIBl7uRxeEacClGlwcAdcYVfaJFF3sAAAAASUVORK5CYII="
_SPIN_DOWN_LIGHT = "iVBORw0KGgoAAAANSUhEUgAAAAwAAAAICAYAAADN5B7xAAAAOUlEQVR4nGNgIBEwwhgpJd3/CSme01PKyITMIaSYgYGBAa4BnyZkcRQNxAAMDei2EHIqHBATCEQBAFsXECDnr5qNAAAAAElFTkSuQmCC"


def _check_indicator_data_url(png_b64: str) -> str:
    return f"data:image/png;base64,{png_b64}"


def _settings_tab_controls_qss(
    *,
    border: str,
    drop_bg: str,
    drop_hover_bg: str,
    spin_up_url: str,
    spin_down_url: str,
) -> str:
    return f"""
        QWidget#settingsTabRoot QLineEdit,
        QWidget#settingsTabRoot QSpinBox,
        QWidget#settingsTabRoot QDoubleSpinBox,
        QWidget#settingsTabRoot QComboBox {{
            min-height: 30px;
            max-height: 32px;
            border-radius: 5px;
        }}
        QWidget#settingsTabRoot QLineEdit {{
            padding: 2px 6px;
        }}
        QWidget#settingsTabRoot QSpinBox,
        QWidget#settingsTabRoot QDoubleSpinBox {{
            padding: 2px 6px;
            padding-right: 28px;
        }}
        QWidget#settingsTabRoot QComboBox {{
            padding: 2px 6px;
            padding-right: 28px;
        }}
        QWidget#settingsTabRoot QComboBox::drop-down {{
            subcontrol-origin: padding;
            subcontrol-position: top right;
            width: 26px;
            border-left: 1px solid {border};
            border-top-right-radius: 5px;
            border-bottom-right-radius: 5px;
            background: {drop_bg};
            image: url("{spin_down_url}");
        }}
        QWidget#settingsTabRoot QComboBox::drop-down:hover {{
            background: {drop_hover_bg};
        }}
        QWidget#settingsTabRoot QComboBox::down-arrow {{
            image: url("{spin_down_url}");
            width: 12px;
            height: 8px;
            margin-right: 6px;
        }}
        QWidget#settingsTabRoot QSpinBox::up-button, QWidget#settingsTabRoot QDoubleSpinBox::up-button {{
            subcontrol-origin: border;
            subcontrol-position: top right;
            width: 22px;
            border-left: 1px solid {border};
            border-top-right-radius: 5px;
            background: {drop_bg};
            image: url("{spin_up_url}");
        }}
        QWidget#settingsTabRoot QSpinBox::up-button:hover, QWidget#settingsTabRoot QDoubleSpinBox::up-button:hover {{
            background: {drop_hover_bg};
        }}
        QWidget#settingsTabRoot QSpinBox::down-button, QWidget#settingsTabRoot QDoubleSpinBox::down-button {{
            subcontrol-origin: border;
            subcontrol-position: bottom right;
            width: 22px;
            border-left: 1px solid {border};
            border-bottom-right-radius: 5px;
            background: {drop_bg};
            image: url("{spin_down_url}");
        }}
        QWidget#settingsTabRoot QSpinBox::down-button:hover, QWidget#settingsTabRoot QDoubleSpinBox::down-button:hover {{
            background: {drop_hover_bg};
        }}
        QWidget#settingsTabRoot QSpinBox::up-arrow, QWidget#settingsTabRoot QDoubleSpinBox::up-arrow {{
            image: url("{spin_up_url}");
            width: 12px;
            height: 8px;
            margin-right: 5px;
            margin-bottom: 1px;
        }}
        QWidget#settingsTabRoot QSpinBox::down-arrow, QWidget#settingsTabRoot QDoubleSpinBox::down-arrow {{
            image: url("{spin_down_url}");
            width: 12px;
            height: 8px;
            margin-right: 5px;
            margin-top: 1px;
        }}
        QWidget#settingsTabRoot QPushButton {{
            padding: 3px 8px;
            margin: 0px;
            min-height: 16px;
            border-radius: 5px;
        }}
        QWidget#settingsTabRoot QLabel#formInlineLabel {{
            font-size: 11px;
            padding: 0px 2px 0px 0px;
        }}
    """


def stylesheet_for(theme: ThemeMode) -> str:
    qcb = _qcheckbox_stylesheet(theme)
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
        settings_form_qss = _settings_tab_controls_qss(
            border=b,
            drop_bg="#111827",
            drop_hover_bg="#334155",
            spin_up_url=spin_u_d,
            spin_down_url=spin_d_d,
        )
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
        QPushButton#headerPrimaryButton {{
            padding: 4px 10px 5px 8px;
            font-size: 11px;
            font-weight: 600;
            border-radius: 8px;
            icon-size: 16px;
            background: {ac};
            color: #F8FAFC;
            border: 1px solid {ac};
        }}
        QPushButton#headerPrimaryButton:hover {{
            background: {ach};
            border-color: {ach};
            color: #F8FAFC;
        }}
        QPushButton#headerPrimaryButton:pressed {{
            background: {aca};
            border-color: {aca};
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
            background: {bg};
            border-top: 1px solid rgba(148, 163, 184, 0.22);
            min-height: 44px;
        }}
        QLabel#footerSecondary {{
            color: {ts};
            font-size: 12px;
            font-weight: 600;
            letter-spacing: 0.03em;
            background: transparent;
            padding: 4px 0px;
        }}
        QLabel#footerStatusLabel {{
            color: {ts};
            font-size: 12px;
            font-weight: 500;
            padding: 5px 14px;
            border-radius: 8px;
            border: 1px solid rgba(148, 163, 184, 0.22);
            background: rgba(30, 41, 59, 0.55);
        }}
        QLabel#footerStatusLabel[state="idle"] {{
            color: {td};
            border: 1px solid rgba(148, 163, 184, 0.18);
            background: rgba(30, 41, 59, 0.4);
        }}
        QLabel#footerStatusLabel[state="running"] {{
            color: {ok};
            border: 1px solid rgba(34, 197, 94, 0.35);
            background: rgba(34, 197, 94, 0.1);
        }}
        QLabel#footerStatusLabel[state="paused"] {{
            color: {warn};
            border: 1px solid rgba(245, 158, 11, 0.35);
            background: rgba(245, 158, 11, 0.1);
        }}
        QLabel#footerStatusLabel[state="macro"] {{
            color: {ach};
            border: 1px solid rgba(99, 102, 241, 0.35);
            background: rgba(99, 102, 241, 0.12);
        }}
        QWidget#brandingPanel {{
            background: {bg};
        }}
        QFrame#sidebarVerticalDivider {{
            border: none;
            background: rgba(99, 102, 241, 0.45);
            max-width: 2px;
            min-width: 2px;
        }}
        QLabel#sidebarCharacter {{
            background: #000000;
        }}
        QFrame#brandDivider {{
            border: none;
            background: rgba(99, 102, 241, 0.4);
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
        QWidget#brandSocialRow {{
            background: transparent;
        }}
        QToolButton#brandSocialButton {{
            background: rgba(30, 41, 59, 0.9);
            border: 1px solid rgba(148, 163, 184, 0.22);
            border-radius: 22px;
            min-width: 44px;
            min-height: 44px;
            padding: 0px;
        }}
        QToolButton#brandSocialButton:hover {{
            background: rgba(51, 65, 85, 0.95);
            border: 1px solid rgba(148, 163, 184, 0.38);
        }}
        QToolButton#brandSocialButton:pressed {{
            background: rgba(15, 23, 42, 0.95);
        }}
        QLabel#brandVersion {{
            color: {td};
            font-size: 11px;
            margin-top: 2px;
        }}
        QWidget#contentArea {{ background: {bg}; }}
        QScrollArea {{ border: none; background: transparent; }}
        QScrollArea > QWidget > QWidget {{ background: transparent; }}
        QFrame#settingsCard {{
            background: rgba(30, 41, 59, 0.42);
            border: 1px solid rgba(51, 65, 85, 0.55);
            border-radius: 6px;
        }}
        QLabel#settingsCardTitle {{
            color: {ts};
            font-size: 10px;
            font-weight: 600;
            letter-spacing: 0.07em;
            text-transform: uppercase;
            margin: 0 0 2px 0;
            padding: 0;
            background: transparent;
            border: none;
        }}
        QLabel#settingsFormLabel {{
            color: {ts};
            font-size: 11px;
            font-weight: 500;
            margin: 0;
            padding: 0px 6px 0px 0;
            background: transparent;
            border: none;
        }}
        QFrame#bindHotkeyRow {{
            background: transparent;
            border: none;
            border-radius: 5px;
            padding: 2px 4px;
        }}
        QFrame#bindHotkeyRow:hover {{
            background: rgba(148, 163, 184, 0.1);
        }}
        QLabel#bindHotkeyActionLabel {{
            color: {ts};
            font-size: 11px;
            font-weight: 500;
            background: transparent;
            border: none;
        }}
        QPushButton#bindHotkeyRowButton {{
            min-height: 30px;
            max-height: 32px;
            padding: 3px 8px;
            font-size: 11px;
            font-weight: 500;
            border-radius: 5px;
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
            font-weight: 500;
            padding: 2px 2px 2px 0;
            background: transparent;
            border: none;
        }}
        QLabel#formHint {{
            color: {td};
            font-size: 11px;
            padding-top: 1px;
        }}
        QLabel#formInlineLabel {{
            color: {ts};
            font-size: 12px;
            font-weight: 400;
            padding: 2px 4px 2px 0;
        }}
        QLabel#settingsFieldLabel {{
            color: {ts};
            font-size: 10px;
            font-weight: 500;
            padding: 1px 2px 1px 0;
            background: transparent;
            border: none;
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
            image: url("{spin_u_d}");
        }}
        QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover {{
            background: #334155;
        }}
        QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {{
            image: url("{spin_u_d}");
            width: 12px;
            height: 8px;
            margin-right: 8px;
            margin-bottom: 1px;
        }}
        QSpinBox::down-button, QDoubleSpinBox::down-button {{
            subcontrol-origin: border;
            subcontrol-position: bottom right;
            width: 28px;
            border-left: 1px solid {b};
            border-bottom-right-radius: 7px;
            background: #111827;
            image: url("{spin_d_d}");
        }}
        QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {{
            background: #334155;
        }}
        QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {{
            image: url("{spin_d_d}");
            width: 12px;
            height: 8px;
            margin-right: 8px;
            margin-top: 1px;
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
            image: url("{spin_d_d}");
        }}
        QComboBox::drop-down:hover {{
            background: #334155;
        }}
        QComboBox::down-arrow {{
            image: url("{spin_d_d}");
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
        {qcb}
        {settings_form_qss}
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
    aca = T.L_ACCENT_ACTIVE
    err = T.D_STATE_ERROR
    ok = T.D_STATE_SUCCESS
    warn = T.D_STATE_WARNING
    sel_bg = T.L_SELECTION_BG
    sel_fg = T.L_SELECTION_FG
    settings_form_qss = _settings_tab_controls_qss(
        border=b,
        drop_bg=surf2,
        drop_hover_bg="#E2E8F0",
        spin_up_url=spin_u_l,
        spin_down_url=spin_d_l,
    )
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
        QPushButton#headerPrimaryButton {{
            padding: 4px 10px 5px 8px;
            font-size: 11px;
            font-weight: 600;
            border-radius: 8px;
            icon-size: 16px;
            background: {ac};
            color: #F8FAFC;
            border: 1px solid {ac};
        }}
        QPushButton#headerPrimaryButton:hover {{
            background: {ach};
            border-color: {ach};
            color: #F8FAFC;
        }}
        QPushButton#headerPrimaryButton:pressed {{
            background: {aca};
            border-color: {aca};
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
            background: {bg};
            border-top: 1px solid rgba(100, 116, 139, 0.25);
            min-height: 44px;
        }}
        QLabel#footerSecondary {{
            color: {ts};
            font-size: 12px;
            font-weight: 600;
            letter-spacing: 0.03em;
            background: transparent;
            padding: 4px 0px;
        }}
        QLabel#footerStatusLabel {{
            color: {ts};
            font-size: 12px;
            font-weight: 500;
            padding: 5px 14px;
            border-radius: 8px;
            border: 1px solid {b};
            background: {surf};
        }}
        QLabel#footerStatusLabel[state="idle"] {{
            color: {td};
            background: {surf2};
        }}
        QLabel#footerStatusLabel[state="running"] {{
            color: #15803D;
            border: 1px solid #86EFAC;
            background: #DCFCE7;
        }}
        QLabel#footerStatusLabel[state="paused"] {{
            color: #B45309;
            border: 1px solid #FCD34D;
            background: #FEF3C7;
        }}
        QLabel#footerStatusLabel[state="macro"] {{
            color: {ac};
            border: 1px solid #C7D2FE;
            background: {sel_bg};
        }}
        QWidget#brandingPanel {{
            background: {bg};
        }}
        QFrame#sidebarVerticalDivider {{
            border: none;
            background: rgba(99, 102, 241, 0.35);
            max-width: 2px;
            min-width: 2px;
        }}
        QLabel#sidebarCharacter {{
            background: #000000;
        }}
        QFrame#brandDivider {{
            border: none;
            background: rgba(99, 102, 241, 0.35);
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
        QWidget#brandSocialRow {{
            background: transparent;
        }}
        QToolButton#brandSocialButton {{
            background: {surf};
            border: 1px solid {b};
            border-radius: 22px;
            min-width: 44px;
            min-height: 44px;
            padding: 0px;
        }}
        QToolButton#brandSocialButton:hover {{
            background: #F1F5F9;
            border: 1px solid #CBD5E1;
        }}
        QToolButton#brandSocialButton:pressed {{
            background: #E2E8F0;
        }}
        QLabel#brandVersion {{
            color: {td};
            font-size: 11px;
            margin-top: 2px;
        }}
        QWidget#contentArea {{ background: {bg}; }}
        QScrollArea {{ border: none; background: transparent; }}
        QFrame#settingsCard {{
            background: rgba(255, 255, 255, 0.58);
            border: 1px solid rgba(226, 232, 240, 0.85);
            border-radius: 6px;
        }}
        QLabel#settingsCardTitle {{
            color: {ts};
            font-size: 10px;
            font-weight: 600;
            letter-spacing: 0.07em;
            text-transform: uppercase;
            margin: 0 0 2px 0;
            padding: 0;
            background: transparent;
            border: none;
        }}
        QLabel#settingsFormLabel {{
            color: {ts};
            font-size: 11px;
            font-weight: 500;
            margin: 0;
            padding: 0px 6px 0px 0;
            background: transparent;
            border: none;
        }}
        QFrame#bindHotkeyRow {{
            background: transparent;
            border: none;
            border-radius: 5px;
            padding: 2px 4px;
        }}
        QFrame#bindHotkeyRow:hover {{
            background: rgba(15, 23, 42, 0.05);
        }}
        QLabel#bindHotkeyActionLabel {{
            color: {ts};
            font-size: 11px;
            font-weight: 500;
            background: transparent;
            border: none;
        }}
        QPushButton#bindHotkeyRowButton {{
            min-height: 30px;
            max-height: 32px;
            padding: 3px 8px;
            font-size: 11px;
            font-weight: 500;
            border-radius: 5px;
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
            font-weight: 500;
            padding: 2px 2px 2px 0;
            background: transparent;
            border: none;
        }}
        QLabel#formHint {{
            color: {td};
            font-size: 11px;
            padding-top: 1px;
        }}
        QLabel#formInlineLabel {{
            color: {ts};
            font-size: 12px;
            font-weight: 400;
            padding: 2px 4px 2px 0;
        }}
        QLabel#settingsFieldLabel {{
            color: {ts};
            font-size: 10px;
            font-weight: 500;
            padding: 1px 2px 1px 0;
            background: transparent;
            border: none;
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
            image: url("{spin_u_l}");
        }}
        QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover {{
            background: #E2E8F0;
        }}
        QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {{
            image: url("{spin_u_l}");
            width: 12px;
            height: 8px;
            margin-right: 8px;
            margin-bottom: 1px;
        }}
        QSpinBox::down-button, QDoubleSpinBox::down-button {{
            subcontrol-origin: border;
            subcontrol-position: bottom right;
            width: 28px;
            border-left: 1px solid {b};
            border-bottom-right-radius: 7px;
            background: {surf2};
            image: url("{spin_d_l}");
        }}
        QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {{
            background: #E2E8F0;
        }}
        QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {{
            image: url("{spin_d_l}");
            width: 12px;
            height: 8px;
            margin-right: 8px;
            margin-top: 1px;
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
            image: url("{spin_d_l}");
        }}
        QComboBox::drop-down:hover {{
            background: #E2E8F0;
        }}
        QComboBox::down-arrow {{
            image: url("{spin_d_l}");
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
        {qcb}
        {settings_form_qss}
        """


class KeyboardKeycapStyles:
    """Стилі капа клавіатури тесту: idle / hover / active × звичайна та Fn."""

    __slots__ = ("idle", "hover", "active", "fn_idle", "fn_hover", "fn_active")

    def __init__(
        self,
        idle: str,
        hover: str,
        active: str,
        fn_idle: str,
        fn_hover: str,
        fn_active: str,
    ) -> None:
        self.idle = idle
        self.hover = hover
        self.active = active
        self.fn_idle = fn_idle
        self.fn_hover = fn_hover
        self.fn_active = fn_active


def keyboard_keycap_styles(theme: ThemeMode) -> KeyboardKeycapStyles:
    """Клавіші тесту: одна система для всіх клавіш (основний блок + numpad + Fn)."""
    ff = '"Segoe UI", "Inter", sans-serif'
    r = "8px"
    fs = "13px"
    if theme == ThemeMode.DARK:
        kf, kh, kbd = T.KB_TEST_KEY_FACE, T.KB_TEST_KEY_FACE_HOVER, T.KB_TEST_KEY_BORDER
        kpress = T.KB_TEST_KEY_FACE_ACTIVE
        tc = T.D_TEXT_PRIMARY
        ac, acs = T.KB_TEST_ACCENT, T.KB_TEST_ACCENT_SOFT
        base = (
            f"QFrame#keyCap {{ background-color: {kf}; border: 1px solid {kbd}; border-radius: {r}; }}"
            f"QFrame#keyCap QLabel#keyCapLabel {{ color: {tc}; font-size: {fs}; font-weight: 500; font-family: {ff}; "
            f"background: transparent; border: none; padding: 1px 2px; }}"
        )
        hover = (
            f"QFrame#keyCap {{ background-color: {kh}; border: 1px solid {kbd}; border-radius: {r}; }}"
            f"QFrame#keyCap QLabel#keyCapLabel {{ color: {tc}; font-size: {fs}; font-weight: 500; font-family: {ff}; "
            f"background: transparent; border: none; padding: 1px 2px; }}"
        )
        active = (
            f"QFrame#keyCap {{ background-color: {kpress}; border: 1px solid {ac}; border-radius: {r}; }}"
            f"QFrame#keyCap QLabel#keyCapLabel {{ color: #F8FAFC; font-size: {fs}; font-weight: 600; font-family: {ff}; "
            f"background: transparent; border: none; padding: 1px 2px; }}"
        )
        return KeyboardKeycapStyles(base, hover, active, base, hover, active)
    kf, kh, kbd = T.L_KB_TEST_KEY_FACE, T.L_KB_TEST_KEY_FACE_HOVER, T.L_KB_TEST_KEY_BORDER
    kpress = T.L_KB_TEST_KEY_FACE_ACTIVE
    tc, tac = T.L_TEXT_PRIMARY, T.L_KB_TEST_ACCENT
    acs = T.L_KB_TEST_ACCENT_SOFT
    base = (
        f"QFrame#keyCap {{ background-color: {kf}; border: 1px solid {kbd}; border-radius: {r}; }}"
        f"QFrame#keyCap QLabel#keyCapLabel {{ color: {tc}; font-size: {fs}; font-weight: 500; font-family: {ff}; "
        f"background: transparent; border: none; padding: 1px 2px; }}"
    )
    hover = (
        f"QFrame#keyCap {{ background-color: {kh}; border: 1px solid {kbd}; border-radius: {r}; }}"
        f"QFrame#keyCap QLabel#keyCapLabel {{ color: {tc}; font-size: {fs}; font-weight: 500; font-family: {ff}; "
        f"background: transparent; border: none; padding: 1px 2px; }}"
    )
    active = (
        f"QFrame#keyCap {{ background-color: {kpress}; border: 1px solid {tac}; border-radius: {r}; }}"
        f"QFrame#keyCap QLabel#keyCapLabel {{ color: {T.L_TEXT_PRIMARY}; font-size: {fs}; font-weight: 600; font-family: {ff}; "
        f"background: transparent; border: none; padding: 1px 2px; }}"
    )
    return KeyboardKeycapStyles(base, hover, active, base, hover, active)


def mouse_test_panel_styles(theme: ThemeMode) -> str:
    """Діагностичні картки: миша, координати, скрол (єдина система)."""
    mono = "'Cascadia Mono', 'Consolas', 'Courier New', monospace"
    if theme == ThemeMode.DARK:
        card = T.D_BG_SURFACE
        inner = T.D_BG_ELEVATED
        b = T.D_BORDER_SUBTLE
        hb = "rgba(51, 65, 85, 0.55)"
        tp, ts = T.D_TEXT_PRIMARY, T.D_TEXT_SECONDARY
        ac = T.KB_TEST_ACCENT
        return (
            f"QFrame#kbTestCard {{ background-color: {card}; border: 1px solid {b}; border-radius: 12px; padding: 0px; }}"
            f"QWidget#kbDiagHeader {{ background-color: transparent; border: none; "
            f"border-bottom: 1px solid {hb}; }}"
            f"QLabel#kbDiagHeaderIcon {{ background-color: transparent; border: none; }}"
            f"QLabel#kbDiagTitle {{ color: {tp}; background-color: transparent; border: none; "
            f"font-size: 13px; font-weight: 600; padding: 0px; }}"
            f"QWidget#kbDiagBody {{ background-color: transparent; }}"
            f"QFrame#mouseDiagCell {{ background-color: {inner}; border: 1px solid {b}; border-radius: 8px; }}"
            f"QFrame#mouseMetricBox {{ background-color: {inner}; border: 1px solid {b}; border-radius: 8px; }}"
            f"QLabel#mouseDiagKeyLbl {{ color: {ts}; background-color: transparent; border: none; "
            f"font-size: 11px; font-weight: 600; letter-spacing: 0.02em; }}"
            f"QLabel#mouseMetricDimLbl {{ color: {ts}; background-color: transparent; border: none; "
            f"font-size: 11px; font-weight: 500; }}"
            f"QLabel#mouseMetricValueCoords {{ color: {ac}; background-color: transparent; border: none; "
            f"font-size: 18px; font-weight: 600; font-family: {mono}; padding: 2px 0px 0px 0px; }}"
            f"QLabel#mouseMetricValueScroll {{ color: {tp}; background-color: transparent; border: none; "
            f"font-size: 16px; font-weight: 600; font-family: {mono}; padding: 2px 0px 0px 0px; }}"
        )
    inner = T.L_BG_SURFACE2
    b = T.L_BORDER_SUBTLE
    hb = "rgba(148, 163, 184, 0.45)"
    tp, ts = T.L_TEXT_PRIMARY, T.L_TEXT_SECONDARY
    ac = T.L_KB_TEST_ACCENT
    card_bg = T.L_KB_TEST_PLATE
    return (
        f"QFrame#kbTestCard {{ background-color: {card_bg}; border: 1px solid {b}; border-radius: 12px; padding: 0px; }}"
        f"QWidget#kbDiagHeader {{ background-color: transparent; border: none; "
        f"border-bottom: 1px solid {hb}; }}"
        f"QLabel#kbDiagHeaderIcon {{ background-color: transparent; border: none; }}"
        f"QLabel#kbDiagTitle {{ color: {tp}; background-color: transparent; border: none; "
        f"font-size: 13px; font-weight: 600; padding: 0px; }}"
        f"QWidget#kbDiagBody {{ background-color: transparent; }}"
        f"QFrame#mouseDiagCell {{ background-color: {inner}; border: 1px solid {b}; border-radius: 8px; }}"
        f"QFrame#mouseMetricBox {{ background-color: {inner}; border: 1px solid {b}; border-radius: 8px; }}"
        f"QLabel#mouseDiagKeyLbl {{ color: {ts}; background-color: transparent; border: none; "
        f"font-size: 11px; font-weight: 600; letter-spacing: 0.02em; }}"
        f"QLabel#mouseMetricDimLbl {{ color: {ts}; background-color: transparent; border: none; "
        f"font-size: 11px; font-weight: 500; }}"
        f"QLabel#mouseMetricValueCoords {{ color: {ac}; background-color: transparent; border: none; "
        f"font-size: 18px; font-weight: 600; font-family: {mono}; padding: 2px 0px 0px 0px; }}"
        f"QLabel#mouseMetricValueScroll {{ color: {tp}; background-color: transparent; border: none; "
        f"font-size: 16px; font-weight: 600; font-family: {mono}; padding: 2px 0px 0px 0px; }}"
    )


def mouse_test_pill_style(theme: ThemeMode, down: bool) -> str:
    """Індикатори ЛКМ/ПКМ/СКМ (акцент тесту клавіатури)."""
    if theme == ThemeMode.DARK:
        if down:
            return (
                f"QLabel#mouseTestPill {{ border-radius: 6px; padding: 6px 10px; font-size: 11px; font-weight: 600; "
                f"background: {T.KB_TEST_ACCENT_SOFT}; color: #F8FAFC; border: 1px solid {T.KB_TEST_ACCENT}; }}"
            )
        return (
            f"QLabel#mouseTestPill {{ border-radius: 6px; padding: 6px 10px; font-size: 11px; font-weight: 500; "
            f"background: {T.D_BG_SURFACE2}; color: {T.D_TEXT_SECONDARY}; border: 1px solid {T.D_BORDER_SUBTLE}; }}"
        )
    if down:
        return (
            f"QLabel#mouseTestPill {{ border-radius: 6px; padding: 6px 10px; font-size: 11px; font-weight: 600; "
            f"background: {T.L_KB_TEST_ACCENT_SOFT}; color: {T.L_TEXT_PRIMARY}; border: 1px solid {T.L_KB_TEST_ACCENT}; }}"
        )
    return (
        f"QLabel#mouseTestPill {{ border-radius: 6px; padding: 6px 10px; font-size: 11px; font-weight: 500; "
        f"background: {T.L_BG_SURFACE2}; color: {T.L_TEXT_SECONDARY}; border: 1px solid {T.L_BORDER_SUBTLE}; }}"
    )


def keyboard_test_area_styles(theme: ThemeMode) -> str:
    """Підкладка тесту: одна пластина для main + numpad; історія натискань (QCheckBox — глобальний QSS)."""
    if theme == ThemeMode.DARK:
        outer = T.KB_TEST_PLATE_OUTER
        plate = T.KB_TEST_PLATE
        b = T.KB_TEST_KEY_BORDER
        return (
            f"QWidget#keyboardTestRoot {{ background: {outer}; border: none; border-radius: 0px; }}"
            f"QWidget#keyboardVisual {{ border: 1px solid {b}; border-radius: 12px; background: {plate}; padding: 0px; }}"
            f"QWidget#kbdNumpadSection {{ background: transparent; border: none; }}"
            f"QWidget#keyboardTestRoot QCheckBox {{ spacing: 8px; }}"
            f"QLabel#kbHistChip {{ color: {T.D_TEXT_PRIMARY}; font-size: 11px; font-weight: 500; "
            f"background: {T.D_BG_SURFACE2}; border: 1px solid {b}; border-radius: 4px; padding: 2px 8px; }}"
        )
    outer = T.L_KB_TEST_PLATE_OUTER
    plate = T.L_KB_TEST_PLATE
    b = T.L_KB_TEST_KEY_BORDER
    return (
        f"QWidget#keyboardTestRoot {{ background: {outer}; border: none; }}"
        f"QWidget#keyboardVisual {{ border: 1px solid {b}; border-radius: 12px; background: {plate}; padding: 0px; }}"
        f"QWidget#kbdNumpadSection {{ background: transparent; border: none; }}"
        f"QWidget#keyboardTestRoot QCheckBox {{ spacing: 8px; }}"
        f"QLabel#kbHistChip {{ color: {T.L_TEXT_PRIMARY}; font-size: 11px; font-weight: 500; "
        f"background: {T.L_BG_SURFACE2}; border: 1px solid {b}; border-radius: 4px; padding: 2px 8px; }}"
    )


def keyboard_frame_style(theme: ThemeMode) -> str:
    """Сумісність: підкладка тесту клавіатури."""
    return keyboard_test_area_styles(theme)
