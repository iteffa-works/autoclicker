"""Font Awesome 5 (Solid) icons via qtawesome; colors follow app theme."""

from __future__ import annotations

import qtawesome as qta

from PySide6.QtGui import QIcon, QPixmap

from app.models.settings import ThemeMode
from app.ui import design_tokens as T

# Parallel to main_window._NAV_TITLES (5 tabs)
NAV_ICON_KEYS = (
    "nav_autoclick",
    "nav_macros",
    "nav_kb_test",
    "nav_settings",
    "nav_logs",
)

# Logical keys -> qtawesome icon id (fa5s.*)
_ICON_MAP: dict[str, str] = {
    # Nav (tabs)
    "nav_autoclick": "fa5s.mouse",
    "nav_macros": "fa5s.layer-group",
    "nav_kb_test": "fa5s.keyboard",
    "nav_settings": "fa5s.cog",
    "nav_logs": "fa5s.file-alt",
    # Toolbar (header)
    "action_play": "fa5s.play",
    "action_pause": "fa5s.pause",
    "action_stop": "fa5s.stop",
    "action_undo": "fa5s.undo",
    "action_save": "fa5s.save",
    "action_crosshairs": "fa5s.crosshairs",
    "action_plus": "fa5s.plus",
    "action_minus": "fa5s.minus",
    "action_listen": "fa5s.bullhorn",
    "action_clear": "fa5s.times",
    "action_apply": "fa5s.check",
    # Autoclick / macro actions
    "macro_record": "fa5s.circle",
    "macro_stop_rec": "fa5s.stop-circle",
    "macro_play": "fa5s.play",
    "macro_stop_play": "fa5s.stop",
    "macro_save_as": "fa5s.save",
    "macro_load": "fa5s.folder-open",
    "macro_delete": "fa5s.trash-alt",
    "macro_rename": "fa5s.edit",
    "macro_preview": "fa5s.eye",
    "macro_profile_new": "fa5s.plus",
    "macro_profile_save": "fa5s.save",
    # Section headers
    "section_click": "fa5s.mouse",
    "section_intervals": "fa5s.clock",
    "section_position": "fa5s.crosshairs",
    "section_work_mode": "fa5s.sliders-h",
    "section_key_repeat": "fa5s.keyboard",
    "section_human": "fa5s.leaf",
    "section_sequence": "fa5s.list-ol",
    "section_profile": "fa5s.id-card",
    "section_record_flags": "fa5s.clipboard-list",
    "section_macros_list": "fa5s.folder-open",
    "section_playback": "fa5s.play-circle",
    "section_logs": "fa5s.stream",
}

# Pixel sizes (width = height)
ICON_SIZE_NAV = 16
ICON_SIZE_TOOLBAR = 18
ICON_SIZE_SECTION = 18
# QCheckBox::indicator:checked — QSS приймає лише url(); збираємо pixmap з Font Awesome (qtawesome).
CHECKBOX_INDICATOR_PX = 18

_KIND_TO_SIZE = {
    "nav": ICON_SIZE_NAV,
    "toolbar": ICON_SIZE_TOOLBAR,
    "section": ICON_SIZE_SECTION,
}


def icon_kind_size(kind: str) -> int:
    return _KIND_TO_SIZE.get(kind, ICON_SIZE_TOOLBAR)


def _icon_color(theme: ThemeMode) -> str:
    return T.D_TEXT_PRIMARY if theme == ThemeMode.DARK else T.L_TEXT_PRIMARY


def app_icon(key: str, theme: ThemeMode) -> QIcon:
    fa = _ICON_MAP.get(key, "fa5s.circle")
    return qta.icon(fa, color=_icon_color(theme))


def checkbox_checked_pixmap(theme: ThemeMode) -> QPixmap:
    """Зелений «увімкнено»: квадрат + галочка (два шари fa5s)."""
    s = CHECKBOX_INDICATOR_PX
    if theme == ThemeMode.DARK:
        return qta.icon(
            "fa5s.square",
            "fa5s.check",
            options=[
                {"color": T.D_STATE_SUCCESS, "scale_factor": 1.0},
                {"color": "#FFFFFF", "scale_factor": 0.55},
            ],
        ).pixmap(s, s)
    return qta.icon(
        "fa5s.square",
        "fa5s.check",
        options=[
            {"color": "#DCFCE7", "scale_factor": 1.0},
            {"color": "#166534", "scale_factor": 0.55},
        ],
    ).pixmap(s, s)
