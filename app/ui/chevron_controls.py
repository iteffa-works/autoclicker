"""Combo/spin controls with reliable chevron painting on top of Qt subcontrols."""

from __future__ import annotations

from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QColor, QPainter, QPen, QShowEvent
from PySide6.QtWidgets import QComboBox as QtQComboBox
from PySide6.QtWidgets import QDoubleSpinBox as QtQDoubleSpinBox
from PySide6.QtWidgets import QSpinBox as QtQSpinBox


class _ChevronOverlayMixin:
    def _overlay_color(self) -> QColor:
        color = self.palette().color(self.foregroundRole())
        if not color.isValid():
            color = QColor("#CBD5E1")
        color.setAlpha(235 if self.isEnabled() else 120)
        return color

    def _refresh_overlay_icons(self) -> None:
        self.update()

    def changeEvent(self, event: QEvent) -> None:
        super().changeEvent(event)
        if event.type() in (
            QEvent.Type.EnabledChange,
            QEvent.Type.PaletteChange,
            QEvent.Type.StyleChange,
        ):
            self._refresh_overlay_icons()

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        self._refresh_overlay_icons()


class QComboBox(_ChevronOverlayMixin, QtQComboBox):
    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        pen = QPen(self._overlay_color(), 1.7, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        p.setPen(pen)
        btn_w = 26 if self.height() <= 34 else 32
        x = self.width() - btn_w + (btn_w - 10) // 2
        y = self.height() // 2 - 1
        p.drawLine(x, y - 2, x + 5, y + 2)
        p.drawLine(x + 5, y + 2, x + 10, y - 2)
        p.end()


class _SpinChevronMixin(_ChevronOverlayMixin):
    def _paint_spin_chevrons(self) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        pen = QPen(self._overlay_color(), 1.7, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        p.setPen(pen)
        btn_w = 22 if self.height() <= 34 else 28
        x = self.width() - btn_w + (btn_w - 10) // 2
        up_y = max(4, self.height() // 4)
        down_y = min(self.height() - 5, (self.height() * 3) // 4)
        p.drawLine(x, up_y + 2, x + 5, up_y - 2)
        p.drawLine(x + 5, up_y - 2, x + 10, up_y + 2)
        p.drawLine(x, down_y - 2, x + 5, down_y + 2)
        p.drawLine(x + 5, down_y + 2, x + 10, down_y - 2)
        p.end()


class QSpinBox(_SpinChevronMixin, QtQSpinBox):
    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        self._paint_spin_chevrons()


class QDoubleSpinBox(_SpinChevronMixin, QtQDoubleSpinBox):
    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        self._paint_spin_chevrons()
