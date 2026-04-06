"""Візуальна клавіатура: сітка як у dist/keyboard.html (table + colspan)."""

from __future__ import annotations

import sys
from collections import defaultdict

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.models.settings import ThemeMode
from app.ui.keyboard_vk_map import KEY_ID_TO_VK_LAYOUT_ONLY
from app.ui.theme import (
    keyboard_fn_key_style,
    keyboard_frame_style,
    keyboard_styles,
    mouse_test_card_style,
    mouse_test_pill_style,
)

# Щільна сітка — мінімальні зазори між клавішами
_GRID_H_SP = 1
_GRID_V_SP = 1
_KEY_MIN_H = 22


class KeyboardTestPanel(QWidget):
    """key_id → список QLabel; підписи залежать від розкладки Windows (UK/RU/EN)."""

    COLS = 16

    def __init__(self, theme: ThemeMode) -> None:
        super().__init__()
        self._theme = theme
        self._idle, self._active = keyboard_styles(theme)
        self._labels: dict[str, list[QLabel]] = defaultdict(list)
        self._fn_deco_labels: list[QLabel] = []
        self._last_hkl_seen: int | None = None
        self._layout_timer = QTimer(self)
        self._layout_timer.setInterval(280)
        self._layout_timer.timeout.connect(self._on_layout_tick)

        root = QVBoxLayout(self)
        root.setSpacing(0)
        root.setContentsMargins(0, 0, 0, 0)

        self._wrap = QWidget()
        self._wrap.setObjectName("keyboardVisual")
        self._wrap.setStyleSheet(keyboard_frame_style(theme))

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setWidget(self._wrap)

        root.addWidget(scroll, 1)

        body = QHBoxLayout(self._wrap)
        body.setSpacing(2)
        body.setContentsMargins(2, 2, 2, 2)

        main_grid = QGridLayout()
        main_grid.setHorizontalSpacing(_GRID_H_SP)
        main_grid.setVerticalSpacing(_GRID_V_SP)
        main_grid.setContentsMargins(0, 0, 0, 0)
        for c in range(self.COLS):
            main_grid.setColumnStretch(c, 1)

        r = 0
        c = 0
        self._gadd(main_grid, r, c, 1, 1, "Esc", "escape")
        c += 1
        for i in range(1, 13):
            self._gadd(main_grid, r, c, 1, 1, f"F{i}", f"f{i}")
            c += 1
        for tx, kid in [
            ("PrtSc\nSysRq", "print_screen"),
            ("Scroll\nLock", "scroll_lock"),
            ("Delete", "delete"),
        ]:
            self._gadd(main_grid, r, c, 1, 1, tx, kid)
            c += 1

        r += 1
        c = 0
        self._gadd(main_grid, r, c, 1, 1, "`\n~", "`")
        c += 1
        for lab, kid in zip(
            ["1\n!", "2\n@", "3\n#", "4\n$", "5\n%", "6\n^", "7\n&", "8\n*", "9\n(", "0\n)"],
            ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"],
            strict=True,
        ):
            self._gadd(main_grid, r, c, 1, 1, lab, kid)
            c += 1
        self._gadd(main_grid, r, c, 1, 1, "-\n_", "-")
        c += 1
        self._gadd(main_grid, r, c, 1, 1, "+\n=", "=")
        c += 1
        self._gadd(main_grid, r, c, 1, 2, "◀\nBackspace", "backspace")
        c += 2
        self._gadd(main_grid, r, c, 1, 1, "Home", "home")

        r += 1
        c = 0
        self._gadd(main_grid, r, c, 1, 2, "◀ Tab ▶", "tab")
        c += 2
        for letter, kid in zip(
            ["Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P"],
            ["q", "w", "e", "r", "t", "y", "u", "i", "o", "p"],
            strict=True,
        ):
            self._gadd(main_grid, r, c, 1, 1, letter, kid)
            c += 1
        self._gadd(main_grid, r, c, 1, 1, "{\n[", "[")
        c += 1
        self._gadd(main_grid, r, c, 1, 1, "}\n]", "]")
        c += 1
        self._gadd(main_grid, r, c, 1, 1, "|\n\\", "\\")
        c += 1
        self._gadd(main_grid, r, c, 1, 1, "PgUp", "page_up")

        r += 1
        c = 0
        self._gadd(main_grid, r, c, 1, 2, "Caps\nLock", "caps_lock")
        c += 2
        for letter, kid in zip(
            ["A", "S", "D", "F", "G", "H", "J", "K", "L"],
            ["a", "s", "d", "f", "g", "h", "j", "k", "l"],
            strict=True,
        ):
            self._gadd(main_grid, r, c, 1, 1, letter, kid)
            c += 1
        self._gadd(main_grid, r, c, 1, 1, ":\n;", ";")
        c += 1
        self._gadd(main_grid, r, c, 1, 1, "\"\n'", "'")
        c += 1
        self._gadd(main_grid, r, c, 1, 2, "◀\nEnter", "enter")
        c += 2
        self._gadd(main_grid, r, c, 1, 1, "PgDn", "page_down")

        r += 1
        c = 0
        self._gadd(main_grid, r, c, 1, 3, "▲\nShift", "shift")
        c += 3
        for letter, kid in zip(
            ["Z", "X", "C", "V", "B", "N", "M"],
            ["z", "x", "c", "v", "b", "n", "m"],
            strict=True,
        ):
            self._gadd(main_grid, r, c, 1, 1, letter, kid)
            c += 1
        self._gadd(main_grid, r, c, 1, 1, "<\n,", ",")
        c += 1
        self._gadd(main_grid, r, c, 1, 1, ">\n.", ".")
        c += 1
        self._gadd(main_grid, r, c, 1, 1, "?\n/", "/")
        c += 1
        self._gadd(main_grid, r, c, 1, 1, "▲\nShift", "shift_r")
        c += 1
        self._gadd(main_grid, r, c, 1, 1, "▲", "up")
        c += 1
        self._gadd(main_grid, r, c, 1, 1, "End", "end")

        r += 1
        c = 0
        self._gadd_deco(main_grid, r, c, 1, 2, "Fn", theme, fn_blue=True)
        c += 2
        self._gadd(main_grid, r, c, 1, 1, "Ctrl", "ctrl_l")
        c += 1
        self._gadd(main_grid, r, c, 1, 1, "Win", "cmd")
        c += 1
        self._gadd(main_grid, r, c, 1, 1, "Alt", "alt")
        c += 1
        self._gadd(main_grid, r, c, 1, 4, "Space", "space")
        c += 4
        self._gadd(main_grid, r, c, 1, 1, "Alt", "alt_r")
        c += 1
        self._gadd(main_grid, r, c, 1, 1, "Win", "cmd_r")
        c += 1
        self._gadd(main_grid, r, c, 1, 1, "\u2630\nMenu", "apps")
        c += 1
        self._gadd(main_grid, r, c, 1, 1, "Ctrl", "ctrl_r")
        c += 1
        self._gadd(main_grid, r, c, 1, 1, "◀", "left")
        c += 1
        self._gadd(main_grid, r, c, 1, 1, "▼", "down")
        c += 1
        self._gadd(main_grid, r, c, 1, 1, "▶", "right")

        body.addLayout(main_grid, 1)

        num_box = QGroupBox("Numpad")
        num_box.setObjectName("kbdNumpadGroup")
        ngrid = QGridLayout(num_box)
        ngrid.setContentsMargins(2, 2, 2, 2)
        ngrid.setHorizontalSpacing(_GRID_H_SP)
        ngrid.setVerticalSpacing(_GRID_V_SP)

        ngrid.addWidget(self._make_key_label("Num\nLock", "num_lock"), 0, 0)
        ngrid.addWidget(self._make_key_label("/", "numpad_divide"), 0, 1)
        ngrid.addWidget(self._make_key_label("*", "numpad_multiply"), 0, 2)
        ngrid.addWidget(self._make_key_label("−", "numpad_subtract"), 0, 3)

        ngrid.addWidget(self._make_key_label("7\nHome", "numpad7"), 1, 0)
        ngrid.addWidget(self._make_key_label("8\n▲", "numpad8"), 1, 1)
        ngrid.addWidget(self._make_key_label("9\nPgUp", "numpad9"), 1, 2)
        ngrid.addWidget(self._make_key_label("+", "numpad_add"), 1, 3, 2, 1)

        ngrid.addWidget(self._make_key_label("4\n◀", "numpad4"), 2, 0)
        ngrid.addWidget(self._make_key_label("5", "numpad5"), 2, 1)
        ngrid.addWidget(self._make_key_label("6\n▶", "numpad6"), 2, 2)

        ngrid.addWidget(self._make_key_label("1\nEnd", "numpad1"), 3, 0)
        ngrid.addWidget(self._make_key_label("2\n▼", "numpad2"), 3, 1)
        ngrid.addWidget(self._make_key_label("3\nPgDn", "numpad3"), 3, 2)
        ngrid.addWidget(self._make_key_label("Enter", "enter"), 3, 3, 2, 1)

        ngrid.addWidget(self._make_key_label("0\nIns", "numpad0"), 4, 0, 1, 2)
        ngrid.addWidget(self._make_key_label(".\nDel", "decimal"), 4, 2)

        body.addWidget(num_box, 0)

        if sys.platform == "win32":
            self._apply_win_layout_labels()

    def _gadd(
        self,
        grid: QGridLayout,
        row: int,
        col: int,
        rowspan: int,
        colspan: int,
        text: str,
        key_id: str,
    ) -> None:
        grid.addWidget(self._make_key_label(text, key_id), row, col, rowspan, colspan)

    def _gadd_deco(
        self,
        grid: QGridLayout,
        row: int,
        col: int,
        rowspan: int,
        colspan: int,
        text: str,
        theme: ThemeMode,
        *,
        fn_blue: bool = False,
    ) -> None:
        lab = QLabel(text)
        lab.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lab.setMinimumHeight(_KEY_MIN_H)
        lab.setFixedHeight(_KEY_MIN_H)
        lab.setMinimumWidth(0)
        lab.setWordWrap(True)
        lab.setObjectName("kbdKeyFn" if fn_blue else "kbdKey")
        lab.setStyleSheet(keyboard_fn_key_style(theme) if fn_blue else self._idle)
        lab.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        if fn_blue:
            self._fn_deco_labels.append(lab)
        grid.addWidget(lab, row, col, rowspan, colspan)

    def _make_key_label(self, text: str, key_id: str) -> QLabel:
        lab = QLabel(text)
        lab.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lab.setMinimumHeight(_KEY_MIN_H)
        lab.setFixedHeight(_KEY_MIN_H)
        lab.setMinimumWidth(0)
        lab.setWordWrap(True)
        lab.setStyleSheet(self._idle)
        lab.setProperty("keyId", key_id)
        lab.setProperty("defaultText", text)
        lab.setObjectName("kbdKey")
        lab.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self._labels[key_id].append(lab)
        return lab

    def _apply_win_layout_labels(self) -> None:
        if sys.platform != "win32":
            return
        from app.ui.keyboard_layout_win import display_labels_for_vks

        labels = display_labels_for_vks(KEY_ID_TO_VK_LAYOUT_ONLY)
        for kid, labs in self._labels.items():
            if kid not in KEY_ID_TO_VK_LAYOUT_ONLY:
                continue
            ch = labels.get(kid, "")
            for lab in labs:
                if ch:
                    lab.setText(ch)
                else:
                    dt = lab.property("defaultText")
                    lab.setText(dt if isinstance(dt, str) else lab.text())

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
        fn_st = keyboard_fn_key_style(theme)
        for labs in self._labels.values():
            for lab in labs:
                lab.setStyleSheet(self._idle)
        for lab in self._fn_deco_labels:
            lab.setStyleSheet(fn_st)

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
            "menu": "apps",
            "pause_break": "pause",
        }
        if n in aliases:
            return aliases[n]
        if len(n) == 1 and n.isalpha():
            return n
        if n.startswith("f") and n[1:].isdigit():
            return n
        if n in self._labels:
            return n
        return None

    def set_key_active(self, key_id: str, active: bool) -> None:
        labs = self._labels.get(key_id)
        if not labs:
            return
        ss = self._active if active else self._idle
        for lab in labs:
            lab.setStyleSheet(ss)


class MouseTestPanel(QWidget):
    def __init__(self, theme: ThemeMode) -> None:
        super().__init__()
        self._theme = theme
        self._down = {"left": False, "right": False, "middle": False}

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        self._card = QFrame()
        self._card.setObjectName("mouseTestCard")
        inner = QVBoxLayout(self._card)
        inner.setContentsMargins(8, 8, 8, 8)
        inner.setSpacing(4)

        title = QLabel("Миша")
        title.setObjectName("mouseTestTitle")

        self.lbl_pos = QLabel("X: 0    Y: 0")
        self.lbl_pos.setObjectName("mouseTestCoords")

        self._pill_l = QLabel("відпущено")
        self._pill_r = QLabel("відпущено")
        self._pill_m = QLabel("відпущено")
        for p in (self._pill_l, self._pill_r, self._pill_m):
            p.setObjectName("mouseTestPill")

        row_l = QHBoxLayout()
        lb_l = QLabel("ЛКМ")
        lb_l.setObjectName("mouseTestLbl")
        row_l.addWidget(lb_l)
        row_l.addWidget(self._pill_l, 1)

        row_r = QHBoxLayout()
        lb_r = QLabel("ПКМ")
        lb_r.setObjectName("mouseTestLbl")
        row_r.addWidget(lb_r)
        row_r.addWidget(self._pill_r, 1)

        row_m = QHBoxLayout()
        lb_m = QLabel("СКМ")
        lb_m.setObjectName("mouseTestLbl")
        row_m.addWidget(lb_m)
        row_m.addWidget(self._pill_m, 1)

        self.lbl_scroll = QLabel("Скрол: dx=0  dy=0")
        self.lbl_scroll.setObjectName("mouseTestScroll")

        inner.addWidget(title)
        inner.addWidget(self.lbl_pos)
        inner.addLayout(row_l)
        inner.addLayout(row_r)
        inner.addLayout(row_m)
        inner.addWidget(self.lbl_scroll)

        root.addWidget(self._card)
        self.set_theme(theme)

    def set_theme(self, theme: ThemeMode) -> None:
        self._theme = theme
        self._card.setStyleSheet(mouse_test_card_style(theme))
        self._apply_pills()

    def _apply_pills(self) -> None:
        t = self._theme
        self._pill_l.setStyleSheet(mouse_test_pill_style(t, self._down["left"]))
        self._pill_r.setStyleSheet(mouse_test_pill_style(t, self._down["right"]))
        self._pill_m.setStyleSheet(mouse_test_pill_style(t, self._down["middle"]))
        self._pill_l.setText("натиснуто" if self._down["left"] else "відпущено")
        self._pill_r.setText("натиснуто" if self._down["right"] else "відпущено")
        self._pill_m.setText("натиснуто" if self._down["middle"] else "відпущено")

    def set_pos(self, x: int, y: int) -> None:
        self.lbl_pos.setText(f"X: {x}  Y: {y}")

    def set_btn(self, name: str, down: bool) -> None:
        if name == "left":
            self._down["left"] = down
        elif name == "right":
            self._down["right"] = down
        else:
            self._down["middle"] = down
        self._apply_pills()

    def set_scroll(self, dx: int, dy: int) -> None:
        self.lbl_scroll.setText(f"Скрол: dx={dx}  dy={dy}")
