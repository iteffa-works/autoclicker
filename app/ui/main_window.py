"""Main window: tabs, status, tray, engines."""

from __future__ import annotations

import copy
import ctypes
import logging
import sys
from pathlib import Path

from PySide6.QtCore import QByteArray, QEvent, QTimer, Qt, Signal
from PySide6.QtGui import QCloseEvent, QIcon, QShowEvent
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QApplication,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.branding import WINDOW_TITLE
from app.core.autoclicker import AutoclickConfig, AutoclickerEngine, ClickMode, MouseButtonChoice
from app.core.sequence_autoclicker import SequenceAutoclickConfig, SequenceAutoclickerEngine
from app.core.bind_validator import validate_bindings
from app.core.macro_engine import MacroEngine, MacroPlayConfig, MacroRecordSession
from app.core.state import AppRunState, AutoclickState
from app.models.autoclick_sequence import AutoclickSequenceStep, AutoclickSequenceStepType, SequenceRepeatMode
from app.models.bindings import BindingsConfig, HotkeyChord
from app.models.macro import MacroDefinition, MacroEvent, MacroEventType, MacroSpeedMode
from app.models.recording_profile import RecordingProfile
from app.models.settings import HotkeyBackend, LogLevel, ThemeMode
from app.services.hotkey_service import ChordCaptureSession, HotkeyService
from app.services.win_hotkey_service import WM_HOTKEY, Win32HotkeyRegistry
from app.services.log_service import setup_logging
from app.services.settings_store import load_settings, save_settings
from app.services.sound_service import play_beep
from app.services.tray_service import TrayService
from app.ui.keyboard_test_hooks import KeyboardTestHooks
from app.ui.keyboard_test_ui import KeyboardTestPanel, MouseTestPanel
from app.ui.overlay_widget import ActivityOverlay
from app.ui.theme import stylesheet_for
from app.utils.json_io import read_json, write_json
from app.utils.paths import macros_dir
from pynput.mouse import Controller as MouseController


class MainWindow(QMainWindow):
    append_log = Signal(str)
    macro_done = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(WINDOW_TITLE)
        self.resize(980, 720)
        self._settings = load_settings()
        self._autoclick = AutoclickerEngine()
        self._seq_autoclick = SequenceAutoclickerEngine()
        self._macro_engine = MacroEngine()
        self._hotkeys = HotkeyService()
        self._win32_hotkeys = Win32HotkeyRegistry()
        self._force_exit = False
        self._record_session: MacroRecordSession | None = None
        self._current_macro: MacroDefinition | None = None
        self._capture: ChordCaptureSession | None = None
        self._capture_field: str | None = None
        self._kb_hooks = KeyboardTestHooks()
        self._mouse_ctrl = MouseController()
        self._overlay = ActivityOverlay()
        self._overlay.set_opacity(self._settings.overlay_opacity)
        self._overlay.set_stop_callback(self._emergency)
        self._overlay_poll = QTimer(self)
        self._overlay_poll.timeout.connect(self._update_overlay_visibility)
        self._overlay_poll.start(400)
        self._autosave_timer = QTimer(self)
        self._autosave_timer.setSingleShot(True)
        self._autosave_timer.timeout.connect(self._autosave_macro)

        self._setup_logging()
        self._build_ui()
        self._connect_signals()
        self._cursor_timer = QTimer(self)
        self._cursor_timer.timeout.connect(self._tick_cursor)
        self._cursor_timer.start(40)
        self._tray = TrayService(self)
        self.append_log.connect(self._append_log_slot)
        self.macro_done.connect(self._refresh_status)
        self._apply_theme()
        self._refresh_status()

    def setup_tray(self, icon: QIcon) -> None:
        self._tray.setup(
            on_show=self.bring_to_front,
            on_quit=self._quit_forced,
            tooltip=WINDOW_TITLE,
            icon=icon,
        )
        if self._settings.minimize_to_tray:
            self._tray.show()

    def _setup_logging(self) -> None:
        def ui_emit(msg: str) -> None:
            self.append_log.emit(msg)

        setup_logging(self._settings.log_level, self._settings.log_to_file, ui_emit)
        logging.getLogger(__name__).info("Запуск застосунку")

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        lay = QVBoxLayout(central)
        self._tabs = QTabWidget()
        lay.addWidget(self._tabs)
        self._tabs.addTab(self._build_autoclick_tab(), "Автоклікер")
        self._tabs.addTab(self._build_macro_tab(), "Макроси")
        self._tabs.addTab(self._build_binds_tab(), "Бинди")
        self._tabs.addTab(self._build_kb_tab(), "Тест клавіатури")
        self._tabs.addTab(self._build_settings_tab(), "Налаштування")
        self._tabs.addTab(self._build_logs_tab(), "Логи")
        self._tabs.currentChanged.connect(self._on_tab_changed)
        self._log_edit = QTextEdit()
        self._log_edit.setReadOnly(True)
        self._log_edit.setMaximumHeight(140)
        lay.addWidget(QLabel("Журнал подій"))
        lay.addWidget(self._log_edit)
        self._status = QLabel("Стан: зупинено")
        self._status.setObjectName("statusLabel")
        self._status.setProperty("state", "idle")
        self.statusBar().addPermanentWidget(self._status)

    def _connect_signals(self) -> None:
        self._kb_hooks.key_event.connect(self._on_test_key)
        self._kb_hooks.mouse_button.connect(self._on_test_mouse_btn)
        self._kb_hooks.mouse_position.connect(self._on_test_mouse_pos)
        self._kb_hooks.scroll_event.connect(self._on_test_scroll)

    def _macros_path(self) -> Path:
        if self._settings.macros_folder.strip():
            return Path(self._settings.macros_folder)
        return macros_dir()

    def _build_autoclick_tab(self) -> QWidget:
        w = QWidget()
        grid = QGridLayout(w)
        r = 0
        self._ac_button = QComboBox()
        self._ac_button.addItems(["ЛКМ", "ПКМ", "СКМ"])
        self._ac_mode = QComboBox()
        self._ac_mode.addItems(["Одинарний", "Подвійний", "Утримання"])
        self._ac_interval_ms = QDoubleSpinBox()
        self._ac_interval_ms.setRange(1, 600_000)
        self._ac_interval_ms.setValue(100)
        self._ac_cps = QDoubleSpinBox()
        self._ac_cps.setRange(0.1, 1000)
        self._ac_cps.setValue(5)
        self._ac_use_interval = QCheckBox("Використовувати інтервал (мс), інакше CPS")
        self._ac_use_interval.setChecked(True)
        self._ac_jitter = QDoubleSpinBox()
        self._ac_jitter.setRange(0, 5000)
        self._ac_jitter.setValue(5)
        self._ac_saved = QCheckBox("Клік по збережених X/Y")
        self._ac_sx = QSpinBox()
        self._ac_sx.setRange(-100_000, 100_000)
        self._ac_sy = QSpinBox()
        self._ac_sy.setRange(-100_000, 100_000)
        self._ac_sx.setValue(self._settings.saved_click_x)
        self._ac_sy.setValue(self._settings.saved_click_y)
        self._lbl_xy = QLabel("Курсор: —")
        grid.addWidget(QLabel("Кнопка"), r, 0)
        grid.addWidget(self._ac_button, r, 1)
        r += 1
        grid.addWidget(QLabel("Режим"), r, 0)
        grid.addWidget(self._ac_mode, r, 1)
        r += 1
        grid.addWidget(self._ac_use_interval, r, 0, 1, 2)
        r += 1
        grid.addWidget(QLabel("Інтервал (мс)"), r, 0)
        grid.addWidget(self._ac_interval_ms, r, 1)
        r += 1
        grid.addWidget(QLabel("CPS"), r, 0)
        grid.addWidget(self._ac_cps, r, 1)
        r += 1
        grid.addWidget(QLabel("Jitter (мс)"), r, 0)
        grid.addWidget(self._ac_jitter, r, 1)
        r += 1
        grid.addWidget(self._ac_saved, r, 0, 1, 2)
        r += 1
        grid.addWidget(QLabel("X"), r, 0)
        grid.addWidget(self._ac_sx, r, 1)
        r += 1
        grid.addWidget(QLabel("Y"), r, 0)
        grid.addWidget(self._ac_sy, r, 1)
        r += 1
        grid.addWidget(self._lbl_xy, r, 0, 1, 2)
        r += 1
        grid.addWidget(QLabel("Режим роботи"), r, 0)
        self._ac_work_mode = QComboBox()
        self._ac_work_mode.addItems(["Простий (миша)", "Послідовність", "Повтор клавіші"])
        self._ac_work_mode.currentIndexChanged.connect(self._on_ac_work_mode_changed)
        grid.addWidget(self._ac_work_mode, r, 1)
        r += 1
        self._ac_seq_group = QGroupBox("Кроки послідовності")
        sg = QVBoxLayout(self._ac_seq_group)
        self._ac_seq_table = QTableWidget(0, 3)
        self._ac_seq_table.setHorizontalHeaderLabels(["Тип", "Ключ / кнопка миші", "Затримка (мс)"])
        sg.addWidget(self._ac_seq_table)
        seq_btns = QHBoxLayout()
        self._ac_seq_add = QPushButton("Додати рядок")
        self._ac_seq_del = QPushButton("Видалити рядок")
        self._ac_seq_add.clicked.connect(self._ac_seq_add_row)
        self._ac_seq_del.clicked.connect(self._ac_seq_del_row)
        seq_btns.addWidget(self._ac_seq_add)
        seq_btns.addWidget(self._ac_seq_del)
        sg.addLayout(seq_btns)
        rep_row = QHBoxLayout()
        self._ac_seq_repeat_mode = QComboBox()
        self._ac_seq_repeat_mode.addItems(["Вся послідовність", "Один крок (за індексом)"])
        self._ac_seq_step_idx = QSpinBox()
        self._ac_seq_step_idx.setRange(0, 10_000)
        self._ac_seq_loop_inf = QCheckBox("Повторювати безкінечно")
        self._ac_seq_loop_inf.setChecked(True)
        rep_row.addWidget(QLabel("Повтор"))
        rep_row.addWidget(self._ac_seq_repeat_mode)
        rep_row.addWidget(QLabel("Індекс кроку"))
        rep_row.addWidget(self._ac_seq_step_idx)
        rep_row.addWidget(self._ac_seq_loop_inf)
        sg.addLayout(rep_row)
        grid.addWidget(self._ac_seq_group, r, 0, 1, 2)
        r += 1
        self._ac_key_repeat_label = QLabel("Клавіша для режиму «Повтор»")
        grid.addWidget(self._ac_key_repeat_label, r, 0)
        self._ac_key_repeat = QLineEdit()
        self._ac_key_repeat.setPlaceholderText("напр. e або space")
        grid.addWidget(self._ac_key_repeat, r, 1)
        r += 1
        row = QHBoxLayout()
        self._btn_start = QPushButton("Старт")
        self._btn_start.setObjectName("acStart")
        self._btn_pause = QPushButton("Пауза")
        self._btn_pause.setObjectName("acPause")
        self._btn_stop = QPushButton("Стоп")
        self._btn_stop.setObjectName("acStop")
        self._btn_reset = QPushButton("Скидання")
        self._btn_save_xy = QPushButton("Зберегти позицію курсора")
        row.addWidget(self._btn_start)
        row.addWidget(self._btn_pause)
        row.addWidget(self._btn_stop)
        row.addWidget(self._btn_reset)
        row.addWidget(self._btn_save_xy)
        grid.addLayout(row, r, 0, 1, 2)
        self._btn_start.clicked.connect(self._ac_start)
        self._btn_pause.clicked.connect(self._ac_pause)
        self._btn_stop.clicked.connect(self._ac_stop)
        self._btn_reset.clicked.connect(self._ac_reset)
        self._btn_save_xy.clicked.connect(self._ac_save_xy)
        self._load_ac_mode_ui()
        return w

    def _load_ac_mode_ui(self) -> None:
        s = self._settings
        mode_map = {"simple": 0, "sequence": 1, "key_repeat": 2}
        self._ac_work_mode.setCurrentIndex(mode_map.get(s.autoclick_work_mode, 0))
        self._ac_seq_repeat_mode.setCurrentIndex(0 if s.sequence_repeat_mode == SequenceRepeatMode.FULL.value else 1)
        self._ac_seq_step_idx.setValue(int(s.sequence_step_index))
        self._ac_seq_loop_inf.setChecked(bool(s.sequence_loop_infinite))
        self._ac_key_repeat.setText(s.autoclick_key_repeat_key)
        self._ac_seq_table.setRowCount(0)
        for row in s.autoclick_sequence_steps:
            try:
                st = AutoclickSequenceStep.from_dict(row)
            except Exception:
                continue
            self._ac_seq_add_row_from_step(st)
        self._on_ac_work_mode_changed()

    def _sync_ac_settings_from_ui(self) -> None:
        idx = self._ac_work_mode.currentIndex()
        modes = ("simple", "sequence", "key_repeat")
        self._settings.autoclick_work_mode = modes[idx] if idx < len(modes) else "simple"
        self._settings.sequence_repeat_mode = (
            SequenceRepeatMode.FULL.value
            if self._ac_seq_repeat_mode.currentIndex() == 0
            else SequenceRepeatMode.SINGLE_STEP.value
        )
        self._settings.sequence_step_index = int(self._ac_seq_step_idx.value())
        self._settings.sequence_loop_infinite = self._ac_seq_loop_inf.isChecked()
        self._settings.autoclick_key_repeat_key = self._ac_key_repeat.text().strip() or "e"
        steps: list[dict] = []
        for r in range(self._ac_seq_table.rowCount()):
            t0 = self._ac_seq_table.item(r, 0)
            t1 = self._ac_seq_table.item(r, 1)
            t2 = self._ac_seq_table.item(r, 2)
            ts = (t0.text().strip().lower() if t0 else "delay") if t0 else "delay"
            try:
                st = AutoclickSequenceStepType(ts)
            except ValueError:
                st = AutoclickSequenceStepType.DELAY
            val = t1.text().strip() if t1 else ""
            dms = float(t2.text().strip() if t2 else "0") if t2 else 0.0
            if st == AutoclickSequenceStepType.DELAY:
                step = AutoclickSequenceStep(type=st, delay_ms=dms)
            elif st == AutoclickSequenceStepType.MOUSE_CLICK:
                step = AutoclickSequenceStep(type=st, button=val or "left")
            else:
                step = AutoclickSequenceStep(type=st, key=val)
            steps.append(step.to_dict())
        self._settings.autoclick_sequence_steps = steps

    def _on_ac_work_mode_changed(self) -> None:
        idx = self._ac_work_mode.currentIndex()
        self._ac_seq_group.setVisible(idx == 1)
        self._ac_key_repeat.setVisible(idx == 2)
        self._ac_key_repeat_label.setVisible(idx == 2)
        self._sync_ac_settings_from_ui()

    def _ac_seq_add_row_from_step(self, st: AutoclickSequenceStep) -> None:
        r = self._ac_seq_table.rowCount()
        self._ac_seq_table.insertRow(r)
        self._ac_seq_table.setItem(r, 0, QTableWidgetItem(st.type.value))
        if st.type == AutoclickSequenceStepType.DELAY:
            self._ac_seq_table.setItem(r, 1, QTableWidgetItem(""))
            self._ac_seq_table.setItem(r, 2, QTableWidgetItem(str(st.delay_ms)))
        elif st.type == AutoclickSequenceStepType.MOUSE_CLICK:
            self._ac_seq_table.setItem(r, 1, QTableWidgetItem(st.button))
            self._ac_seq_table.setItem(r, 2, QTableWidgetItem("0"))
        else:
            self._ac_seq_table.setItem(r, 1, QTableWidgetItem(st.key))
            self._ac_seq_table.setItem(r, 2, QTableWidgetItem("0"))

    def _ac_seq_add_row(self) -> None:
        self._ac_seq_add_row_from_step(AutoclickSequenceStep(type=AutoclickSequenceStepType.DELAY, delay_ms=50.0))

    def _ac_seq_del_row(self) -> None:
        r = self._ac_seq_table.currentRow()
        if r >= 0:
            self._ac_seq_table.removeRow(r)

    def _ac_config_from_ui(self) -> AutoclickConfig:
        btn = [MouseButtonChoice.LEFT, MouseButtonChoice.RIGHT, MouseButtonChoice.MIDDLE][
            self._ac_button.currentIndex()
        ]
        mode = [ClickMode.SINGLE, ClickMode.DOUBLE, ClickMode.HOLD][self._ac_mode.currentIndex()]
        return AutoclickConfig(
            button=btn,
            mode=mode,
            use_interval_ms=self._ac_use_interval.isChecked(),
            interval_ms=float(self._ac_interval_ms.value()),
            cps=float(self._ac_cps.value()),
            jitter_ms=float(self._ac_jitter.value()),
            use_saved_position=self._ac_saved.isChecked(),
            saved_x=int(self._ac_sx.value()),
            saved_y=int(self._ac_sy.value()),
        )

    def _ac_effective_interval_ms(self) -> float:
        if self._ac_use_interval.isChecked():
            return float(self._ac_interval_ms.value())
        return 1000.0 / max(0.1, float(self._ac_cps.value()))

    def _active_autoclick_state(self) -> AutoclickState:
        if self._ac_work_mode.currentIndex() == 0:
            return self._autoclick.get_state()
        return self._seq_autoclick.get_state()

    def _ac_start(self) -> None:
        self._sync_ac_settings_from_ui()
        mode = self._settings.autoclick_work_mode
        if mode == "simple":
            self._seq_autoclick.stop()
            self._autoclick.set_config(self._ac_config_from_ui())
            self._autoclick.start()
        elif mode == "sequence":
            self._autoclick.stop()
            steps: list[AutoclickSequenceStep] = []
            for x in self._settings.autoclick_sequence_steps:
                try:
                    steps.append(AutoclickSequenceStep.from_dict(x if isinstance(x, dict) else {}))
                except Exception:
                    continue
            if not steps:
                QMessageBox.warning(self, "Автоклікер", "Додайте хоча б один крок послідовності.")
                return
            try:
                sr = SequenceRepeatMode(self._settings.sequence_repeat_mode)
            except ValueError:
                sr = SequenceRepeatMode.FULL
            cfg = SequenceAutoclickConfig(
                steps=steps,
                repeat_mode=sr,
                step_index=int(self._settings.sequence_step_index),
                loop_infinite=bool(self._settings.sequence_loop_infinite),
                interval_ms=float(self._ac_effective_interval_ms()),
                jitter_ms=float(self._ac_jitter.value()),
                key_repeat_token="",
            )
            self._seq_autoclick.start_sequence(cfg)
        else:
            self._autoclick.stop()
            tok = (self._settings.autoclick_key_repeat_key or "").strip()
            if not tok:
                QMessageBox.warning(self, "Автоклікер", "Вкажіть клавішу для повтору.")
                return
            self._seq_autoclick.start_key_repeat(
                tok,
                self._ac_effective_interval_ms(),
                float(self._ac_jitter.value()),
            )
        if self._settings.sound_on_start_stop:
            play_beep("start")
        self._refresh_status()
        logging.getLogger(__name__).info("Автоклікер: старт")

    def _ac_pause(self) -> None:
        if self._ac_work_mode.currentIndex() == 0:
            st = self._autoclick.get_state()
            if st == AutoclickState.PAUSED:
                self._autoclick.resume()
            else:
                self._autoclick.pause()
        else:
            st = self._seq_autoclick.get_state()
            if st == AutoclickState.PAUSED:
                self._seq_autoclick.resume()
            else:
                self._seq_autoclick.pause()
        self._refresh_status()

    def _ac_stop(self) -> None:
        self._autoclick.stop()
        self._seq_autoclick.stop()
        if self._settings.sound_on_start_stop:
            play_beep("stop")
        self._refresh_status()
        logging.getLogger(__name__).info("Автоклікер: стоп")

    def _ac_reset(self) -> None:
        self._ac_stop()
        self._ac_interval_ms.setValue(100)
        self._ac_cps.setValue(5)
        self._ac_jitter.setValue(5)

    def _ac_save_xy(self) -> None:
        p = self._mouse_ctrl.position
        self._ac_sx.setValue(int(p[0]))
        self._ac_sy.setValue(int(p[1]))
        self._settings.saved_click_x = int(p[0])
        self._settings.saved_click_y = int(p[1])
        save_settings(self._settings)

    def _tick_cursor(self) -> None:
        p = self._mouse_ctrl.position
        self._lbl_xy.setText(f"Курсор: X={int(p[0])} Y={int(p[1])}")
        self._settings.last_cursor_x = int(p[0])
        self._settings.last_cursor_y = int(p[1])

    def _build_macro_tab(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        prof_row = QHBoxLayout()
        prof_row.addWidget(QLabel("Профіль запису:"))
        self._macro_profile_combo = QComboBox()
        self._macro_profile_combo.currentIndexChanged.connect(self._on_macro_profile_changed)
        prof_row.addWidget(self._macro_profile_combo, 1)
        self._btn_prof_new = QPushButton("Новий профіль")
        self._btn_prof_save = QPushButton("Зберегти профіль")
        self._btn_prof_new.clicked.connect(self._macro_profile_new)
        self._btn_prof_save.clicked.connect(self._macro_profile_save)
        prof_row.addWidget(self._btn_prof_new)
        prof_row.addWidget(self._btn_prof_save)
        lay.addLayout(prof_row)
        flags = QHBoxLayout()
        self._chk_p_keys = QCheckBox("Клавіатура")
        self._chk_p_clicks = QCheckBox("Кліки миші")
        self._chk_p_move = QCheckBox("Рух миші")
        self._chk_p_scroll = QCheckBox("Скрол")
        self._chk_p_filter = QCheckBox("Фільтр биндів")
        for c in (self._chk_p_keys, self._chk_p_clicks, self._chk_p_move, self._chk_p_scroll, self._chk_p_filter):
            flags.addWidget(c)
        lay.addLayout(flags)
        top = QHBoxLayout()
        self._macro_list = QListWidget()
        self._macro_list.currentItemChanged.connect(self._macro_selected)
        self._btn_rec = QPushButton("Запис")
        self._btn_stop_rec = QPushButton("Стоп запису")
        self._btn_play = QPushButton("Відтворити")
        self._btn_stop_play = QPushButton("Стоп відтворення")
        self._btn_save_m = QPushButton("Зберегти як…")
        self._btn_load_m = QPushButton("Завантажити…")
        self._btn_del_m = QPushButton("Видалити")
        self._btn_rename = QPushButton("Перейменувати")
        top.addWidget(self._macro_list)
        col = QVBoxLayout()
        col.addWidget(self._btn_rec)
        col.addWidget(self._btn_stop_rec)
        col.addWidget(self._btn_play)
        col.addWidget(self._btn_stop_play)
        col.addWidget(self._btn_save_m)
        col.addWidget(self._btn_load_m)
        col.addWidget(self._btn_rename)
        col.addWidget(self._btn_del_m)
        top.addLayout(col)
        lay.addLayout(top)
        rep = QHBoxLayout()
        self._macro_repeat = QComboBox()
        self._macro_repeat.addItems(["1 раз", "N раз", "Безкінечно"])
        self._macro_n = QSpinBox()
        self._macro_n.setRange(1, 1_000_000)
        self._macro_n.setValue(3)
        self._macro_speed = QComboBox()
        self._macro_speed.addItems(["Оригінал", "Швидше", "Повільніше", "Множник"])
        self._macro_mult = QDoubleSpinBox()
        self._macro_mult.setRange(0.05, 20)
        self._macro_mult.setValue(1.0)
        rep.addWidget(QLabel("Повтор"))
        rep.addWidget(self._macro_repeat)
        rep.addWidget(QLabel("N"))
        rep.addWidget(self._macro_n)
        rep.addWidget(QLabel("Швидкість"))
        rep.addWidget(self._macro_speed)
        rep.addWidget(QLabel("Множник"))
        rep.addWidget(self._macro_mult)
        lay.addLayout(rep)
        self._macro_table = QTableWidget(0, 6)
        self._macro_table.setHorizontalHeaderLabels(
            ["Тип", "Клавіша/кнопка", "Затримка (мс)", "X", "Y", "Скрол"]
        )
        lay.addWidget(self._macro_table)
        self._btn_rec.clicked.connect(self._macro_start_rec)
        self._btn_stop_rec.clicked.connect(self._macro_stop_rec)
        self._btn_play.clicked.connect(self._macro_play)
        self._btn_stop_play.clicked.connect(self._macro_stop_play)
        self._btn_save_m.clicked.connect(self._macro_save)
        self._btn_load_m.clicked.connect(self._macro_load)
        self._btn_del_m.clicked.connect(self._macro_delete)
        self._btn_rename.clicked.connect(self._macro_rename)
        self._btn_apply_tbl = QPushButton("Застосувати зміни з таблиці")
        self._btn_apply_tbl.clicked.connect(self._macro_apply_table)
        lay.addWidget(self._btn_apply_tbl)
        self._macro_table.itemChanged.connect(lambda *_: self._schedule_autosave())
        self._refresh_macro_list()
        self._populate_recording_profiles_ui()
        return w

    def _refresh_macro_list(self) -> None:
        self._macro_list.clear()
        p = self._macros_path()
        p.mkdir(parents=True, exist_ok=True)
        for f in sorted(p.glob("*.json")):
            self._macro_list.addItem(f.name)

    def _populate_recording_profiles_ui(self) -> None:
        self._macro_profile_combo.blockSignals(True)
        self._macro_profile_combo.clear()
        for p in self._settings.recording_profiles:
            self._macro_profile_combo.addItem(p.name, p.id)
        idx = max(
            0,
            self._macro_profile_combo.findData(self._settings.active_recording_profile_id),
        )
        self._macro_profile_combo.setCurrentIndex(idx)
        self._macro_profile_combo.blockSignals(False)
        self._load_profile_flags_to_ui()

    def _current_profile_obj(self) -> RecordingProfile | None:
        pid = self._macro_profile_combo.currentData()
        for p in self._settings.recording_profiles:
            if p.id == pid:
                return p
        return self._settings.recording_profiles[0] if self._settings.recording_profiles else None

    def _load_profile_flags_to_ui(self) -> None:
        p = self._current_profile_obj()
        if not p:
            return
        self._chk_p_keys.setChecked(p.record_keyboard)
        self._chk_p_clicks.setChecked(p.record_mouse_clicks)
        self._chk_p_move.setChecked(p.record_mouse_move)
        self._chk_p_scroll.setChecked(p.record_scroll)
        self._chk_p_filter.setChecked(p.filter_binding_chords)

    def _read_profile_flags_from_ui(self, p: RecordingProfile) -> None:
        p.record_keyboard = self._chk_p_keys.isChecked()
        p.record_mouse_clicks = self._chk_p_clicks.isChecked()
        p.record_mouse_move = self._chk_p_move.isChecked()
        p.record_scroll = self._chk_p_scroll.isChecked()
        p.filter_binding_chords = self._chk_p_filter.isChecked()

    def _on_macro_profile_changed(self) -> None:
        pid = self._macro_profile_combo.currentData()
        if pid:
            self._settings.active_recording_profile_id = str(pid)
            save_settings(self._settings)
        self._load_profile_flags_to_ui()

    def _macro_profile_new(self) -> None:
        name, ok = QInputDialog.getText(self, "Новий профіль", "Назва профілю")
        if not ok or not name.strip():
            return
        p = RecordingProfile(name=name.strip())
        self._read_profile_flags_from_ui(p)
        self._settings.recording_profiles.append(p)
        self._settings.active_recording_profile_id = p.id
        save_settings(self._settings)
        self._populate_recording_profiles_ui()

    def _macro_profile_save(self) -> None:
        p = self._current_profile_obj()
        if not p:
            return
        self._read_profile_flags_from_ui(p)
        save_settings(self._settings)
        logging.getLogger(__name__).info("Профіль запису збережено: %s", p.name)

    def _active_recording_profile(self) -> RecordingProfile:
        p = self._current_profile_obj()
        if not p:
            p = RecordingProfile()
        out = copy.deepcopy(p)
        self._read_profile_flags_from_ui(out)
        return out

    def _schedule_autosave(self) -> None:
        if not self._settings.autosave_macros:
            return
        sec = max(2, int(self._settings.autosave_interval_sec))
        self._autosave_timer.start(sec * 1000)

    def _autosave_macro(self) -> None:
        if not self._current_macro or not self._current_macro.events:
            return
        try:
            p = self._macros_path()
            p.mkdir(parents=True, exist_ok=True)
            path = p / "autosave_last.json"
            write_json(path, self._current_macro.to_dict())
            logging.getLogger(__name__).debug("Автозбереження: %s", path)
        except Exception as e:
            logging.getLogger(__name__).warning("Автозбереження не вдалося: %s", e)

    def _macro_selected(self) -> None:
        it = self._macro_list.currentItem()
        if not it:
            return
        path = self._macros_path() / it.text()
        raw = read_json(path, {})
        try:
            self._current_macro = MacroDefinition.from_dict(raw)
            self._fill_macro_table(self._current_macro)
        except Exception as e:
            logging.getLogger(__name__).exception("Помилка читання макросу: %s", e)

    def _fill_macro_table(self, macro: MacroDefinition) -> None:
        self._macro_table.setRowCount(0)
        for ev in macro.events:
            r = self._macro_table.rowCount()
            self._macro_table.insertRow(r)
            self._macro_table.setItem(r, 0, QTableWidgetItem(ev.kind.value))
            self._macro_table.setItem(r, 1, QTableWidgetItem(ev.key or ""))
            self._macro_table.setItem(r, 2, QTableWidgetItem(str(ev.delay_ms)))
            self._macro_table.setItem(r, 3, QTableWidgetItem("" if ev.x is None else str(ev.x)))
            self._macro_table.setItem(r, 4, QTableWidgetItem("" if ev.y is None else str(ev.y)))
            scr = ""
            if ev.scroll_dx is not None or ev.scroll_dy is not None:
                scr = f"{ev.scroll_dx or 0},{ev.scroll_dy or 0}"
            self._macro_table.setItem(r, 5, QTableWidgetItem(scr))

    def _macro_start_rec(self) -> None:
        if self._record_session:
            return
        prof = self._active_recording_profile()
        self._record_session = MacroRecordSession(
            prof,
            self._settings.bindings if prof.filter_binding_chords else None,
        )
        self._record_session.start()
        logging.getLogger(__name__).info("Запис макросу: старт (%s)", prof.name)

    def _macro_stop_rec(self) -> None:
        if not self._record_session:
            return
        macro = self._record_session.stop()
        self._record_session = None
        self._current_macro = macro
        self._fill_macro_table(macro)
        self._schedule_autosave()
        logging.getLogger(__name__).info("Запис макросу: стоп, подій: %s", len(macro.events))

    def _macro_play_cfg(self) -> MacroPlayConfig:
        idx = self._macro_repeat.currentIndex()
        repeat = 1
        if idx == 1:
            repeat = int(self._macro_n.value())
        elif idx == 2:
            repeat = -1
        sm = [
            MacroSpeedMode.ORIGINAL,
            MacroSpeedMode.FAST,
            MacroSpeedMode.SLOW,
            MacroSpeedMode.CUSTOM,
        ][self._macro_speed.currentIndex()]
        return MacroPlayConfig(
            repeat_count=repeat,
            speed_mode=sm,
            speed_multiplier=float(self._macro_mult.value()),
        )

    def _macro_play(self) -> None:
        if not self._current_macro or not self._current_macro.events:
            QMessageBox.warning(self, "Макрос", "Немає подій для відтворення.")
            return
        cfg = self._macro_play_cfg()
        if cfg.repeat_count < 0 and not self._settings.infinite_loop_confirmed:
            ok = QMessageBox.question(
                self,
                "Підтвердження",
                "Увімкнути безкінечне відтворення? Це можна зупинити хоткеєм або кнопкою.",
            )
            if ok != QMessageBox.StandardButton.Yes:
                return
            self._settings.infinite_loop_confirmed = True
            save_settings(self._settings)
        self._macro_engine.play(
            self._current_macro,
            cfg,
            on_finished=lambda: self.macro_done.emit(),
        )
        logging.getLogger(__name__).info("Відтворення макросу")

    def _macro_stop_play(self) -> None:
        self._macro_engine.stop()

    def _macro_save(self) -> None:
        if not self._current_macro:
            QMessageBox.information(self, "Макрос", "Немає даних.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Зберегти макрос", str(self._macros_path()), "JSON (*.json)"
        )
        if not path:
            return
        write_json(Path(path), self._current_macro.to_dict())
        self._refresh_macro_list()
        logging.getLogger(__name__).info("Макрос збережено: %s", path)

    def _macro_load(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Завантажити", str(self._macros_path()), "JSON (*.json)")
        if not path:
            return
        raw = read_json(Path(path), {})
        self._current_macro = MacroDefinition.from_dict(raw)
        self._fill_macro_table(self._current_macro)

    def _macro_delete(self) -> None:
        it = self._macro_list.currentItem()
        if not it:
            return
        path = self._macros_path() / it.text()
        path.unlink(missing_ok=True)
        self._refresh_macro_list()

    def _macro_apply_table(self) -> None:
        if not self._current_macro:
            self._current_macro = MacroDefinition(name="macro")
        evs: list = []
        for r in range(self._macro_table.rowCount()):
            try:
                kind_s = self._macro_table.item(r, 0).text().strip()
                key_s = self._macro_table.item(r, 1).text().strip() if self._macro_table.item(r, 1) else ""
                delay_s = self._macro_table.item(r, 2).text().strip() if self._macro_table.item(r, 2) else "0"
                x_s = self._macro_table.item(r, 3).text().strip() if self._macro_table.item(r, 3) else ""
                y_s = self._macro_table.item(r, 4).text().strip() if self._macro_table.item(r, 4) else ""
                scr = self._macro_table.item(r, 5).text().strip() if self._macro_table.item(r, 5) else ""
                kind = MacroEventType(kind_s)
                delay = float(delay_s.replace(",", "."))
                ev = MacroEvent(
                    kind=kind,
                    delay_ms=delay,
                    key=key_s or None,
                )
                if x_s:
                    ev.x = float(x_s)
                if y_s:
                    ev.y = float(y_s)
                if scr and "," in scr:
                    a, b = scr.split(",", 1)
                    ev.scroll_dx = int(a.strip())
                    ev.scroll_dy = int(b.strip())
                evs.append(ev)
            except Exception as e:
                logging.getLogger(__name__).warning("Рядок %s таблиці: %s", r, e)
        self._current_macro.events = evs
        logging.getLogger(__name__).info("Таблицю макросу застосовано, подій: %s", len(evs))

    def _macro_rename(self) -> None:
        it = self._macro_list.currentItem()
        if not it:
            return
        old = it.text()
        new, ok = QInputDialog.getText(self, "Перейменувати", "Нове ім'я файлу", text=old)
        if not ok or not new:
            return
        p = self._macros_path()
        (p / old).rename(p / new)
        self._refresh_macro_list()

    def _build_binds_tab(self) -> QWidget:
        w = QWidget()
        lay = QFormLayout(w)
        self._bind_fields: dict[str, QLineEdit] = {}
        names = [
            ("toggle_autoclick", "Перемикач автоклікера"),
            ("pause_autoclick", "Пауза"),
            ("toggle_macro_play", "Перемикач відтворення макросу"),
            ("toggle_record_macro", "Запис макросу (перемикач)"),
            ("toggle_tray", "Згорнути / показати (трей)"),
            ("emergency_stop", "Аварійна зупинка"),
        ]
        for key, title in names:
            row = QHBoxLayout()
            le = QLineEdit()
            le.setReadOnly(True)
            b_listen = QPushButton("Слухати")
            b_clear = QPushButton("Очистити")
            b_listen.clicked.connect(lambda checked=False, k=key: self._bind_listen(k))
            b_clear.clicked.connect(lambda checked=False, k=key: self._bind_clear(k))
            row.addWidget(le, 1)
            row.addWidget(b_listen)
            row.addWidget(b_clear)
            lay.addRow(title, row)
            self._bind_fields[key] = le
        self._load_binds_to_ui()
        self._btn_apply_binds = QPushButton("Застосувати бинди")
        self._btn_apply_binds.clicked.connect(self._apply_binds_from_ui)
        lay.addRow(self._btn_apply_binds)
        return w

    def _chord_to_text(self, ch: HotkeyChord | None) -> str:
        return ch.display_string() if ch else ""

    def _load_binds_to_ui(self) -> None:
        b = self._settings.bindings
        mapping = {
            "toggle_autoclick": b.toggle_autoclick,
            "pause_autoclick": b.pause_autoclick,
            "toggle_macro_play": b.toggle_macro_play,
            "toggle_record_macro": b.toggle_record_macro,
            "toggle_tray": b.toggle_tray,
            "emergency_stop": b.emergency_stop,
        }
        for k, le in self._bind_fields.items():
            le.setText(self._chord_to_text(mapping[k]))

    def _read_binds_from_ui(self) -> BindingsConfig:
        def parse_field(name: str) -> HotkeyChord | None:
            t = self._bind_fields[name].text().strip()
            if not t:
                return None
            parts = [p.strip().lower() for p in t.split("+") if p.strip()]
            if not parts:
                return None
            mods = ("ctrl", "alt", "shift", "win")
            mlist = [p for p in parts if p in mods]
            rest = [p for p in parts if p not in mods]
            key = rest[-1] if rest else ""
            return HotkeyChord(tuple(sorted(set(mlist))), key)

        return BindingsConfig(
            toggle_autoclick=parse_field("toggle_autoclick"),
            pause_autoclick=parse_field("pause_autoclick"),
            toggle_macro_play=parse_field("toggle_macro_play"),
            toggle_record_macro=parse_field("toggle_record_macro"),
            toggle_tray=parse_field("toggle_tray"),
            emergency_stop=parse_field("emergency_stop"),
        )

    def _bind_listen(self, field: str) -> None:
        if self._capture:
            self._capture.stop()
        self._capture_field = field
        self._capture = ChordCaptureSession(self._on_chord_captured)
        self._capture.start()
        self.append_log.emit("Натисніть комбінацію…")

    def _on_chord_captured(self, ch: HotkeyChord) -> None:
        if self._capture_field and self._capture_field in self._bind_fields:
            self._bind_fields[self._capture_field].setText(ch.display_string())
        self._capture = None

    def _bind_clear(self, field: str) -> None:
        self._bind_fields[field].clear()

    def _apply_binds_from_ui(self) -> None:
        cfg = self._read_binds_from_ui()
        errs = validate_bindings(cfg)
        if errs:
            QMessageBox.warning(self, "Бинди", "\n".join(errs))
            return
        self._settings.bindings = cfg
        save_settings(self._settings)
        self._apply_hotkeys()
        logging.getLogger(__name__).info("Бинди оновлено")

    def _build_settings_tab(self) -> QWidget:
        w = QWidget()
        lay = QFormLayout(w)
        self._set_theme = QComboBox()
        self._set_theme.addItems(["Темна", "Світла"])
        self._set_theme.setCurrentIndex(0 if self._settings.theme == ThemeMode.DARK else 1)
        self._set_lang = QLineEdit(self._settings.ui_language)
        self._set_top = QCheckBox("Поверх усіх вікон")
        self._set_top.setChecked(self._settings.always_on_top)
        self._set_sound = QCheckBox("Звук старт/стоп")
        self._set_sound.setChecked(self._settings.sound_on_start_stop)
        self._set_tray = QCheckBox("Мінімізація в трей")
        self._set_tray.setChecked(self._settings.minimize_to_tray)
        self._set_close_tray = QCheckBox("Закривати в трей замість виходу (×)")
        self._set_close_tray.setChecked(self._settings.close_to_tray)
        self._set_hk_backend = QComboBox()
        self._set_hk_backend.addItems(["Авто (Win32, інакше pynput)", "Лише Win32", "Лише pynput"])
        self._set_hk_backend.setCurrentIndex(
            {HotkeyBackend.AUTO: 0, HotkeyBackend.WIN32: 1, HotkeyBackend.PYNPUT: 2}[
                self._settings.hotkey_backend
            ]
        )
        self._set_overlay_op = QDoubleSpinBox()
        self._set_overlay_op.setRange(0.3, 1.0)
        self._set_overlay_op.setSingleStep(0.05)
        self._set_overlay_op.setValue(self._settings.overlay_opacity)
        self._set_autosave = QCheckBox("Автозбереження макросу")
        self._set_autosave.setChecked(self._settings.autosave_macros)
        self._set_autosave_sec = QSpinBox()
        self._set_autosave_sec.setRange(5, 600)
        self._set_autosave_sec.setValue(self._settings.autosave_interval_sec)
        self._set_macros_dir = QLineEdit(self._settings.macros_folder)
        self._set_log_level = QComboBox()
        self._set_log_level.addItems([x.value for x in LogLevel])
        self._set_log_level.setCurrentText(self._settings.log_level.value)
        self._set_log_file = QCheckBox("Лог у файл")
        self._set_log_file.setChecked(self._settings.log_to_file)
        self._set_jitter = QDoubleSpinBox()
        self._set_jitter.setRange(0, 50)
        self._set_jitter.setValue(self._settings.jitter_percent)
        lay.addRow("Тема", self._set_theme)
        lay.addRow("Мова (заглушка)", self._set_lang)
        lay.addRow(self._set_top)
        lay.addRow(self._set_sound)
        lay.addRow(self._set_tray)
        lay.addRow(self._set_close_tray)
        lay.addRow("Глобальні клавіші", self._set_hk_backend)
        lay.addRow("Прозорість оверлею", self._set_overlay_op)
        lay.addRow(self._set_autosave)
        lay.addRow("Інтервал автозбереження (с)", self._set_autosave_sec)
        lay.addRow("Папка макросів (порожньо = типова)", self._set_macros_dir)
        lay.addRow("Рівень логу", self._set_log_level)
        lay.addRow(self._set_log_file)
        lay.addRow("Jitter % (загальний)", self._set_jitter)
        btn = QPushButton("Зберегти налаштування")
        btn.clicked.connect(self._save_settings_ui)
        lay.addRow(btn)
        return w

    def _save_settings_ui(self) -> None:
        self._settings.theme = ThemeMode.DARK if self._set_theme.currentIndex() == 0 else ThemeMode.LIGHT
        self._settings.ui_language = self._set_lang.text().strip() or "uk"
        self._settings.always_on_top = self._set_top.isChecked()
        self._settings.sound_on_start_stop = self._set_sound.isChecked()
        self._settings.minimize_to_tray = self._set_tray.isChecked()
        self._settings.close_to_tray = self._set_close_tray.isChecked()
        self._settings.hotkey_backend = (
            HotkeyBackend.AUTO,
            HotkeyBackend.WIN32,
            HotkeyBackend.PYNPUT,
        )[self._set_hk_backend.currentIndex()]
        self._settings.overlay_opacity = float(self._set_overlay_op.value())
        self._settings.autosave_macros = self._set_autosave.isChecked()
        self._settings.autosave_interval_sec = int(self._set_autosave_sec.value())
        self._settings.macros_folder = self._set_macros_dir.text().strip()
        self._settings.log_level = LogLevel(self._set_log_level.currentText())
        self._settings.log_to_file = self._set_log_file.isChecked()
        self._settings.jitter_percent = float(self._set_jitter.value())
        save_settings(self._settings)
        self._apply_theme()
        if hasattr(self, "_kb_panel"):
            self._kb_panel.set_theme(self._settings.theme)
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, self._settings.always_on_top)
        self.show()
        setup_logging(self._settings.log_level, self._settings.log_to_file, lambda m: self.append_log.emit(m))
        if self._settings.minimize_to_tray:
            self._tray.show()
        else:
            self._tray.hide()
        self._overlay.set_opacity(self._settings.overlay_opacity)
        self._apply_hotkeys()
        logging.getLogger(__name__).info("Налаштування збережено")

    def _build_logs_tab(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.addWidget(QLabel("Повний лог у нижній панелі головного вікна."))
        return w

    def _build_kb_tab(self) -> QWidget:
        w = QWidget()
        lay = QHBoxLayout(w)
        self._kb_panel = KeyboardTestPanel(self._settings.theme)
        self._mouse_panel = MouseTestPanel()
        lay.addWidget(self._kb_panel, 2)
        lay.addWidget(self._mouse_panel, 1)
        return w

    def _on_tab_changed(self, idx: int) -> None:
        name = self._tabs.tabText(idx)
        if name == "Тест клавіатури":
            self._kb_hooks.start()
        else:
            self._kb_hooks.stop()

    def _on_test_key(self, name: str, down: bool) -> None:
        kid = self._kb_panel.normalize(name)
        if kid:
            self._kb_panel.set_key_active(kid, down)

    def _on_test_mouse_btn(self, name: str, down: bool) -> None:
        self._mouse_panel.set_btn(name, down)

    def _on_test_mouse_pos(self, x: int, y: int) -> None:
        self._mouse_panel.set_pos(x, y)

    def _on_test_scroll(self, dx: int, dy: int) -> None:
        self._mouse_panel.set_scroll(dx, dy)

    def _append_log_slot(self, msg: str) -> None:
        self._log_edit.append(msg)

    def _apply_theme(self) -> None:
        self.setStyleSheet(stylesheet_for(self._settings.theme))
        if hasattr(self, "_kb_panel"):
            self._kb_panel.set_theme(self._settings.theme)

    def _is_busy(self) -> bool:
        if self._macro_engine.get_state() == AppRunState.PLAYING_MACRO:
            return True
        return self._active_autoclick_state() != AutoclickState.STOPPED

    def _update_overlay_visibility(self) -> None:
        self._overlay.set_opacity(self._settings.overlay_opacity)
        if not self._settings.minimize_to_tray or self.isVisible() or not self._is_busy():
            self._overlay.hide()
            return
        b = self._settings.bindings
        lines: list[str] = []
        if b.toggle_autoclick:
            lines.append(f"Перемикач: {b.toggle_autoclick.display_string()}")
        if b.pause_autoclick:
            lines.append(f"Пауза: {b.pause_autoclick.display_string()}")
        if b.emergency_stop:
            lines.append(f"Аварія: {b.emergency_stop.display_string()}")
        title = "Активно (автоклікер або макрос)"
        self._overlay.set_text(title, "\n".join(lines) if lines else "Бинди не задані")
        self._overlay.show()
        self._overlay.raise_()

    def _refresh_status(self) -> None:
        self._status.setProperty("state", "idle")
        self._btn_start.setProperty("state", "")
        self._btn_pause.setProperty("state", "")
        self._btn_stop.setProperty("state", "")
        st = self._active_autoclick_state()
        ms = self._macro_engine.get_state()
        if ms == AppRunState.PLAYING_MACRO:
            self._status.setText("Стан: відтворення макросу")
            self._status.setProperty("state", "macro")
        elif st == AutoclickState.RUNNING:
            self._status.setText("Стан: автоклікер активний")
            self._status.setProperty("state", "running")
            self._btn_start.setProperty("state", "on")
            self._btn_stop.setProperty("state", "danger")
        elif st == AutoclickState.PAUSED:
            self._status.setText("Стан: пауза")
            self._status.setProperty("state", "paused")
            self._btn_pause.setProperty("state", "paused")
            self._btn_stop.setProperty("state", "danger")
        else:
            self._status.setText("Стан: зупинено")
        for w in (self._status, self._btn_start, self._btn_pause, self._btn_stop):
            w.style().unpolish(w)
            w.style().polish(w)
        self._update_overlay_visibility()

    def _apply_hotkeys(self) -> None:
        def wrap(fn):
            def inner() -> None:
                try:
                    fn()
                except Exception:
                    logging.getLogger(__name__).exception("Hotkey callback")
            return inner

        cb = {
            "toggle_autoclick": wrap(self._hk_toggle_ac),
            "pause_autoclick": wrap(self._hk_pause_ac),
            "toggle_macro_play": wrap(self._hk_toggle_macro_play),
            "toggle_record_macro": wrap(self._hk_toggle_rec),
            "toggle_tray": wrap(self._hk_toggle_tray),
            "emergency_stop": wrap(self._emergency),
        }
        self._hotkeys.stop()
        self._win32_hotkeys.stop()
        be = self._settings.hotkey_backend
        if sys.platform == "win32" and self.isVisible():
            try:
                hwnd = int(self.winId())
            except Exception:
                hwnd = 0
            if hwnd and be in (HotkeyBackend.AUTO, HotkeyBackend.WIN32):
                ok, errs = self._win32_hotkeys.register_all(hwnd, self._settings.bindings, cb)
                if ok:
                    logging.getLogger(__name__).info("Глобальні клавіші: Win32 RegisterHotKey")
                    return
                for msg in errs:
                    logging.getLogger(__name__).warning("%s", msg)
                if be == HotkeyBackend.WIN32:
                    logging.getLogger(__name__).error("Win32 не вдалося; перевірте бинди")
                    return
        self._hotkeys.start(self._settings.bindings, cb)
        logging.getLogger(__name__).info("Глобальні клавіші: pynput")

    def _hk_toggle_ac(self) -> None:
        if self._active_autoclick_state() in (AutoclickState.RUNNING, AutoclickState.PAUSED):
            self._ac_stop()
        else:
            self._ac_start()

    def _hk_pause_ac(self) -> None:
        self._ac_pause()

    def _hk_toggle_macro_play(self) -> None:
        if self._macro_engine.get_state() == AppRunState.PLAYING_MACRO:
            self._macro_stop_play()
        else:
            self._macro_play()

    def _hk_toggle_rec(self) -> None:
        if self._record_session:
            self._macro_stop_rec()
        else:
            self._macro_start_rec()

    def _hk_toggle_tray(self) -> None:
        if not self._settings.minimize_to_tray:
            return
        if self.isVisible():
            self.hide()
            self._tray.ensure_visible()
        else:
            self.bring_to_front()

    def _emergency(self) -> None:
        self._autoclick.stop()
        self._seq_autoclick.stop()
        self._macro_engine.stop()
        if self._record_session:
            self._macro_stop_rec()
        self._refresh_status()
        logging.getLogger(__name__).warning("Аварійна зупинка")

    def bring_to_front(self) -> None:
        self.showNormal()
        self.raise_()
        self.activateWindow()
        self._update_overlay_visibility()

    def _quit_forced(self) -> None:
        self._force_exit = True
        self.close()

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        if self.isVisible():
            self._apply_hotkeys()

    def nativeEvent(self, eventType, message):
        if sys.platform == "win32":
            try:
                et = QByteArray(eventType)
                if et.startsWith(b"windows"):
                    from ctypes import wintypes

                    class POINT(ctypes.Structure):
                        _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

                    class MSG(ctypes.Structure):
                        _fields_ = [
                            ("hwnd", wintypes.HWND),
                            ("message", wintypes.UINT),
                            ("wParam", wintypes.WPARAM),
                            ("lParam", wintypes.LPARAM),
                            ("time", wintypes.DWORD),
                            ("pt", POINT),
                        ]

                    msg = ctypes.cast(int(message), ctypes.POINTER(MSG)).contents
                    if int(msg.message) == WM_HOTKEY:
                        self._win32_hotkeys.dispatch(int(msg.wParam))
                        return True, 0
            except Exception:
                logging.getLogger(__name__).debug("nativeEvent", exc_info=True)
        return super().nativeEvent(eventType, message)

    def changeEvent(self, event: QEvent) -> None:
        if event.type() == QEvent.Type.WindowStateChange and self._settings.minimize_to_tray:
            if self.isMinimized():
                self.hide()
                self._tray.ensure_visible()
                event.accept()
                self._update_overlay_visibility()
                return
        super().changeEvent(event)

    def closeEvent(self, event: QCloseEvent) -> None:
        if self._settings.close_to_tray and not self._force_exit:
            event.ignore()
            self.hide()
            self._tray.ensure_visible()
            self._update_overlay_visibility()
            return
        self._sync_ac_settings_from_ui()
        self._hotkeys.stop()
        self._win32_hotkeys.stop()
        self._autoclick.stop()
        self._seq_autoclick.stop()
        self._macro_engine.stop()
        self._kb_hooks.stop()
        self._overlay.hide()
        if self._capture:
            self._capture.stop()
        save_settings(self._settings)
        event.accept()
        QApplication.quit()
