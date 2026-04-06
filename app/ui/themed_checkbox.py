"""Custom QCheckBox with reliable painted checkmark for desktop dark/light UI."""

from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, QSize, Qt
from PySide6.QtGui import QColor, QFontMetrics, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QCheckBox, QSizePolicy, QWidget

from app.models.settings import ThemeMode
from app.ui import design_tokens as T

_INDICATOR_PX = 18
_RADIUS = 5.0
_TEXT_GAP = 10


class ThemedCheckBox(QCheckBox):
    """Checkbox with custom-painted indicator and checkmark."""

    def __init__(self, text: str = "", parent: QWidget | None = None, *, theme: ThemeMode = ThemeMode.DARK) -> None:
        super().__init__(text, parent)
        self._theme = theme
        self._hover = False
        self._pressed = False
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMouseTracking(True)
        self.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        self.setMinimumHeight(max(_INDICATOR_PX, self.fontMetrics().height()) + 4)

    def set_theme(self, theme: ThemeMode) -> None:
        self._theme = theme
        self.update()

    def sizeHint(self) -> QSize:
        fm = QFontMetrics(self.font())
        text_w = fm.horizontalAdvance(self.text()) if self.text() else 0
        w = _INDICATOR_PX + (_TEXT_GAP if text_w else 0) + text_w + 6
        h = max(_INDICATOR_PX, fm.height()) + 6
        return QSize(w, h)

    def minimumSizeHint(self) -> QSize:
        return self.sizeHint()

    def enterEvent(self, event) -> None:  # type: ignore[override]
        self._hover = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:  # type: ignore[override]
        self._hover = False
        self._pressed = False
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event) -> None:  # type: ignore[override]
        if event.button() == Qt.MouseButton.LeftButton and self.isEnabled():
            self._pressed = True
            self.update()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event) -> None:  # type: ignore[override]
        self._pressed = False
        self.update()
        super().mouseReleaseEvent(event)

    def changeEvent(self, event) -> None:  # type: ignore[override]
        super().changeEvent(event)
        self.update()

    def paintEvent(self, event) -> None:  # type: ignore[override]
        del event
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect()
        ind_rect = QRectF(
            0.5,
            (rect.height() - _INDICATOR_PX) / 2 + 0.5,
            _INDICATOR_PX - 1.0,
            _INDICATOR_PX - 1.0,
        )

        border, fill, text_color, check_color = self._colors()
        pen = QPen(border)
        pen.setWidth(1)
        p.setPen(pen)
        p.setBrush(fill)
        p.drawRoundedRect(ind_rect, _RADIUS, _RADIUS)

        if self.isChecked():
            self._draw_checkmark(p, check_color, ind_rect)

        if self.text():
            text_rect = rect.adjusted(_INDICATOR_PX + _TEXT_GAP, 0, 0, 0)
            p.setPen(text_color)
            p.drawText(text_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, self.text())

        p.end()

    def _colors(self) -> tuple[QColor, QColor, QColor, QColor]:
        if self._theme == ThemeMode.DARK:
            text = QColor(T.D_TEXT_DISABLED if not self.isEnabled() else T.D_TEXT_PRIMARY)
            if self.isChecked():
                if not self.isEnabled():
                    return QColor("#475569"), QColor("#334155"), text, QColor("#94A3B8")
                if self._pressed:
                    return QColor(T.D_ACCENT_ACTIVE), QColor("#1E1B4B"), text, QColor("#F8FAFC")
                if self._hover:
                    return QColor(T.D_ACCENT_HOVER), QColor("#3730A3"), text, QColor("#FFFFFF")
                return QColor(T.D_ACCENT), QColor(T.D_SELECTION_BG), text, QColor("#FFFFFF")
            if not self.isEnabled():
                return QColor("#475569"), QColor("#293548"), text, QColor("#94A3B8")
            if self._pressed:
                return QColor(T.D_BORDER_SUBTLE), QColor("#1E293B"), text, QColor("#FFFFFF")
            if self._hover:
                return QColor("#475569"), QColor("#334155"), text, QColor("#FFFFFF")
            return QColor(T.D_BORDER_SUBTLE), QColor(T.D_BG_SURFACE2), text, QColor("#FFFFFF")

        text = QColor(T.L_TEXT_DISABLED if not self.isEnabled() else T.L_TEXT_PRIMARY)
        if self.isChecked():
            if not self.isEnabled():
                return QColor("#CBD5E1"), QColor("#F1F5F9"), text, QColor("#94A3B8")
            if self._pressed:
                return QColor(T.L_ACCENT_ACTIVE), QColor("#C7D2FE"), text, QColor("#1E1B4B")
            if self._hover:
                return QColor(T.L_ACCENT_HOVER), QColor("#E0E7FF"), text, QColor("#312E81")
            return QColor(T.L_ACCENT), QColor(T.L_SELECTION_BG), text, QColor(T.L_ACCENT_ACTIVE)
        if not self.isEnabled():
            return QColor("#E2E8F0"), QColor("#F1F5F9"), text, QColor("#94A3B8")
        if self._pressed:
            return QColor(T.L_BORDER_SUBTLE), QColor("#E2E8F0"), text, QColor(T.L_ACCENT_ACTIVE)
        if self._hover:
            return QColor("#CBD5E1"), QColor("#F1F5F9"), text, QColor(T.L_ACCENT_ACTIVE)
        return QColor(T.L_BORDER_SUBTLE), QColor(T.L_BG_SURFACE), text, QColor(T.L_ACCENT_ACTIVE)

    def _draw_checkmark(self, p: QPainter, color: QColor, ind_rect: QRectF) -> None:
        pen = QPen(color)
        pen.setWidthF(2.5)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        path = QPainterPath()
        left = ind_rect.left()
        top = ind_rect.top()
        path.moveTo(QPointF(left + 4.0, top + 8.7))
        path.lineTo(QPointF(left + 7.7, top + 12.2))
        path.lineTo(QPointF(left + 13.4, top + 4.8))
        p.strokePath(path, pen)


def sync_themed_checkboxes(root: QWidget, theme: ThemeMode) -> None:
    """Apply current theme to every custom checkbox under root."""
    for cb in root.findChildren(ThemedCheckBox):
        cb.set_theme(theme)
