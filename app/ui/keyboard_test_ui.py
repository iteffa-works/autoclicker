"""Visual keyboard + mouse test widgets."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from app.models.settings import ThemeMode
from app.ui.theme import keyboard_styles


def _make_key_button(text: str, key_id: str, idle_style: str) -> QLabel:
    lab = QLabel(text)
    lab.setAlignment(Qt.AlignmentFlag.AlignCenter)
    lab.setMinimumSize(30, 30)
    lab.setStyleSheet(idle_style)
    lab.setProperty("keyId", key_id)
    return lab


class KeyboardTestPanel(QWidget):
    """Maps key_id -> QLabel for highlight."""

    def __init__(self, theme: ThemeMode) -> None:
        super().__init__()
        self._theme = theme
        self._idle, self._active = keyboard_styles(theme)
        self._labels: dict[str, QLabel] = {}
        root = QVBoxLayout(self)
        rows: list[list[tuple[str, str]]] = [
            [(f"F{i}", f"f{i}") for i in range(1, 13)],
            [
                ("`", "`"),
                ("1", "1"),
                ("2", "2"),
                ("3", "3"),
                ("4", "4"),
                ("5", "5"),
                ("6", "6"),
                ("7", "7"),
                ("8", "8"),
                ("9", "9"),
                ("0", "0"),
                ("-", "-"),
                ("=", "="),
                ("Bksp", "backspace"),
            ],
            [
                ("Tab", "tab"),
                ("Q", "q"),
                ("W", "w"),
                ("E", "e"),
                ("R", "r"),
                ("T", "t"),
                ("Y", "y"),
                ("U", "u"),
                ("I", "i"),
                ("O", "o"),
                ("P", "p"),
                ("[", "["),
                ("]", "]"),
                ("\\", "\\"),
            ],
            [
                ("Caps", "caps_lock"),
                ("A", "a"),
                ("S", "s"),
                ("D", "d"),
                ("F", "f"),
                ("G", "g"),
                ("H", "h"),
                ("J", "j"),
                ("K", "k"),
                ("L", "l"),
                (";", ";"),
                ("'", "'"),
                ("Enter", "enter"),
            ],
            [
                ("Shift", "shift"),
                ("Z", "z"),
                ("X", "x"),
                ("C", "c"),
                ("V", "v"),
                ("B", "b"),
                ("N", "n"),
                ("M", "m"),
                (",", ","),
                (".", "."),
                ("/", "/"),
                ("Shift", "shift_r"),
            ],
            [
                ("Ctrl", "ctrl_l"),
                ("Win", "cmd"),
                ("Alt", "alt"),
                ("Space", "space"),
                ("Alt", "alt_r"),
                ("Ctrl", "ctrl_r"),
            ],
        ]
        for r in rows:
            row_w = QWidget()
            hl = QHBoxLayout(row_w)
            hl.setSpacing(4)
            for text, kid in r:
                lab = _make_key_button(text, kid, self._idle)
                self._labels[kid] = lab
                hl.addWidget(lab)
            root.addWidget(row_w)
        arrow = QHBoxLayout()
        for text, kid in [("←", "left"), ("↑", "up"), ("↓", "down"), ("→", "right")]:
            lab = _make_key_button(text, kid, self._idle)
            self._labels[kid] = lab
            arrow.addWidget(lab)
        root.addLayout(arrow)
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
        for (text, kid), pos in zip(nmap, positions, strict=False):
            lab = _make_key_button(text, kid, self._idle)
            self._labels[kid] = lab
            ng.addWidget(lab, pos[0], pos[1])
        root.addWidget(num)

    def set_theme(self, theme: ThemeMode) -> None:
        self._theme = theme
        self._idle, self._active = keyboard_styles(theme)
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
