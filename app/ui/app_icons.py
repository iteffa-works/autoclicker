"""Font Awesome 5 (Solid) icons via qtawesome; colors follow app theme."""

from __future__ import annotations

import qtawesome as qta

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (
    QBrush,
    QColor,
    QIcon,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
)

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
    # Діагностика (вкладка тесту клавіатури)
    "diag_mouse": "fa5s.mouse",
    "diag_coords": "fa5s.crosshairs",
    "diag_scroll": "fa5s.arrows-alt-v",
    # Сайдбар: соцмережі та контакт
    "brand_telegram": "fa5b.telegram",
    "brand_whatsapp": "fa5b.whatsapp",
    "brand_email": "fa5s.envelope",
}

# Pixel sizes (width = height)
ICON_SIZE_NAV = 16
ICON_SIZE_TOOLBAR = 18
ICON_SIZE_SECTION = 18
ICON_SIZE_BRAND_SOCIAL = 20
# QCheckBox::indicator:checked — QSS приймає лише url(); збираємо pixmap з Font Awesome (qtawesome).
CHECKBOX_INDICATOR_PX = 18

_KIND_TO_SIZE = {
    "nav": ICON_SIZE_NAV,
    "toolbar": ICON_SIZE_TOOLBAR,
    "section": ICON_SIZE_SECTION,
    "brand_social": ICON_SIZE_BRAND_SOCIAL,
}


def icon_kind_size(kind: str) -> int:
    return _KIND_TO_SIZE.get(kind, ICON_SIZE_TOOLBAR)


def _icon_color(theme: ThemeMode) -> str:
    return T.D_TEXT_PRIMARY if theme == ThemeMode.DARK else T.L_TEXT_PRIMARY


def app_icon(key: str, theme: ThemeMode) -> QIcon:
    fa = _ICON_MAP.get(key, "fa5s.circle")
    if key == "brand_telegram":
        return qta.icon(fa, color="#2AABEE")
    if key == "brand_whatsapp":
        return qta.icon(fa, color="#25D366")
    if key == "brand_email":
        return qta.icon(fa, color="#EF4444")
    return qta.icon(fa, color=_icon_color(theme))


def _paint_vector_checkmark_color(p: QPainter, check_hex: str) -> None:
    """Галочка штрихами — один шар PNG для QSS `image:`."""
    pen = QPen(QColor(check_hex))
    pen.setWidthF(2.5)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    path = QPainterPath()
    path.moveTo(QPointF(4.0, 9.2))
    path.lineTo(QPointF(7.85, 13.0))
    path.lineTo(QPointF(14.0, 5.2))
    p.strokePath(path, pen)


def _checkbox_indicator_composite_pixmap(
    border_hex: str,
    fill_hex: str,
    check_hex: str,
    *,
    radius: float = 5.0,
) -> QPixmap:
    """18×18: рамка + заливка + галочка (повний растр для QCheckBox::indicator:checked*)."""
    s = CHECKBOX_INDICATOR_PX
    pm = QPixmap(s, s)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    pen = QPen(QColor(border_hex))
    pen.setWidth(1)
    p.setPen(pen)
    p.setBrush(QBrush(QColor(fill_hex)))
    p.drawRoundedRect(QRectF(0.5, 0.5, s - 1.0, s - 1.0), radius, radius)
    p.setBrush(Qt.BrushStyle.NoBrush)
    _paint_vector_checkmark_color(p, check_hex)
    p.end()
    return pm


def checkbox_checked_state_pixmaps(theme: ThemeMode) -> dict[str, QPixmap]:
    """Растри для QSS: checked, checked_hover, checked_pressed, checked_disabled."""
    if theme == ThemeMode.DARK:
        return {
            "checked": _checkbox_indicator_composite_pixmap(
                T.D_ACCENT, T.D_SELECTION_BG, "#FFFFFF"
            ),
            "checked_hover": _checkbox_indicator_composite_pixmap(
                T.D_ACCENT_HOVER, "#3730A3", "#FFFFFF"
            ),
            "checked_pressed": _checkbox_indicator_composite_pixmap(
                T.D_ACCENT_ACTIVE, "#1E1B4B", "#F8FAFC"
            ),
            "checked_disabled": _checkbox_indicator_composite_pixmap(
                "#475569", "#334155", "#94A3B8"
            ),
        }
    return {
        "checked": _checkbox_indicator_composite_pixmap(
            T.L_ACCENT, T.L_SELECTION_BG, T.L_ACCENT_ACTIVE
        ),
        "checked_hover": _checkbox_indicator_composite_pixmap(
            T.L_ACCENT_HOVER, "#E0E7FF", "#312E81"
        ),
        "checked_pressed": _checkbox_indicator_composite_pixmap(
            T.L_ACCENT_ACTIVE, "#C7D2FE", "#1E1B4B"
        ),
        "checked_disabled": _checkbox_indicator_composite_pixmap(
            "#CBD5E1", "#F1F5F9", "#94A3B8"
        ),
    }
