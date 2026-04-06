"""Візуальна клавіатура + тест миші."""

from __future__ import annotations

import sys

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from app.models.settings import ThemeMode
from app.ui.keyboard_vk_map import KEY_ID_TO_VK_LAYOUT_ONLY
from app.ui.theme import keyboard_frame_style, keyboard_styles


def _cell_size(w_scale: float, base_w: int = 30, base_h: int = 34) -> tuple[int, int]:
    w = max(int(base_w * w_scale), 22)
    h = max(base_h, 28)
    return w, h


class KeyboardTestPanel(QWidget):
    """key_id → QLabel; підписи залежать від розкладки Windows (UK/RU/EN)."""

    def __init__(self, theme: ThemeMode) -> None:
        super().__init__()
        self._theme = theme
        self._idle, self._active = keyboard_styles(theme)
        self._labels: dict[str, QLabel] = {}
        self._default_text: dict[str, str] = {}
        self._last_hkl_seen: int | None = None
        self._layout_timer = QTimer(self)
        self._layout_timer.setInterval(280)
        self._layout_timer.timeout.connect(self._on_layout_tick)

        root = QVBoxLayout(self)
        root.setSpacing(6)
        root.setContentsMargins(0, 0, 0, 0)

        self._wrap = QWidget()
        self._wrap.setObjectName("keyboardVisual")
        self._wrap.setStyleSheet(keyboard_frame_style(theme))
        root.addWidget(self._wrap, 0)
        inner = QVBoxLayout(self._wrap)
        inner.setSpacing(5)
        inner.setContentsMargins(4, 8, 4, 8)

        # F-ряд
        self._add_key_row(
            inner,
            [(f"F{i}", f"f{i}", 0.82) for i in range(1, 13)],
            indent_px=0,
        )
        # Ряд 2–6: US QWERTY зі зміщенням
        self._add_key_row(
            inner,
            [
                ("`", "`", 1.0),
                ("1", "1", 1.0),
                ("2", "2", 1.0),
                ("3", "3", 1.0),
                ("4", "4", 1.0),
                ("5", "5", 1.0),
                ("6", "6", 1.0),
                ("7", "7", 1.0),
                ("8", "8", 1.0),
                ("9", "9", 1.0),
                ("0", "0", 1.0),
                ("-", "-", 1.0),
                ("=", "=", 1.0),
                ("Bksp", "backspace", 1.95),
            ],
            indent_px=0,
        )
        self._add_key_row(
            inner,
            [
                ("Tab", "tab", 1.45),
                ("Q", "q", 1.0),
                ("W", "w", 1.0),
                ("E", "e", 1.0),
                ("R", "r", 1.0),
                ("T", "t", 1.0),
                ("Y", "y", 1.0),
                ("U", "u", 1.0),
                ("I", "i", 1.0),
                ("O", "o", 1.0),
                ("P", "p", 1.0),
                ("[", "[", 1.0),
                ("]", "]", 1.0),
                ("\\", "\\", 1.25),
            ],
            indent_px=24,
        )
        self._add_key_row(
            inner,
            [
                ("Caps", "caps_lock", 1.75),
                ("A", "a", 1.0),
                ("S", "s", 1.0),
                ("D", "d", 1.0),
                ("F", "f", 1.0),
                ("G", "g", 1.0),
                ("H", "h", 1.0),
                ("J", "j", 1.0),
                ("K", "k", 1.0),
                ("L", "l", 1.0),
                (";", ";", 1.0),
                ("'", "'", 1.0),
                ("Enter", "enter", 1.95),
            ],
            indent_px=40,
        )
        self._add_key_row(
            inner,
            [
                ("Shift", "shift", 2.15),
                ("Z", "z", 1.0),
                ("X", "x", 1.0),
                ("C", "c", 1.0),
                ("V", "v", 1.0),
                ("B", "b", 1.0),
                ("N", "n", 1.0),
                ("M", "m", 1.0),
                (",", ",", 1.0),
                (".", ".", 1.0),
                ("/", "/", 1.0),
                ("Shift", "shift_r", 2.35),
            ],
            indent_px=52,
        )
        row_mod = QWidget()
        hl = QHBoxLayout(row_mod)
        hl.setSpacing(4)
        for text, kid, sc in [
            ("Ctrl", "ctrl_l", 1.15),
            ("Win", "cmd", 1.15),
            ("Alt", "alt", 1.15),
        ]:
            lab = self._make_key_label(text, kid, sc)
            hl.addWidget(lab)
        space = self._make_key_label("Space", "space", 5.5)
        hl.addWidget(space, 6)
        for text, kid, sc in [("Alt", "alt_r", 1.15), ("Ctrl", "ctrl_r", 1.15)]:
            lab = self._make_key_label(text, kid, sc)
            hl.addWidget(lab)
        inner.addWidget(row_mod)

        arrow = QHBoxLayout()
        arrow.addStretch(1)
        for text, kid in [("←", "left"), ("↑", "up"), ("↓", "down"), ("→", "right")]:
            lab = self._make_key_label(text, kid, 1.05)
            arrow.addWidget(lab)
        arrow.addStretch(1)
        inner.addLayout(arrow)

        num = QGroupBox("Numpad")
        ng = QGridLayout(num)
        nmap = [
            ("7", "numpad7"),
            ("8", "numpad8"),
            ("9", "numpad9"),
            ("4", "numpad4"),
            ("5", "numpad5"),
            ("6", "numpad6"),
            ("1", "numpad1"),
            ("2", "numpad2"),
            ("3", "numpad3"),
            ("0", "numpad0"),
            (".", "decimal"),
        ]
        positions = [(0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (2, 0), (2, 1), (2, 2), (3, 0), (3, 1)]
        for (text, kid), pos in zip(nmap, positions, strict=True):
            lab = self._make_key_label(text, kid, 1.0)
            ng.addWidget(lab, pos[0], pos[1])
        inner.addWidget(num)

        if sys.platform == "win32":
            self._apply_win_layout_labels()

    def _make_key_label(self, text: str, key_id: str, w_scale: float) -> QLabel:
        lab = QLabel(text)
        lab.setAlignment(Qt.AlignmentFlag.AlignCenter)
        w, h = _cell_size(w_scale)
        lab.setMinimumSize(w, h)
        lab.setFixedHeight(h)
        lab.setStyleSheet(self._idle)
        lab.setProperty("keyId", key_id)
        lab.setObjectName("kbdKey")
        self._labels[key_id] = lab
        self._default_text[key_id] = text
        return lab

    def _add_key_row(
        self,
        layout: QVBoxLayout,
        keys: list[tuple[str, str, float]],
        indent_px: int,
    ) -> None:
        row_w = QWidget()
        hl = QHBoxLayout(row_w)
        hl.setSpacing(4)
        hl.setContentsMargins(0, 0, 0, 0)
        if indent_px:
            hl.addSpacing(indent_px)
        for text, kid, scale in keys:
            hl.addWidget(self._make_key_label(text, kid, scale))
        layout.addWidget(row_w)

    def _apply_win_layout_labels(self) -> None:
        if sys.platform != "win32":
            return
        from app.ui.keyboard_layout_win import display_labels_for_vks

        labels = display_labels_for_vks(KEY_ID_TO_VK_LAYOUT_ONLY)
        for kid, lab in self._labels.items():
            if kid not in KEY_ID_TO_VK_LAYOUT_ONLY:
                continue
            ch = labels.get(kid, "")
            if ch:
                lab.setText(ch)
            else:
                lab.setText(self._default_text[kid])

    def _on_layout_tick(self) -> None:
        if not self.isVisible() or sys.platform != "win32":
            return
        from app.ui.keyboard_layout_win import current_hkl

        h = current_hkl() & 0xFFFFFFFFFFFFFFFF
        if h == self._last_hkl_seen:
            return
        self._last_hkl_seen = h
        self._apply_win_layout_labels()

    def set_layout_tracking(self, active: bool) -> None:
        if active:
            self._last_hkl_seen = None
            if sys.platform == "win32":
                self._apply_win_layout_labels()
                from app.ui.keyboard_layout_win import current_hkl

                self._last_hkl_seen = current_hkl() & 0xFFFFFFFFFFFFFFFF
            self._layout_timer.start()
        else:
            self._layout_timer.stop()

    def set_theme(self, theme: ThemeMode) -> None:
        self._theme = theme
        self._idle, self._active = keyboard_styles(theme)
        self._wrap.setStyleSheet(keyboard_frame_style(theme))
        for lab in self._labels.values():
            lab.setStyleSheet(self._idle)

    def normalize(self, name: str) -> str | None:
        n = name.lower().strip()
        aliases = {
            "esc": "escape",
            "backspace": "backspace",
            "return": "enter",
            "enter": "enter",
            "space": "space",
            "shift_l": "shift",
            "shift_r": "shift_r",
            "ctrl_l": "ctrl_l",
            "ctrl_r": "ctrl_r",
            "alt_l": "alt",
            "alt_r": "alt_r",
        }
        if n in aliases:
            return aliases[n]
        if len(n) == 1 and n.isalpha():
            return n
        if n.startswith("f") and n[1:].isdigit():
            return n
        return n if n in self._labels else None

    def set_key_active(self, key_id: str, active: bool) -> None:
        lab = self._labels.get(key_id)
        if not lab:
            return
        lab.setStyleSheet(self._active if active else self._idle)


class MouseTestPanel(QWidget):
    def __init__(self) -> None:
        super().__init__()
        lay = QVBoxLayout(self)
        self.lbl_pos = QLabel("X: 0  Y: 0")
        self.lbl_left = QLabel("ЛКМ: —")
        self.lbl_right = QLabel("ПКМ: —")
        self.lbl_mid = QLabel("СКМ: —")
        self.lbl_scroll = QLabel("Скрол: —")
        for w in (self.lbl_pos, self.lbl_left, self.lbl_right, self.lbl_mid, self.lbl_scroll):
            lay.addWidget(w)

    def set_pos(self, x: int, y: int) -> None:
        self.lbl_pos.setText(f"X: {x}  Y: {y}")

    def set_btn(self, name: str, down: bool) -> None:
        state = "натиснуто" if down else "відпущено"
        if name == "left":
            self.lbl_left.setText(f"ЛКМ: {state}")
        elif name == "right":
            self.lbl_right.setText(f"ПКМ: {state}")
        else:
            self.lbl_mid.setText(f"СКМ: {state}")

    def set_scroll(self, dx: int, dy: int) -> None:
        self.lbl_scroll.setText(f"Скрол: dx={dx} dy={dy}")
