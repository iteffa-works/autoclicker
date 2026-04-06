"""Візуальна клавіатура тесту: сітка 16×col, KeyCapWidget; main + numpad — одна пластина."""

from __future__ import annotations

import sys
from collections import defaultdict, deque

from PySide6.QtCore import QEvent, QEasingCurve, QPropertyAnimation, Qt, QTimer
from PySide6.QtGui import QEnterEvent
from PySide6.QtWidgets import (
    QCheckBox,
    QFrame,
    QGraphicsOpacityEffect,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.models.settings import ThemeMode
from app.ui import design_tokens as DT
from app.ui.app_icons import app_icon
from app.ui.keyboard_vk_map import KEY_ID_TO_VK_LAYOUT_ONLY
from app.ui.theme import (
    KeyboardKeycapStyles,
    keyboard_frame_style,
    keyboard_keycap_styles,
    mouse_test_panel_styles,
    mouse_test_pill_style,
)


def _key_outer_size(colspan: int, rowspan: int) -> tuple[int, int]:
    uw, h, g = DT.KB_TEST_KEY_UNIT_W, DT.KB_TEST_KEY_H, DT.KB_TEST_GRID_GAP
    w = colspan * uw + (colspan - 1) * g
    hh = rowspan * h + (rowspan - 1) * g
    return w, hh


class KeyCapWidget(QFrame):
    """Клавіша з hover / active і коротким fade після відпускання."""

    def __init__(
        self,
        text: str,
        key_id: str,
        *,
        width_px: int,
        height_px: int,
        fn_key: bool = False,
        tooltip: str | None = None,
    ) -> None:
        super().__init__()
        self.setObjectName("keyCap")
        self._key_id = key_id
        self._fn_key = fn_key
        self._styles: KeyboardKeycapStyles | None = None
        self._is_active = False
        self._hover = False
        self.setMinimumSize(width_px, height_px)
        self.setMouseTracking(True)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

        self._lbl = QLabel(text)
        self._lbl.setObjectName("keyCapLabel")
        self._lbl.setAlignment(
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter
        )
        self._lbl.setWordWrap(True)
        self._lbl.setMinimumWidth(0)
        self._lbl.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )
        self._lbl.setMouseTracking(True)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(6, 5, 6, 5)
        lay.addWidget(self._lbl, 0, Qt.AlignmentFlag.AlignCenter)

        self._opacity = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._opacity)
        self._opacity.setOpacity(1.0)
        self._fade = QPropertyAnimation(self._opacity, b"opacity", self)
        self._fade.setDuration(130)
        self._fade.setEasingCurve(QEasingCurve.Type.OutCubic)

        if tooltip:
            self.setToolTip(tooltip)
            self._lbl.setToolTip(tooltip)

    def key_id(self) -> str:
        return self._key_id

    def set_styles(self, styles: KeyboardKeycapStyles) -> None:
        self._styles = styles
        self._fade.stop()
        self._opacity.setOpacity(1.0)
        self._apply_style()

    def set_label_text(self, text: str) -> None:
        self._lbl.setText(text)

    def text(self) -> str:
        return self._lbl.text()

    def set_active(self, on: bool) -> None:
        self._fade.stop()
        self._is_active = on
        if on:
            self._opacity.setOpacity(1.0)
            self._apply_style()
            return
        self._apply_style()
        self._opacity.setOpacity(0.88)
        self._fade.setStartValue(0.88)
        self._fade.setEndValue(1.0)
        self._fade.start()

    def _apply_style(self) -> None:
        if not self._styles:
            return
        s = self._styles
        if self._fn_key:
            if self._is_active:
                self.setStyleSheet(s.fn_active)
            elif self._hover:
                self.setStyleSheet(s.fn_hover)
            else:
                self.setStyleSheet(s.fn_idle)
        elif self._is_active:
            self.setStyleSheet(s.active)
        elif self._hover:
            self.setStyleSheet(s.hover)
        else:
            self.setStyleSheet(s.idle)

    def enterEvent(self, event: QEnterEvent) -> None:
        self._hover = True
        if not self._is_active:
            self._apply_style()
        super().enterEvent(event)

    def leaveEvent(self, event: QEvent) -> None:
        self._hover = False
        if not self._is_active:
            self._apply_style()
        super().leaveEvent(event)


def _tooltip_for_key(default_text: str, key_id: str) -> str:
    t = default_text.replace("\n", " ").strip()
    if t:
        return f"{t} ({key_id})"
    return key_id


class KeyboardTestPanel(QWidget):
    """key_id → список KeyCapWidget; підписи залежать від розкладки Windows (UK/RU/EN)."""

    COLS = 16
    NUM_COLS = 4
    _HIST_MAX = 32

    def __init__(self, theme: ThemeMode) -> None:
        super().__init__()
        self.setObjectName("keyboardTestRoot")
        self._theme = theme
        self._styles = keyboard_keycap_styles(theme)
        self._caps: dict[str, list[KeyCapWidget]] = defaultdict(list)
        self._fn_caps: list[KeyCapWidget] = []
        self._last_hkl_seen: int | None = None
        self._layout_timer = QTimer(self)
        self._layout_timer.setInterval(280)
        self._layout_timer.timeout.connect(self._on_layout_tick)

        self._hist_deque: deque[str] = deque(maxlen=self._HIST_MAX)

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        root = QVBoxLayout(self)
        root.setSpacing(DT.S16)
        root.setContentsMargins(0, 0, 0, 0)

        hist_row = QHBoxLayout()
        hist_row.setContentsMargins(DT.S12, 0, DT.S12, 0)
        hist_row.setSpacing(DT.S8)
        self._hist_check = QCheckBox("Історія натискань")
        self._hist_check.setToolTip("Показувати останні натискання клавіш")
        hist_row.addWidget(self._hist_check)
        self._hist_chips_host = QWidget()
        self._hist_chips_host.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )
        self._hist_chips_layout = QHBoxLayout(self._hist_chips_host)
        self._hist_chips_layout.setContentsMargins(0, 0, 0, 0)
        self._hist_chips_layout.setSpacing(6)
        self._hist_chips_layout.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        hist_row.addWidget(self._hist_chips_host, 1)
        root.addLayout(hist_row)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        scroll.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        self._wrap = QWidget()
        self._wrap.setObjectName("keyboardVisual")
        self._wrap.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        inner = QVBoxLayout(self._wrap)
        inner.setSpacing(DT.S16)
        inner.setContentsMargins(DT.S12, DT.S16, DT.S12, DT.S16)
        inner.setAlignment(Qt.AlignmentFlag.AlignTop)

        main_keyboard_wrap = QWidget()
        main_keyboard_wrap.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )
        main_grid = QGridLayout(main_keyboard_wrap)
        main_grid.setHorizontalSpacing(DT.KB_TEST_GRID_GAP)
        main_grid.setVerticalSpacing(DT.KB_TEST_GRID_GAP)
        main_grid.setContentsMargins(0, 0, 0, 0)
        for c in range(self.COLS):
            main_grid.setColumnMinimumWidth(c, DT.KB_TEST_KEY_UNIT_W)
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
        self._gadd_deco(main_grid, r, c, 1, 1, "Fn", fn_blue=True)
        c += 1
        self._gadd(main_grid, r, c, 1, 1, "Ctrl", "ctrl_l")
        c += 1
        self._gadd(main_grid, r, c, 1, 1, "Win", "cmd")
        c += 1
        self._gadd(main_grid, r, c, 1, 1, "Alt", "alt")
        c += 1
        self._gadd(main_grid, r, c, 1, 5, "Space", "space")
        c += 5
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

        main_holder = QWidget()
        main_holder.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )
        mh_row = QHBoxLayout(main_holder)
        mh_row.setContentsMargins(0, 0, 0, 0)
        mh_row.setSpacing(0)
        mh_row.addWidget(main_keyboard_wrap, 1, Qt.AlignmentFlag.AlignTop)

        row_kb = QHBoxLayout()
        row_kb.setSpacing(DT.KB_TEST_MAIN_NUM_GAP)
        row_kb.setContentsMargins(0, 0, 0, 0)
        row_kb.setAlignment(Qt.AlignmentFlag.AlignTop)
        row_kb.addWidget(main_holder, 1, Qt.AlignmentFlag.AlignTop)
        num_pad = QWidget()
        num_pad.setObjectName("kbdNumpadSection")
        num_pad.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        num_lay = QVBoxLayout(num_pad)
        num_lay.setContentsMargins(0, 0, 0, 0)
        num_lay.setSpacing(0)
        ngrid = QGridLayout()
        ngrid.setHorizontalSpacing(DT.KB_TEST_GRID_GAP)
        ngrid.setVerticalSpacing(DT.KB_TEST_GRID_GAP)
        for c in range(self.NUM_COLS):
            ngrid.setColumnMinimumWidth(c, DT.KB_TEST_KEY_UNIT_W)
            ngrid.setColumnStretch(c, 1)

        ngrid.addWidget(self._make_key_cap("Num\nLock", "num_lock", 1, 1), 0, 0)
        ngrid.addWidget(self._make_key_cap("/", "numpad_divide", 1, 1), 0, 1)
        ngrid.addWidget(self._make_key_cap("*", "numpad_multiply", 1, 1), 0, 2)
        ngrid.addWidget(self._make_key_cap("−", "numpad_subtract", 1, 1), 0, 3)

        ngrid.addWidget(self._make_key_cap("7\nHome", "numpad7", 1, 1), 1, 0)
        ngrid.addWidget(self._make_key_cap("8\n▲", "numpad8", 1, 1), 1, 1)
        ngrid.addWidget(self._make_key_cap("9\nPgUp", "numpad9", 1, 1), 1, 2)
        ngrid.addWidget(self._make_key_cap("+", "numpad_add", 1, 2), 1, 3, 2, 1)

        ngrid.addWidget(self._make_key_cap("4\n◀", "numpad4", 1, 1), 2, 0)
        ngrid.addWidget(self._make_key_cap("5", "numpad5", 1, 1), 2, 1)
        ngrid.addWidget(self._make_key_cap("6\n▶", "numpad6", 1, 1), 2, 2)

        ngrid.addWidget(self._make_key_cap("1\nEnd", "numpad1", 1, 1), 3, 0)
        ngrid.addWidget(self._make_key_cap("2\n▼", "numpad2", 1, 1), 3, 1)
        ngrid.addWidget(self._make_key_cap("3\nPgDn", "numpad3", 1, 1), 3, 2)
        ngrid.addWidget(self._make_key_cap("Enter", "enter", 1, 2), 3, 3, 2, 1)

        ngrid.addWidget(self._make_key_cap("0\nIns", "numpad0", 2, 1), 4, 0, 1, 2)
        ngrid.addWidget(self._make_key_cap(".\nDel", "decimal", 1, 1), 4, 2)

        num_lay.addLayout(ngrid)
        row_kb.addWidget(num_pad, 0, Qt.AlignmentFlag.AlignTop)
        inner.addLayout(row_kb)

        scroll.setWidget(self._wrap)
        root.addWidget(scroll, 0)

        self.setStyleSheet(keyboard_frame_style(theme))
        self._apply_styles_to_caps()

        if sys.platform == "win32":
            self._apply_win_layout_labels()

    def _apply_styles_to_caps(self) -> None:
        for caps in self._caps.values():
            for cap in caps:
                cap.set_styles(self._styles)
        for cap in self._fn_caps:
            cap.set_styles(self._styles)

    def _make_key_cap(self, text: str, key_id: str, colspan: int, rowspan: int) -> KeyCapWidget:
        w, h = _key_outer_size(colspan, rowspan)
        tip = _tooltip_for_key(text, key_id)
        cap = KeyCapWidget(text, key_id, width_px=w, height_px=h, fn_key=False, tooltip=tip)
        cap.set_styles(self._styles)
        cap.setProperty("defaultText", text)
        self._caps[key_id].append(cap)
        return cap

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
        grid.addWidget(self._make_key_cap(text, key_id, colspan, rowspan), row, col, rowspan, colspan)

    def _gadd_deco(
        self,
        grid: QGridLayout,
        row: int,
        col: int,
        rowspan: int,
        colspan: int,
        text: str,
        *,
        fn_blue: bool = False,
    ) -> None:
        w, h = _key_outer_size(colspan, rowspan)
        tip = _tooltip_for_key(text, "fn")
        cap = KeyCapWidget(text, "fn", width_px=w, height_px=h, fn_key=True, tooltip=tip)
        cap.set_styles(self._styles)
        cap.setProperty("defaultText", text)
        self._fn_caps.append(cap)
        self._caps["fn"].append(cap)
        grid.addWidget(cap, row, col, rowspan, colspan)

    def _apply_win_layout_labels(self) -> None:
        if sys.platform != "win32":
            return
        from app.ui.keyboard_layout_win import display_labels_for_vks

        labels = display_labels_for_vks(KEY_ID_TO_VK_LAYOUT_ONLY)
        for kid, caps in self._caps.items():
            if kid not in KEY_ID_TO_VK_LAYOUT_ONLY:
                continue
            ch = labels.get(kid, "")
            for cap in caps:
                if ch:
                    cap.set_label_text(ch)
                else:
                    dt = cap.property("defaultText")
                    cap.set_label_text(dt if isinstance(dt, str) else cap.text())

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
        self._styles = keyboard_keycap_styles(theme)
        self.setStyleSheet(keyboard_frame_style(theme))
        self._apply_styles_to_caps()

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
        if n in self._caps:
            return n
        return None

    def set_key_active(self, key_id: str, active: bool) -> None:
        caps = self._caps.get(key_id)
        if not caps:
            return
        for cap in caps:
            cap.set_active(active)

    def record_key_press(self, key_id: str) -> None:
        if not self._hist_check.isChecked():
            return
        self._hist_deque.append(key_id)
        self._refresh_hist_chips()

    def _refresh_hist_chips(self) -> None:
        while self._hist_chips_layout.count():
            item = self._hist_chips_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for kid in self._hist_deque:
            lab = QLabel(kid)
            lab.setObjectName("kbHistChip")
            lab.setSizePolicy(
                QSizePolicy.Policy.Preferred,
                QSizePolicy.Policy.Preferred,
            )
            self._hist_chips_layout.addWidget(lab)


class MouseTestPanel(QWidget):
    _ICON_HEADER_PX = 18

    def __init__(self, theme: ThemeMode) -> None:
        super().__init__()
        self._theme = theme
        self._down = {"left": False, "right": False, "middle": False}
        self._header_icons: list[tuple[str, QLabel]] = []

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(DT.S12)

        row = QHBoxLayout()
        row.setSpacing(DT.S12)
        row.setContentsMargins(0, 0, 0, 0)
        self._pill_l = QLabel("відпущено")
        self._pill_r = QLabel("відпущено")
        self._pill_m = QLabel("відпущено")
        for p in (self._pill_l, self._pill_r, self._pill_m):
            p.setObjectName("mouseTestPill")
        self._lbl_x = QLabel("0")
        self._lbl_y = QLabel("0")
        self._lbl_x.setObjectName("mouseMetricValueCoords")
        self._lbl_y.setObjectName("mouseMetricValueCoords")
        self._lbl_dx = QLabel("0")
        self._lbl_dy = QLabel("0")
        self._lbl_dx.setObjectName("mouseMetricValueScroll")
        self._lbl_dy.setObjectName("mouseMetricValueScroll")

        row.addWidget(self._build_card_mouse(), 1)
        row.addWidget(self._build_card_coords(), 1)
        row.addWidget(self._build_card_scroll(), 1)
        root.addLayout(row)

        self.set_theme(theme)

    def _diag_header(self, title: str, icon_key: str) -> QWidget:
        w = QWidget()
        w.setObjectName("kbDiagHeader")
        h = QHBoxLayout(w)
        h.setContentsMargins(DT.S12, 10, DT.S12, 10)
        h.setSpacing(DT.S8)
        ic = QLabel()
        ic.setObjectName("kbDiagHeaderIcon")
        ic.setFixedSize(self._ICON_HEADER_PX, self._ICON_HEADER_PX)
        ic.setPixmap(app_icon(icon_key, self._theme).pixmap(self._ICON_HEADER_PX, self._ICON_HEADER_PX))
        self._header_icons.append((icon_key, ic))
        tit = QLabel(title)
        tit.setObjectName("kbDiagTitle")
        tit.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        h.addWidget(ic, 0, Qt.AlignmentFlag.AlignVCenter)
        h.addWidget(tit, 0, Qt.AlignmentFlag.AlignVCenter)
        h.addStretch(1)
        return w

    def _build_card_mouse(self) -> QFrame:
        card = QFrame()
        card.setObjectName("kbTestCard")
        card.setMinimumHeight(148)
        v = QVBoxLayout(card)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)
        v.addWidget(self._diag_header("Миша", "diag_mouse"))
        body = QWidget()
        body.setObjectName("kbDiagBody")
        vb = QVBoxLayout(body)
        vb.setContentsMargins(DT.S12, DT.S12, DT.S12, DT.S12)
        vb.setSpacing(0)
        hrow = QHBoxLayout()
        hrow.setSpacing(DT.S8)
        for name, pill in (
            ("ЛКМ", self._pill_l),
            ("ПКМ", self._pill_r),
            ("СКМ", self._pill_m),
        ):
            cell = QFrame()
            cell.setObjectName("mouseDiagCell")
            cv = QVBoxLayout(cell)
            cv.setContentsMargins(10, 10, 10, 10)
            cv.setSpacing(DT.S8)
            lb = QLabel(name)
            lb.setObjectName("mouseDiagKeyLbl")
            lb.setAlignment(Qt.AlignmentFlag.AlignCenter)
            cv.addWidget(lb, 0, Qt.AlignmentFlag.AlignHCenter)
            cv.addWidget(pill, 0, Qt.AlignmentFlag.AlignHCenter)
            hrow.addWidget(cell, 1)
        vb.addLayout(hrow)
        v.addWidget(body, 1)
        return card

    def _metric_box(self, dim: str, value: QLabel) -> QFrame:
        f = QFrame()
        f.setObjectName("mouseMetricBox")
        lay = QVBoxLayout(f)
        lay.setContentsMargins(10, 10, 10, 10)
        lay.setSpacing(4)
        d = QLabel(dim)
        d.setObjectName("mouseMetricDimLbl")
        value.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        lay.addWidget(d)
        lay.addWidget(value)
        return f

    def _build_card_coords(self) -> QFrame:
        card = QFrame()
        card.setObjectName("kbTestCard")
        card.setMinimumHeight(148)
        v = QVBoxLayout(card)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)
        v.addWidget(self._diag_header("Координати", "diag_coords"))
        body = QWidget()
        body.setObjectName("kbDiagBody")
        vb = QVBoxLayout(body)
        vb.setContentsMargins(DT.S12, DT.S12, DT.S12, DT.S12)
        hrow = QHBoxLayout()
        hrow.setSpacing(DT.S8)
        hrow.addWidget(self._metric_box("X", self._lbl_x), 1)
        hrow.addWidget(self._metric_box("Y", self._lbl_y), 1)
        vb.addLayout(hrow)
        v.addWidget(body, 1)
        return card

    def _build_card_scroll(self) -> QFrame:
        card = QFrame()
        card.setObjectName("kbTestCard")
        card.setMinimumHeight(148)
        v = QVBoxLayout(card)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)
        v.addWidget(self._diag_header("Скрол", "diag_scroll"))
        body = QWidget()
        body.setObjectName("kbDiagBody")
        vb = QVBoxLayout(body)
        vb.setContentsMargins(DT.S12, DT.S12, DT.S12, DT.S12)
        hrow = QHBoxLayout()
        hrow.setSpacing(DT.S8)
        hrow.addWidget(self._metric_box("dx", self._lbl_dx), 1)
        hrow.addWidget(self._metric_box("dy", self._lbl_dy), 1)
        vb.addLayout(hrow)
        v.addWidget(body, 1)
        return card

    def set_theme(self, theme: ThemeMode) -> None:
        self._theme = theme
        ss = mouse_test_panel_styles(theme)
        self.setStyleSheet(ss)
        px = self._ICON_HEADER_PX
        for key, lbl in self._header_icons:
            lbl.setPixmap(app_icon(key, theme).pixmap(px, px))
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
        self._lbl_x.setText(str(x))
        self._lbl_y.setText(str(y))

    def set_btn(self, name: str, down: bool) -> None:
        if name == "left":
            self._down["left"] = down
        elif name == "right":
            self._down["right"] = down
        else:
            self._down["middle"] = down
        self._apply_pills()

    def set_scroll(self, dx: int, dy: int) -> None:
        self._lbl_dx.setText(str(dx))
        self._lbl_dy.setText(str(dy))
