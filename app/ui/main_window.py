"""Main window: tabs, status, tray, engines."""

from __future__ import annotations

import copy
import ctypes
import logging
import sys
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QByteArray, QEvent, QSize, QTimer, Qt, QUrl, Signal
from PySide6.QtGui import QColor, QCloseEvent, QDesktopServices, QIcon, QPainter, QPen, QPixmap, QShowEvent
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QCheckBox,
    QComboBox as QtQComboBox,
    QDoubleSpinBox as QtQDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QHeaderView,
    QScrollArea,
    QSizePolicy,
    QSpinBox as QtQSpinBox,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from app.branding import (
    APP_VERSION,
    BRAND_TELEGRAM_URL,
    BRAND_WHATSAPP_URL,
    STUDIO_EMAIL,
    STUDIO_URL,
    format_window_title,
)
from app.i18n import normalize_ui_language, tr
from app.core.autoclicker import AutoclickConfig, ClickMode, MouseButtonChoice
from app.core.bind_validator import validate_bindings
from app.core.clicker_facade import UnifiedClickerEngine
from app.core.event_bus import AppEvent, EventBus, EventType
from app.core.input_engine import InputEngine
from app.core.macro_engine import MacroEngine, MacroPlayConfig, MacroRecordSession
from app.core.sequence_autoclicker import SequenceAutoclickConfig
from app.core.state import AppRunState, AutoclickState
from app.models.autoclick_sequence import AutoclickSequenceStep, AutoclickSequenceStepType, SequenceRepeatMode
from app.models.bindings import BindingsConfig, HotkeyChord
from app.models.macro import MacroDefinition, MacroEvent, MacroEventType, MacroSpeedMode
from app.models.recording_profile import RecordingProfile
from app.models.settings import HotkeyBackend, LogLevel, ThemeMode
from app.services.hotkey_service import ChordCaptureSession
from app.services.hotkey_manager import HotkeyManager
from app.services.logging_service import LoggingService
from app.services.settings_store import load_settings, save_settings
from app.services.sound_service import play_beep
from app.services.tray_service import TrayService
from app.ui.app_icons import NAV_ICON_KEYS, app_icon, icon_kind_size
from app.ui.keyboard_test_hooks import KeyboardTestHooks
from app.ui.keyboard_test_ui import KeyboardTestPanel, MouseTestPanel
from app.ui.overlay_widget import ActivityOverlay
from app.ui.themed_checkbox import ThemedCheckBox as QCheckBox
from app.ui.themed_checkbox import sync_themed_checkboxes
from app.ui.design_tokens import (
    AC_COL_COMBO_MAX_W,
    AC_COL_FIELD_MAX_W,
    AC_GRID_LABEL_W,
    BINDS_LABEL_MIN_W,
    CONTENT_PADDING,
    FORM_COMBO_MAX_W,
    FORM_FIELD_MAX_W,
    FORM_LABEL_MIN_W,
    SETTINGS_CONTENT_MAX_W,
    SETTINGS_GRID_BREAKPOINT_W,
    SETTINGS_INLINE_LABEL_W,
    SETTINGS_NUM_FIELD_MAX_W,
    MACRO_SIDE_BTN_MIN_W,
    S16,
    S24,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
)
from app.presenter import AppPresenter
from app.ui.tabs.logs_tab import build_logs_tab
from app.ui.theme import stylesheet_for
from app.utils.json_io import read_json, write_json
from app.utils.paths import assets_dir, macros_dir
from app.services.win_hotkey_service import WM_HOTKEY

# QSS не задає gap між іконкою та підписом у QPushButton — тонкий пробіл (було 3× en — забагато).
_ICON_TEXT_GAP = "\u2009"

_NAV_KEYS = (
    "nav.autoclick",
    "nav.macros",
    "nav.keyboard_test",
    "nav.settings",
    "nav.logs",
)
_NAV_INDEX_KEYBOARD_TEST = 2


def _chevron_pixmap(direction: str, color: QColor) -> QPixmap:
    pm = QPixmap(12, 8)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    pen = QPen(color, 1.7, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    if direction == "down":
        p.drawLine(1, 2, 6, 6)
        p.drawLine(6, 6, 11, 2)
    else:
        p.drawLine(1, 6, 6, 2)
        p.drawLine(6, 2, 11, 6)
    p.end()
    return pm


class _ChevronOverlayMixin:
    def _overlay_color(self) -> QColor:
        color = self.palette().color(self.foregroundRole())
        if not color.isValid():
            color = QColor("#CBD5E1")
        color.setAlpha(235 if self.isEnabled() else 120)
        return color

    def _refresh_overlay_icons(self) -> None:
        pass

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
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._arrow_overlay = QLabel(self)
        self._arrow_overlay.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self._arrow_overlay.setFixedSize(12, 8)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        x = self.width() - 22
        y = (self.height() - self._arrow_overlay.height()) // 2
        self._arrow_overlay.move(max(0, x), max(0, y))
        self._arrow_overlay.raise_()

    def _refresh_overlay_icons(self) -> None:
        self._arrow_overlay.setPixmap(_chevron_pixmap("down", self._overlay_color()))
        self._arrow_overlay.raise_()


class _SpinChevronMixin(_ChevronOverlayMixin):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._up_overlay = QLabel(self)
        self._down_overlay = QLabel(self)
        for overlay in (self._up_overlay, self._down_overlay):
            overlay.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
            overlay.setFixedSize(12, 8)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        btn_w = 22 if self.height() <= 34 else 28
        x = self.width() - btn_w + (btn_w - self._up_overlay.width()) // 2
        self._up_overlay.move(max(0, x), 4)
        self._down_overlay.move(max(0, x), self.height() - self._down_overlay.height() - 4)
        self._up_overlay.raise_()
        self._down_overlay.raise_()

    def _refresh_overlay_icons(self) -> None:
        color = self._overlay_color()
        self._up_overlay.setPixmap(_chevron_pixmap("up", color))
        self._down_overlay.setPixmap(_chevron_pixmap("down", color))
        self._up_overlay.raise_()
        self._down_overlay.raise_()


class QSpinBox(_SpinChevronMixin, QtQSpinBox):
    pass


class QDoubleSpinBox(_SpinChevronMixin, QtQDoubleSpinBox):
    pass


class _ResponsiveSettingsBody(QWidget):
    """Дві колонки карток налаштувань; при вузькій ширині — одна колонка. Бинди на всю ширину знизу."""

    __slots__ = ("_binds", "_bp", "_c1", "_c2", "_c3", "_c4", "_grid", "_wide")

    def __init__(
        self,
        card_general: QFrame,
        card_behavior: QFrame,
        card_macro: QFrame,
        card_log: QFrame,
        binds: QFrame,
        *,
        breakpoint_w: int,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._c1 = card_general
        self._c2 = card_behavior
        self._c3 = card_macro
        self._c4 = card_log
        self._binds = binds
        self._bp = breakpoint_w
        self._wide = True
        self._grid = QGridLayout(self)
        self._grid.setContentsMargins(0, 0, 0, 0)
        self._grid.setHorizontalSpacing(11)
        self._grid.setVerticalSpacing(11)
        self.setMaximumWidth(SETTINGS_CONTENT_MAX_W)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self._apply_layout()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        w = self.width()
        if w <= 0:
            return
        wide = w >= self._bp
        if wide != self._wide:
            self._wide = wide
            self._apply_layout()

    def _clear_grid(self) -> None:
        while self._grid.count():
            item = self._grid.takeAt(0)
            if item is None:
                break

    def _apply_layout(self) -> None:
        self._clear_grid()
        top = Qt.AlignmentFlag.AlignTop
        if self._wide:
            self._grid.setColumnStretch(0, 1)
            self._grid.setColumnStretch(1, 1)
            self._grid.addWidget(self._c1, 0, 0, 1, 1, top)
            self._grid.addWidget(self._c2, 0, 1, 1, 1, top)
            self._grid.addWidget(self._c3, 1, 0, 1, 1, top)
            self._grid.addWidget(self._c4, 1, 1, 1, 1, top)
            self._grid.addWidget(self._binds, 2, 0, 1, 2, top)
        else:
            self._grid.setColumnStretch(0, 1)
            self._grid.setColumnStretch(1, 0)
            self._grid.addWidget(self._c1, 0, 0, 1, 2, top)
            self._grid.addWidget(self._c2, 1, 0, 1, 2, top)
            self._grid.addWidget(self._c3, 2, 0, 1, 2, top)
            self._grid.addWidget(self._c4, 3, 0, 1, 2, top)
            self._grid.addWidget(self._binds, 4, 0, 1, 2, top)


class MainWindow(QMainWindow):
    append_log = Signal(str)
    macro_done = Signal()
    status_refresh = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.setFixedSize(WINDOW_WIDTH, WINDOW_HEIGHT)
        self._apply_no_maximize_button()
        self._settings = load_settings()
        self._event_bus = EventBus()
        self._icon_targets: list[tuple[QWidget, str, str]] = []
        self._brand_social_tooltips: list[tuple[QToolButton, str]] = []
        self._clicker = UnifiedClickerEngine(self._event_bus)
        self._macro_engine = MacroEngine(self._event_bus)
        self._hotkey_manager = HotkeyManager()
        self._input = InputEngine()
        self._logging_service = LoggingService()
        self._presenter = AppPresenter(self._event_bus, self._logging_service)
        self._force_exit = False
        self._record_session: MacroRecordSession | None = None
        self._current_macro: MacroDefinition | None = None
        self._capture: ChordCaptureSession | None = None
        self._capture_field: str | None = None
        self._kb_hooks = KeyboardTestHooks()
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
        self._create_autoclick_buttons()
        self._build_ui()
        self._connect_signals()
        self._cursor_timer = QTimer(self)
        self._cursor_timer.timeout.connect(self._tick_cursor)
        self._cursor_timer.start(40)
        self._tray = TrayService(self)
        self.append_log.connect(self._append_log_slot)
        self.macro_done.connect(self._refresh_status)
        self.status_refresh.connect(self._refresh_status)
        self._wire_engine_events()
        self._apply_theme()
        self._refresh_status()

    def _apply_no_maximize_button(self) -> None:
        self.setWindowFlag(Qt.WindowType.WindowMaximizeButtonHint, False)

    def setup_tray(self, icon: QIcon) -> None:
        _L = normalize_ui_language(self._settings.ui_language)
        _tip = format_window_title(tr(_L, "app.product_subtitle"))
        self._tray.setup(
            on_show=self.bring_to_front,
            on_quit=self._quit_forced,
            tooltip=_tip,
            icon=icon,
        )
        if self._settings.minimize_to_tray:
            self._tray.show()

    def _wire_engine_events(self) -> None:
        def _on_bus(_: AppEvent) -> None:
            self.status_refresh.emit()

        for kind in (
            EventType.CLICK_STARTED,
            EventType.CLICK_STOPPED,
            EventType.CLICK_PAUSED,
            EventType.CLICK_RESUMED,
            EventType.MACRO_PLAY_STARTED,
            EventType.MACRO_PLAY_STOPPED,
        ):
            self._event_bus.subscribe(kind, _on_bus)

    def _setup_logging(self) -> None:
        def ui_emit(msg: str) -> None:
            self.append_log.emit(msg)

        self._logging_service.configure(self._settings.log_level, self._settings.log_to_file, ui_emit)
        logging.getLogger(__name__).info("Запуск застосунку")

    def _create_autoclick_buttons(self) -> None:
        self._btn_start = QPushButton("Старт")
        self._btn_start.setObjectName("acStart")
        self._btn_pause = QPushButton("Пауза")
        self._btn_pause.setObjectName("acPause")
        self._btn_stop = QPushButton("Стоп")
        self._btn_stop.setObjectName("acStop")
        self._btn_reset = QPushButton("Скидання")
        self._btn_save_xy = QPushButton("Зберегти позицію курсора")
        self._btn_start.clicked.connect(self._ac_start)
        self._btn_pause.clicked.connect(self._ac_pause)
        self._btn_stop.clicked.connect(self._ac_stop)
        self._btn_reset.clicked.connect(self._ac_reset)
        self._btn_save_xy.clicked.connect(self._ac_save_xy)
        for _b in (self._btn_start, self._btn_pause, self._btn_stop):
            _b.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        self._register_icon_widget(self._btn_start, "action_play", "toolbar")
        self._register_icon_widget(self._btn_pause, "action_pause", "toolbar")
        self._register_icon_widget(self._btn_stop, "action_stop", "toolbar")
        self._register_icon_widget(self._btn_reset, "action_undo", "toolbar")
        self._register_icon_widget(self._btn_save_xy, "action_crosshairs", "toolbar")

    def _register_icon_widget(self, w: QWidget, key: str, kind: str) -> None:
        self._icon_targets.append((w, key, kind))

    def _refresh_ui_icons(self) -> None:
        t = self._settings.theme
        for w, key, kind in self._icon_targets:
            ic = app_icon(key, t)
            sz = icon_kind_size(kind)
            qsz = QSize(sz, sz)
            if isinstance(w, QPushButton):
                w.setIcon(ic)
                w.setIconSize(qsz)
            elif isinstance(w, QToolButton):
                w.setIcon(ic)
                w.setIconSize(qsz)
            elif isinstance(w, QLabel):
                w.setPixmap(ic.pixmap(qsz))

    def _create_header_actions_stack(self) -> QStackedWidget:
        """Права зона хедера: залежить від активної вкладки (див. _on_nav_changed)."""
        st = QStackedWidget()
        st.setObjectName("headerActionsStack")

        w_ac = QWidget()
        la = QHBoxLayout(w_ac)
        la.setContentsMargins(0, 0, 0, 0)
        la.setSpacing(4)
        la.addStretch(1)
        la.addWidget(self._btn_start)
        la.addWidget(self._btn_pause)
        la.addWidget(self._btn_stop)
        st.addWidget(w_ac)

        w_macro = QWidget()
        lm = QHBoxLayout(w_macro)
        lm.setContentsMargins(0, 0, 0, 0)
        lm.setSpacing(4)
        self._btn_macro_play = QPushButton(_ICON_TEXT_GAP + "Відтворити")
        self._btn_macro_rec = QPushButton(_ICON_TEXT_GAP + "Запис")
        self._btn_macro_stop_rec = QPushButton(_ICON_TEXT_GAP + "Стоп запису")
        self._btn_macro_stop_play = QPushButton(_ICON_TEXT_GAP + "Стоп відтворення")
        for _mb in (
            self._btn_macro_play,
            self._btn_macro_rec,
            self._btn_macro_stop_rec,
            self._btn_macro_stop_play,
        ):
            _mb.setObjectName("headerActionButton")
            _mb.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        self._btn_macro_play.clicked.connect(self._macro_play)
        self._btn_macro_rec.clicked.connect(self._macro_start_rec)
        self._btn_macro_stop_rec.clicked.connect(self._macro_stop_rec)
        self._btn_macro_stop_play.clicked.connect(self._macro_stop_play)
        self._register_icon_widget(self._btn_macro_play, "macro_play", "toolbar")
        self._register_icon_widget(self._btn_macro_rec, "macro_record", "toolbar")
        self._register_icon_widget(self._btn_macro_stop_rec, "macro_stop_rec", "toolbar")
        self._register_icon_widget(self._btn_macro_stop_play, "macro_stop_play", "toolbar")
        lm.addStretch(1)
        lm.addWidget(self._btn_macro_play)
        lm.addWidget(self._btn_macro_rec)
        lm.addWidget(self._btn_macro_stop_rec)
        lm.addWidget(self._btn_macro_stop_play)
        st.addWidget(w_macro)
        # Єдині екземпляри кнопок запису/відтворення (вкладка макросів не дублює)
        self._btn_play = self._btn_macro_play
        self._btn_rec = self._btn_macro_rec
        self._btn_stop_play = self._btn_macro_stop_play
        self._btn_stop_rec = self._btn_macro_stop_rec

        st.addWidget(QWidget())

        w_set = QWidget()
        ls = QHBoxLayout(w_set)
        ls.setContentsMargins(0, 0, 0, 0)
        self._btn_save_settings = QPushButton(_ICON_TEXT_GAP + "Зберегти налаштування")
        self._btn_save_settings.setObjectName("headerPrimaryButton")
        self._btn_save_settings.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        self._btn_save_settings.clicked.connect(self._save_settings_ui)
        self._register_icon_widget(self._btn_save_settings, "action_save", "toolbar")
        ls.addWidget(self._btn_save_settings, 0, Qt.AlignmentFlag.AlignRight)
        st.addWidget(w_set)

        st.addWidget(QWidget())
        st.setCurrentIndex(0)
        return st

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._log_edit = QTextEdit()
        self._log_edit.setReadOnly(True)
        self._log_edit.setObjectName("eventLog")
        self._log_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self._header_actions_stack = self._create_header_actions_stack()

        self._stack = QStackedWidget()
        self._stack.setObjectName("mainStack")
        self._stack.addWidget(self._build_autoclick_tab())
        self._stack.addWidget(self._build_macro_tab())
        self._stack.addWidget(self._build_kb_tab())
        self._stack.addWidget(self._build_settings_tab())
        self._stack.addWidget(build_logs_tab(self))

        header = QWidget()
        header.setObjectName("headerBar")
        head_lay = QHBoxLayout(header)
        head_lay.setContentsMargins(S16, 6, S16, 6)
        head_lay.setSpacing(8)
        nav_wrap = QWidget()
        nav_lay = QHBoxLayout(nav_wrap)
        nav_lay.setContentsMargins(0, 0, 0, 0)
        nav_lay.setSpacing(4)
        self._nav_group = QButtonGroup(self)
        self._nav_group.setExclusive(True)
        _L = normalize_ui_language(self._settings.ui_language)
        for i, nk in enumerate(_NAV_KEYS):
            nb = QPushButton(_ICON_TEXT_GAP + tr(_L, nk))
            nb.setObjectName("headerNavButton")
            nb.setCheckable(True)
            self._nav_group.addButton(nb, i)
            self._register_icon_widget(nb, NAV_ICON_KEYS[i], "nav")
            nav_lay.addWidget(nb)
        self._nav_group.button(0).setChecked(True)
        self._nav_group.idClicked.connect(self._on_nav_id_clicked)
        head_lay.addWidget(nav_wrap, 0)
        head_lay.addStretch(1)
        head_lay.addWidget(self._header_actions_stack, 0)
        root.addWidget(header)

        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)

        sidebar_wrap = QWidget()
        sidebar_wrap.setObjectName("brandingPanel")
        sidebar_wrap.setFixedWidth(260)
        side_col = QVBoxLayout(sidebar_wrap)
        side_col.setContentsMargins(0, 0, 0, 0)
        side_col.setSpacing(0)
        _char_path = assets_dir() / "images" / "character.png"
        _pix = QPixmap(str(_char_path))
        if not _pix.isNull():
            _char = QLabel()
            _char.setObjectName("sidebarCharacter")
            _char.setAlignment(Qt.AlignmentFlag.AlignCenter)
            _char.setFixedWidth(260)
            _char.setPixmap(
                _pix.scaled(
                    260,
                    168,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
            side_col.addWidget(_char)
        _divider = QFrame()
        _divider.setObjectName("brandDivider")
        _divider.setFrameShape(QFrame.Shape.HLine)
        _divider.setFixedHeight(2)
        side_col.addWidget(_divider)
        _brand = QWidget()
        _bl = QVBoxLayout(_brand)
        _bl.setContentsMargins(10, 8, 10, 10)
        _bl.setSpacing(6)
        self._lbl_brand_product = QLabel(tr(_L, "app.product_subtitle"))
        self._lbl_brand_product.setObjectName("brandTitle")
        self._lbl_brand_product.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl_brand_product.setWordWrap(True)
        self._lbl_brand_blurb = QLabel(tr(_L, "app.blurb"))
        self._lbl_brand_blurb.setObjectName("brandBlurb")
        self._lbl_brand_blurb.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl_brand_blurb.setWordWrap(True)
        _info = QFrame()
        _info.setObjectName("brandInfoCard")
        _il = QVBoxLayout(_info)
        _il.setContentsMargins(10, 10, 10, 10)
        _il.setSpacing(8)
        self._lbl_brand_sec_feat = QLabel(tr(_L, "app.about_features_title"))
        self._lbl_brand_sec_feat.setObjectName("brandSectionTitle")
        self._lbl_brand_feat = QLabel(tr(_L, "app.about_features"))
        self._lbl_brand_feat.setObjectName("brandFeaturesList")
        self._lbl_brand_feat.setWordWrap(True)
        self._lbl_brand_hint = QLabel(tr(_L, "app.disclaimer"))
        self._lbl_brand_hint.setObjectName("brandHint")
        self._lbl_brand_hint.setWordWrap(True)
        _il.addWidget(self._lbl_brand_sec_feat)
        _il.addWidget(self._lbl_brand_feat)
        _il.addWidget(self._lbl_brand_hint)
        _div_bottom = QFrame()
        _div_bottom.setObjectName("brandDivider")
        _div_bottom.setFrameShape(QFrame.Shape.HLine)
        _div_bottom.setFixedHeight(2)
        _social_row = QWidget()
        _social_row.setObjectName("brandSocialRow")
        _sl = QHBoxLayout(_social_row)
        _sl.setContentsMargins(0, 10, 0, 10)
        _sl.setSpacing(12)
        _sl.addStretch(1)
        _sz_social = icon_kind_size("brand_social")
        _qsz_social = QSize(_sz_social, _sz_social)
        for key, url, tip_key in (
            ("brand_telegram", BRAND_TELEGRAM_URL, "app.social_telegram"),
            ("brand_whatsapp", BRAND_WHATSAPP_URL, "app.social_whatsapp"),
            ("brand_email", f"mailto:{STUDIO_EMAIL}", "app.social_email"),
        ):
            tb = QToolButton()
            tb.setObjectName("brandSocialButton")
            tb.setAutoRaise(True)
            tb.setIcon(app_icon(key, self._settings.theme))
            tb.setIconSize(_qsz_social)
            tb.setCursor(Qt.CursorShape.PointingHandCursor)
            tb.setToolTip(tr(_L, tip_key))
            tb.clicked.connect(lambda _=False, u=url: QDesktopServices.openUrl(QUrl(u)))
            self._register_icon_widget(tb, key, "brand_social")
            self._brand_social_tooltips.append((tb, tip_key))
            _sl.addWidget(tb)
        _sl.addStretch(1)
        for w in (
            self._lbl_brand_product,
            self._lbl_brand_blurb,
            _info,
        ):
            _bl.addWidget(w)
        _bl.addStretch(1)
        _bl.addWidget(_div_bottom)
        _bl.addWidget(_social_row)
        side_col.addWidget(_brand, 1)

        scroll_inner = QWidget()
        sil = QVBoxLayout(scroll_inner)
        sil.setContentsMargins(CONTENT_PADDING, CONTENT_PADDING, CONTENT_PADDING, CONTENT_PADDING)
        sil.setSpacing(2)
        self._stack.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sil.addWidget(self._stack, 1)

        center = QWidget()
        center.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        c_lay = QVBoxLayout(center)
        c_lay.setContentsMargins(0, 0, 0, 0)
        c_lay.addWidget(scroll_inner)

        wrap_row = QWidget()
        wrap_lay = QHBoxLayout(wrap_row)
        wrap_lay.setContentsMargins(0, 0, 0, 0)
        wrap_lay.addWidget(center, 1)

        content_area = QWidget()
        content_area.setObjectName("contentArea")
        ca_lay = QVBoxLayout(content_area)
        ca_lay.setContentsMargins(0, 0, 0, 0)
        ca_lay.addWidget(wrap_row, 1)

        _side_div = QFrame()
        _side_div.setObjectName("sidebarVerticalDivider")
        _side_div.setFrameShape(QFrame.Shape.NoFrame)
        _side_div.setFixedWidth(2)
        _side_div.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)

        body.addWidget(sidebar_wrap, 0)
        body.addWidget(_side_div, 0)
        body.addWidget(content_area, 1)
        root.addLayout(body, 1)

        footer = QWidget()
        footer.setObjectName("appFooter")
        foot_lay = QHBoxLayout(footer)
        foot_lay.setContentsMargins(S16, 10, S16, 10)
        foot_lay.setSpacing(S16)
        self._footer_info = QLabel()
        self._footer_info.setObjectName("footerSecondary")
        self._footer_info.setTextFormat(Qt.TextFormat.RichText)
        self._footer_info.setOpenExternalLinks(True)
        self._footer_info.setText(self._footer_copyright_html(_L))
        self._footer_status = QLabel("Стан: зупинено")
        self._footer_status.setObjectName("footerStatusLabel")
        self._footer_status.setProperty("state", "idle")
        foot_lay.addWidget(self._footer_info, 0)
        foot_lay.addStretch(1)
        foot_lay.addWidget(self._footer_status, 0)
        root.addWidget(footer)

        self.statusBar().hide()

    def _connect_signals(self) -> None:
        self._kb_hooks.key_event.connect(self._on_test_key)
        self._kb_hooks.mouse_button.connect(self._on_test_mouse_btn)
        self._kb_hooks.mouse_position.connect(self._on_test_mouse_pos)
        self._kb_hooks.scroll_event.connect(self._on_test_scroll)

    def _macros_path(self) -> Path:
        if self._settings.macros_folder.strip():
            return Path(self._settings.macros_folder)
        return macros_dir()

    def _form_label(self, text: str) -> QLabel:
        lb = QLabel(text)
        lb.setObjectName("formFieldLabel")
        lb.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        lb.setMinimumWidth(FORM_LABEL_MIN_W)
        lb.setMaximumWidth(FORM_LABEL_MIN_W + 24)
        return lb

    def _form_label_compact(self, text: str) -> QLabel:
        lb = QLabel(text)
        lb.setObjectName("formFieldLabel")
        lb.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        lb.setFixedWidth(AC_GRID_LABEL_W)
        lb.setWordWrap(True)
        return lb

    def _bind_row_label(self, text: str) -> QLabel:
        lb = QLabel(text)
        lb.setObjectName("settingsFieldLabel")
        lb.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        lb.setMinimumWidth(BINDS_LABEL_MIN_W)
        lb.setMaximumWidth(BINDS_LABEL_MIN_W + 80)
        lb.setWordWrap(True)
        return lb

    def _inline_lbl(self, text: str, w: int = 72) -> QLabel:
        lb = QLabel(text)
        lb.setObjectName("formInlineLabel")
        lb.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        lb.setFixedWidth(w)
        return lb

    def _pair_labeled(self, text: str, ctrl: QWidget, lab_w: int = 72) -> QWidget:
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(8)
        row.addWidget(self._inline_lbl(text, lab_w), 0, Qt.AlignmentFlag.AlignVCenter)
        row.addWidget(ctrl, 0, Qt.AlignmentFlag.AlignVCenter)
        wrap = QWidget()
        wrap.setLayout(row)
        return wrap

    def _settings_lbl(self, text: str) -> QLabel:
        lb = QLabel(text)
        lb.setObjectName("settingsFieldLabel")
        lb.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        lb.setFixedWidth(176)
        lb.setWordWrap(True)
        return lb

    def _settings_card(self, title: str) -> tuple[QFrame, QVBoxLayout]:
        card = QFrame()
        card.setObjectName("settingsCard")
        outer = QVBoxLayout(card)
        outer.setContentsMargins(10, 10, 10, 10)
        outer.setSpacing(4)
        tl = QLabel(title)
        tl.setObjectName("settingsCardTitle")
        tl.setWordWrap(True)
        outer.addWidget(tl)
        rows = QVBoxLayout()
        rows.setSpacing(5)
        rows.setContentsMargins(0, 0, 0, 0)
        outer.addLayout(rows)
        return card, rows

    def _settings_inline_row(self, label_text: str, widget: QWidget) -> QWidget:
        w = QWidget()
        h = QHBoxLayout(w)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(8)
        lab = QLabel(label_text)
        lab.setObjectName("settingsFormLabel")
        lab.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        lab.setFixedWidth(SETTINGS_INLINE_LABEL_W)
        lab.setWordWrap(True)
        widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        h.addWidget(lab, 0, Qt.AlignmentFlag.AlignTop)
        h.addWidget(widget, 1, Qt.AlignmentFlag.AlignVCenter)
        return w

    def _field_max_width(self, w: QWidget, max_w: int) -> None:
        w.setMaximumWidth(max_w)
        w.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)

    def _section_card(self, title: str, icon_key: str | None = None) -> tuple[QFrame, QVBoxLayout]:
        card = QFrame()
        card.setObjectName("contentCard")
        lay = QVBoxLayout(card)
        lay.setSpacing(4)
        lay.setContentsMargins(6, 6, 6, 6)
        if title:
            if icon_key:
                head = QHBoxLayout()
                head.setContentsMargins(0, 0, 0, 0)
                head.setSpacing(8)
                il = QLabel()
                il.setObjectName("sectionTitleIcon")
                il.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                il.setAutoFillBackground(False)
                self._register_icon_widget(il, icon_key, "section")
                tl = QLabel(title)
                tl.setObjectName("sectionTitle")
                tl.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                tl.setAutoFillBackground(False)
                head.addWidget(il, 0, Qt.AlignmentFlag.AlignVCenter)
                head.addWidget(tl, 0, Qt.AlignmentFlag.AlignVCenter)
                head.addStretch(1)
                lay.addLayout(head)
            else:
                tl = QLabel(title)
                tl.setObjectName("sectionTitle")
                tl.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                tl.setAutoFillBackground(False)
                lay.addWidget(tl)
        return card, lay

    def _build_autoclick_tab(self) -> QWidget:
        w = QWidget()
        outer = QVBoxLayout(w)
        outer.setSpacing(2)
        outer.setContentsMargins(0, 0, 0, 0)

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
        self._lbl_xy.setObjectName("formHint")
        self._lbl_xy.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        c1, l1 = self._section_card("Клік", "section_click")
        g1 = QGridLayout()
        g1.setHorizontalSpacing(4)
        g1.setVerticalSpacing(4)
        g1.setColumnStretch(1, 1)
        g1.addWidget(self._form_label_compact("Кнопка"), 0, 0)
        g1.addWidget(self._ac_button, 0, 1)
        g1.addWidget(self._form_label_compact("Режим"), 1, 0)
        g1.addWidget(self._ac_mode, 1, 1)
        l1.addLayout(g1)

        c2, l2 = self._section_card("Інтервали та CPS", "section_intervals")
        l2.addWidget(self._ac_use_interval)
        g2 = QGridLayout()
        g2.setHorizontalSpacing(4)
        g2.setVerticalSpacing(4)
        g2.setColumnStretch(1, 1)
        g2.addWidget(self._form_label_compact("Інтервал (мс)"), 0, 0)
        g2.addWidget(self._ac_interval_ms, 0, 1)
        g2.addWidget(self._form_label_compact("CPS"), 1, 0)
        g2.addWidget(self._ac_cps, 1, 1)
        g2.addWidget(self._form_label_compact("Jitter (мс)"), 2, 0)
        g2.addWidget(self._ac_jitter, 2, 1)
        l2.addLayout(g2)

        c3, l3 = self._section_card("Позиція", "section_position")
        g3 = QGridLayout()
        g3.setHorizontalSpacing(4)
        g3.setVerticalSpacing(4)
        g3.setColumnStretch(1, 1)
        g3.addWidget(self._ac_saved, 0, 0, 1, 2)
        g3.addWidget(self._form_label_compact("X"), 1, 0)
        g3.addWidget(self._ac_sx, 1, 1)
        g3.addWidget(self._form_label_compact("Y"), 2, 0)
        g3.addWidget(self._ac_sy, 2, 1)
        g3.addWidget(self._lbl_xy, 3, 0, 1, 2)
        l3.addLayout(g3)

        c4, l4 = self._section_card("Режим роботи", "section_work_mode")
        self._ac_work_mode = QComboBox()
        self._ac_work_mode.addItems(["Простий (миша)", "Послідовність", "Повтор клавіші"])
        self._ac_work_mode.currentIndexChanged.connect(self._on_ac_work_mode_changed)
        g4 = QGridLayout()
        g4.setHorizontalSpacing(4)
        g4.setVerticalSpacing(4)
        g4.setColumnStretch(1, 1)
        g4.addWidget(self._form_label_compact("Режим"), 0, 0)
        g4.addWidget(self._ac_work_mode, 0, 1)
        l4.addLayout(g4)

        self._ac_key_repeat_card, l5 = self._section_card("Повтор клавіші", "section_key_repeat")
        self._ac_key_repeat_label = self._form_label_compact("Клавіша")
        self._ac_key_repeat = QLineEdit()
        self._ac_key_repeat.setPlaceholderText("напр. e або space")
        g5 = QGridLayout()
        g5.setHorizontalSpacing(4)
        g5.setVerticalSpacing(4)
        g5.setColumnStretch(1, 1)
        g5.addWidget(self._ac_key_repeat_label, 0, 0)
        g5.addWidget(self._ac_key_repeat, 0, 1)
        l5.addLayout(g5)

        row_top = QHBoxLayout()
        row_top.setSpacing(4)
        row_top.addWidget(c1, 1, Qt.AlignmentFlag.AlignTop)
        row_top.addWidget(c2, 1, Qt.AlignmentFlag.AlignTop)
        row_top.addWidget(c3, 1, Qt.AlignmentFlag.AlignTop)
        outer.addLayout(row_top)

        row_mid = QHBoxLayout()
        row_mid.setSpacing(4)
        row_mid.addWidget(c4, 1, Qt.AlignmentFlag.AlignTop)
        row_mid.addWidget(self._ac_key_repeat_card, 1, Qt.AlignmentFlag.AlignTop)
        outer.addLayout(row_mid)

        _hs = self._settings
        self._ac_human_card, hmain = self._section_card("Природна варіативність")
        self._ac_humanize = QCheckBox("Додаткові випадкові паузи між кліками")
        self._ac_humanize.setChecked(_hs.ac_humanize_enabled)
        self._ac_gauss_jitter = QCheckBox("Гаусівський розкид джитера (замість рівномірного)")
        self._ac_gauss_jitter.setChecked(_hs.ac_jitter_gaussian)
        self._ac_pause_chance = QDoubleSpinBox()
        self._ac_pause_chance.setRange(0, 25)
        self._ac_pause_chance.setDecimals(1)
        self._ac_pause_chance.setSuffix(" %")
        self._ac_pause_chance.setValue(_hs.ac_pause_chance_percent)
        self._ac_pause_extra = QDoubleSpinBox()
        self._ac_pause_extra.setRange(20, 4000)
        self._ac_pause_extra.setDecimals(0)
        self._ac_pause_extra.setValue(_hs.ac_pause_extra_ms)
        self._ac_micro_move = QSpinBox()
        self._ac_micro_move.setRange(0, 48)
        self._ac_micro_move.setValue(_hs.ac_micro_move_px)
        self._ac_pre_click = QDoubleSpinBox()
        self._ac_pre_click.setRange(0, 120)
        self._ac_pre_click.setDecimals(0)
        self._ac_pre_click.setValue(_hs.ac_pre_click_delay_ms_max)
        hmain.addWidget(self._ac_humanize)
        hmain.addWidget(self._ac_gauss_jitter)
        hg = QGridLayout()
        hg.setHorizontalSpacing(4)
        hg.setVerticalSpacing(4)
        hg.setColumnStretch(1, 1)
        hg.addWidget(self._form_label_compact("Ймовірність паузи"), 0, 0)
        hg.addWidget(self._ac_pause_chance, 0, 1)
        hg.addWidget(self._form_label_compact("Макс. додаткова пауза"), 1, 0)
        hg.addWidget(self._ac_pause_extra, 1, 1)
        hg.addWidget(self._form_label_compact("Мікрозміщення ±px"), 2, 0)
        hg.addWidget(self._ac_micro_move, 2, 1)
        hg.addWidget(self._form_label_compact("Затримка перед кліком (макс. мс)"), 3, 0)
        hg.addWidget(self._ac_pre_click, 3, 1)
        hmain.addLayout(hg)
        _hum_hint = QLabel(
            "Не гарантує обхід захисту ігор; дотримуйтесь правил сервісів. "
            "Мікрозміщення діє, коли не ввімкнено «Клік по збережених X/Y»."
        )
        _hum_hint.setObjectName("formHint")
        _hum_hint.setWordWrap(True)
        hmain.addWidget(_hum_hint)
        outer.addWidget(self._ac_human_card)

        self._ac_seq_group, sg = self._section_card("Кроки послідовності", "section_sequence")
        sg.setSpacing(3)
        self._ac_seq_table = QTableWidget(0, 3)
        self._ac_seq_table.setHorizontalHeaderLabels(["Тип", "Ключ / кнопка миші", "Затримка (мс)"])
        self._ac_seq_table.setMinimumHeight(88)
        self._ac_seq_table.setAlternatingRowColors(True)
        self._ac_seq_table.verticalHeader().setVisible(False)
        self._ac_seq_table.setShowGrid(True)
        _seq_hdr = self._ac_seq_table.horizontalHeader()
        _seq_hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        _seq_hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        _seq_hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        _seq_hdr.setMinimumSectionSize(88)
        _seq_hdr.setStretchLastSection(False)
        _seq_hdr.setDefaultAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        sg.addWidget(self._ac_seq_table)
        seq_btns = QHBoxLayout()
        self._ac_seq_add = QPushButton("Додати рядок")
        self._ac_seq_add.setObjectName("seqRowButton")
        self._ac_seq_del = QPushButton("Видалити рядок")
        self._ac_seq_del.setObjectName("seqRowButton")
        self._ac_seq_add.clicked.connect(self._ac_seq_add_row)
        self._ac_seq_del.clicked.connect(self._ac_seq_del_row)
        self._register_icon_widget(self._ac_seq_add, "action_plus", "toolbar")
        self._register_icon_widget(self._ac_seq_del, "action_minus", "toolbar")
        seq_btns.setSpacing(4)
        seq_btns.addWidget(self._ac_seq_add)
        seq_btns.addWidget(self._ac_seq_del)
        sg.addLayout(seq_btns)
        rep_row = QHBoxLayout()
        rep_row.setSpacing(6)
        self._ac_seq_repeat_mode = QComboBox()
        self._ac_seq_repeat_mode.addItems(["Вся послідовність", "Один крок (за індексом)"])
        self._ac_seq_step_idx = QSpinBox()
        self._ac_seq_step_idx.setRange(0, 10_000)
        self._ac_seq_loop_inf = QCheckBox("Повторювати безкінечно")
        self._ac_seq_loop_inf.setChecked(True)
        rep_row.addWidget(self._pair_labeled("Повтор", self._ac_seq_repeat_mode, 88))
        rep_row.addWidget(self._pair_labeled("Індекс кроку", self._ac_seq_step_idx, 100))
        rep_row.addStretch(1)
        rep_row.addWidget(self._ac_seq_loop_inf, 0, Qt.AlignmentFlag.AlignVCenter)
        sg.addLayout(rep_row)
        outer.addWidget(self._ac_seq_group)

        for _w in (self._ac_button, self._ac_mode, self._ac_work_mode, self._ac_seq_repeat_mode):
            self._field_max_width(_w, AC_COL_COMBO_MAX_W)
        for _w in (
            self._ac_interval_ms,
            self._ac_cps,
            self._ac_jitter,
            self._ac_sx,
            self._ac_sy,
            self._ac_seq_step_idx,
        ):
            self._field_max_width(_w, AC_COL_FIELD_MAX_W)
        self._field_max_width(self._ac_key_repeat, AC_COL_COMBO_MAX_W)
        for _w in (
            self._ac_pause_chance,
            self._ac_pause_extra,
            self._ac_micro_move,
            self._ac_pre_click,
        ):
            self._field_max_width(_w, AC_COL_FIELD_MAX_W)

        row = QHBoxLayout()
        row.setSpacing(4)
        row.addWidget(self._btn_reset)
        row.addWidget(self._btn_save_xy)
        row.addStretch(1)
        outer.addLayout(row)
        self._load_ac_mode_ui()
        self._update_ac_button_hotkey_labels()
        return w

    def _update_ac_button_hotkey_labels(self) -> None:
        """Показати на кнопках глобальні бинди з налаштувань."""
        if not hasattr(self, "_btn_start"):
            return
        b = self._settings.bindings

        def suf(ch: HotkeyChord | None) -> str:
            return f" ({ch.display_string()})" if ch else ""

        g = _ICON_TEXT_GAP
        self._btn_start.setText(g + "Старт" + suf(b.toggle_autoclick))
        self._btn_pause.setText(g + "Пауза" + suf(b.pause_autoclick))
        self._btn_stop.setText(g + "Стоп" + suf(b.toggle_autoclick))
        self._btn_reset.setText(g + "Скидання")
        self._btn_save_xy.setText(g + "Зберегти позицію курсора")

    def _load_ac_mode_ui(self) -> None:
        s = self._settings
        mode_map = {"simple": 0, "sequence": 1, "key_repeat": 2}
        self._ac_work_mode.setCurrentIndex(mode_map.get(s.autoclick_work_mode, 0))
        self._ac_seq_repeat_mode.setCurrentIndex(0 if s.sequence_repeat_mode == SequenceRepeatMode.FULL.value else 1)
        self._ac_seq_step_idx.setValue(int(s.sequence_step_index))
        self._ac_seq_loop_inf.setChecked(bool(s.sequence_loop_infinite))
        self._ac_key_repeat.setText(s.autoclick_key_repeat_key)
        self._ac_humanize.setChecked(s.ac_humanize_enabled)
        self._ac_gauss_jitter.setChecked(s.ac_jitter_gaussian)
        self._ac_pause_chance.setValue(s.ac_pause_chance_percent)
        self._ac_pause_extra.setValue(s.ac_pause_extra_ms)
        self._ac_micro_move.setValue(s.ac_micro_move_px)
        self._ac_pre_click.setValue(s.ac_pre_click_delay_ms_max)
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
        self._settings.ac_humanize_enabled = self._ac_humanize.isChecked()
        self._settings.ac_jitter_gaussian = self._ac_gauss_jitter.isChecked()
        self._settings.ac_pause_chance_percent = float(self._ac_pause_chance.value())
        self._settings.ac_pause_extra_ms = float(self._ac_pause_extra.value())
        self._settings.ac_micro_move_px = int(self._ac_micro_move.value())
        self._settings.ac_pre_click_delay_ms_max = float(self._ac_pre_click.value())
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
        self._ac_key_repeat_card.setVisible(idx == 2)
        self._ac_human_card.setVisible(idx == 0)
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
            humanize_enabled=self._ac_humanize.isChecked(),
            jitter_gaussian=self._ac_gauss_jitter.isChecked(),
            pause_chance_percent=float(self._ac_pause_chance.value()),
            pause_extra_ms=float(self._ac_pause_extra.value()),
            micro_move_px=int(self._ac_micro_move.value()),
            pre_click_delay_ms_max=float(self._ac_pre_click.value()),
        )

    def _ac_effective_interval_ms(self) -> float:
        if self._ac_use_interval.isChecked():
            return float(self._ac_interval_ms.value())
        return 1000.0 / max(0.1, float(self._ac_cps.value()))

    def _ac_work_mode_key(self) -> str:
        idx = self._ac_work_mode.currentIndex()
        modes = ("simple", "sequence", "key_repeat")
        return modes[idx] if idx < len(modes) else "simple"

    def _active_autoclick_state(self) -> AutoclickState:
        return self._clicker.get_state(self._ac_work_mode_key())

    def _ac_start(self) -> None:
        self._sync_ac_settings_from_ui()
        mode = self._settings.autoclick_work_mode
        if mode == "simple":
            self._clicker.start_simple(self._ac_config_from_ui())
        elif mode == "sequence":
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
            self._clicker.start_sequence(cfg)
        else:
            tok = (self._settings.autoclick_key_repeat_key or "").strip()
            if not tok:
                QMessageBox.warning(self, "Автоклікер", "Вкажіть клавішу для повтору.")
                return
            self._clicker.start_key_repeat(
                tok,
                self._ac_effective_interval_ms(),
                float(self._ac_jitter.value()),
            )
        if self._settings.sound_on_start_stop:
            play_beep("start")
        self._refresh_status()
        logging.getLogger(__name__).info("Автоклікер: старт")

    def _ac_pause(self) -> None:
        self._clicker.pause(self._ac_work_mode_key())
        self._refresh_status()

    def _ac_stop(self) -> None:
        self._clicker.stop_all()
        if self._settings.sound_on_start_stop:
            play_beep("stop")
        self._refresh_status()
        logging.getLogger(__name__).info("Автоклікер: стоп")

    def _ac_reset(self) -> None:
        self._ac_stop()
        self._ac_interval_ms.setValue(100)
        self._ac_cps.setValue(5)
        self._ac_jitter.setValue(5)
        self._ac_humanize.setChecked(False)
        self._ac_gauss_jitter.setChecked(False)
        self._ac_pause_chance.setValue(0)
        self._ac_pause_extra.setValue(220)
        self._ac_micro_move.setValue(0)
        self._ac_pre_click.setValue(0)

    def _ac_save_xy(self) -> None:
        p = self._input.get_mouse_position()
        self._ac_sx.setValue(int(p[0]))
        self._ac_sy.setValue(int(p[1]))
        self._settings.saved_click_x = int(p[0])
        self._settings.saved_click_y = int(p[1])
        save_settings(self._settings)

    def _tick_cursor(self) -> None:
        p = self._input.get_mouse_position()
        self._lbl_xy.setText(f"Курсор: X={int(p[0])} Y={int(p[1])}")
        self._settings.last_cursor_x = int(p[0])
        self._settings.last_cursor_y = int(p[1])

    def _build_macro_tab(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setSpacing(6)
        lay.setContentsMargins(0, 0, 0, 0)

        c_prof, lp = self._section_card("Профіль запису", "section_profile")
        prof_row = QHBoxLayout()
        prof_row.setSpacing(10)
        plab = QLabel("Профіль:")
        plab.setObjectName("formInlineLabel")
        plab.setFixedWidth(72)
        plab.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        prof_row.addWidget(plab, 0, Qt.AlignmentFlag.AlignVCenter)
        self._macro_profile_combo = QComboBox()
        self._macro_profile_combo.currentIndexChanged.connect(self._on_macro_profile_changed)
        prof_row.addWidget(self._macro_profile_combo, 1)
        self._btn_prof_new = QPushButton("Новий профіль")
        self._btn_prof_save = QPushButton("Зберегти профіль")
        self._btn_prof_new.clicked.connect(self._macro_profile_new)
        self._btn_prof_save.clicked.connect(self._macro_profile_save)
        prof_row.addWidget(self._btn_prof_new)
        prof_row.addWidget(self._btn_prof_save)
        self._register_icon_widget(self._btn_prof_new, "macro_profile_new", "toolbar")
        self._register_icon_widget(self._btn_prof_save, "macro_profile_save", "toolbar")
        lp.addLayout(prof_row)
        lay.addWidget(c_prof)

        c_flags, lf = self._section_card("Що записувати", "section_record_flags")
        flags = QHBoxLayout()
        flags.setSpacing(12)
        self._chk_p_keys = QCheckBox("Клавіатура")
        self._chk_p_clicks = QCheckBox("Кліки миші")
        self._chk_p_move = QCheckBox("Рух миші")
        self._chk_p_scroll = QCheckBox("Скрол")
        self._chk_p_filter = QCheckBox("Фільтр биндів")
        for c in (self._chk_p_keys, self._chk_p_clicks, self._chk_p_move, self._chk_p_scroll, self._chk_p_filter):
            flags.addWidget(c)
        lf.addLayout(flags)
        lay.addWidget(c_flags)

        c_list, ll = self._section_card("Макроси та дії", "section_macros_list")
        top = QHBoxLayout()
        top.setContentsMargins(0, 0, 0, 0)
        top.setSpacing(8)
        self._macro_list = QListWidget()
        self._macro_list.setObjectName("macroFileList")
        self._macro_list.setMinimumHeight(112)
        self._btn_macro_preview = QPushButton(_ICON_TEXT_GAP + "Переглянути")
        self._btn_save_m = QPushButton("Зберегти як…")
        self._btn_load_m = QPushButton("Завантажити…")
        self._btn_del_m = QPushButton("Видалити")
        self._btn_rename = QPushButton("Перейменувати")
        for _mb in (self._btn_macro_preview, self._btn_save_m, self._btn_load_m, self._btn_rename, self._btn_del_m):
            _mb.setObjectName("macroSideButton")
        top.addWidget(self._macro_list, 1)
        col = QVBoxLayout()
        col.setSpacing(6)
        col.addWidget(self._btn_macro_preview)
        col.addWidget(self._btn_save_m)
        col.addWidget(self._btn_load_m)
        col.addWidget(self._btn_rename)
        col.addWidget(self._btn_del_m)
        col.addStretch(1)
        for _mb in (self._btn_macro_preview, self._btn_save_m, self._btn_load_m, self._btn_rename, self._btn_del_m):
            _mb.setMinimumWidth(MACRO_SIDE_BTN_MIN_W)
            _mb.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        self._register_icon_widget(self._btn_macro_preview, "macro_preview", "toolbar")
        self._register_icon_widget(self._btn_save_m, "macro_save_as", "toolbar")
        self._register_icon_widget(self._btn_load_m, "macro_load", "toolbar")
        self._register_icon_widget(self._btn_rename, "macro_rename", "toolbar")
        self._register_icon_widget(self._btn_del_m, "macro_delete", "toolbar")
        top.addLayout(col)
        ll.addLayout(top)
        lay.addWidget(c_list)

        c_rep, lr = self._section_card("Відтворення", "section_playback")
        rep = QHBoxLayout()
        rep.setSpacing(10)
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
        rep.addWidget(self._pair_labeled("Повтор", self._macro_repeat, 72))
        rep.addWidget(self._pair_labeled("N", self._macro_n, 28))
        rep.addWidget(self._pair_labeled("Швидкість", self._macro_speed, 88))
        rep.addWidget(self._pair_labeled("Множник", self._macro_mult, 88))
        rep.addStretch(1)
        lr.addLayout(rep)
        lay.addWidget(c_rep)
        for _mw in (self._macro_repeat, self._macro_speed):
            self._field_max_width(_mw, FORM_COMBO_MAX_W)
        for _mw in (self._macro_n, self._macro_mult):
            self._field_max_width(_mw, FORM_FIELD_MAX_W)

        self._macro_table = QTableWidget(0, 6)
        self._macro_table.setHorizontalHeaderLabels(
            ["Тип", "Клавіша/кнопка", "Затримка (мс)", "X", "Y", "Скрол"]
        )
        self._macro_table.setMinimumHeight(120)
        self._macro_table.verticalHeader().setVisible(False)
        self._macro_table.setAlternatingRowColors(True)
        _mh = self._macro_table.horizontalHeader()
        for i, mode in enumerate(
            (
                QHeaderView.ResizeMode.ResizeToContents,
                QHeaderView.ResizeMode.Stretch,
                QHeaderView.ResizeMode.ResizeToContents,
                QHeaderView.ResizeMode.ResizeToContents,
                QHeaderView.ResizeMode.ResizeToContents,
                QHeaderView.ResizeMode.ResizeToContents,
            )
        ):
            _mh.setSectionResizeMode(i, mode)
        _mh.setStretchLastSection(True)
        _mh.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        lay.addWidget(self._macro_table, 1)
        self._btn_macro_preview.clicked.connect(self._macro_preview_from_list)
        self._btn_save_m.clicked.connect(self._macro_save)
        self._btn_load_m.clicked.connect(self._macro_load)
        self._btn_del_m.clicked.connect(self._macro_delete)
        self._btn_rename.clicked.connect(self._macro_rename)
        self._btn_apply_tbl = QPushButton("Застосувати зміни з таблиці")
        self._btn_apply_tbl.clicked.connect(self._macro_apply_table)
        self._register_icon_widget(self._btn_apply_tbl, "action_apply", "toolbar")
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

    def _macro_list_active_item(self):
        """Після кліку по кнопці фокус зникає зі списку — currentItem() часто None; беремо виділення."""
        sel = self._macro_list.selectedItems()
        if sel:
            return sel[0]
        return self._macro_list.currentItem()

    def _ensure_macro_table_visible(self) -> None:
        w: QWidget | None = self._macro_table
        for _ in range(16):
            if w is None:
                return
            p = w.parentWidget()
            if isinstance(p, QScrollArea):
                p.ensureWidgetVisible(self._macro_table)
                return
            w = p

    def _macro_preview_from_list(self) -> None:
        self._load_macro_from_list_item(silent=False)

    def _load_macro_from_list_item(self, silent: bool) -> None:
        it = self._macro_list_active_item()
        if not it:
            if not silent:
                QMessageBox.information(self, "Макрос", "Оберіть файл у списку.")
            return
        path = self._macros_path() / it.text()
        raw = read_json(path, {})
        try:
            self._current_macro = MacroDefinition.from_dict(raw)
            self._fill_macro_table(self._current_macro)
            QTimer.singleShot(0, self._ensure_macro_table_visible)
        except Exception as e:
            logging.getLogger(__name__).exception("Помилка читання макросу: %s", e)
            if not silent:
                QMessageBox.warning(self, "Макрос", f"Не вдалося прочитати файл:\n{e}")

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
        it = self._macro_list_active_item()
        if it:
            path = self._macros_path() / it.text()
            raw = read_json(path, {})
            try:
                self._current_macro = MacroDefinition.from_dict(raw)
            except Exception as e:
                logging.getLogger(__name__).exception("Макрос для відтворення: %s", e)
                QMessageBox.warning(self, "Макрос", f"Не вдалося прочитати файл:\n{e}")
                return
        if not self._current_macro or not self._current_macro.events:
            QMessageBox.warning(self, "Макрос", "Немає подій для відтворення. Оберіть файл і натисніть «Переглянути» або запишіть макрос.")
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

    def _build_binds_section(self) -> QFrame:
        card, lay = self._settings_card("Гарячі клавіші (бинди)")
        self._bind_fields = {}
        names = [
            ("toggle_autoclick", "Перемикач автоклікера"),
            ("pause_autoclick", "Пауза"),
            ("toggle_macro_play", "Перемикач відтворення макросу"),
            ("toggle_record_macro", "Запис макросу (перемикач)"),
            ("toggle_tray", "Згорнути / показати (трей)"),
            ("emergency_stop", "Аварійна зупинка"),
        ]
        for key, title in names:
            row = QFrame()
            row.setObjectName("bindHotkeyRow")
            h = QHBoxLayout(row)
            h.setContentsMargins(0, 0, 0, 0)
            h.setSpacing(6)
            lbl = QLabel(title)
            lbl.setObjectName("bindHotkeyActionLabel")
            lbl.setFixedWidth(SETTINGS_INLINE_LABEL_W)
            lbl.setWordWrap(True)
            lbl.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            le = QLineEdit()
            le.setReadOnly(True)
            le.setMinimumHeight(30)
            le.setMaximumHeight(32)
            b_listen = QPushButton("Слухати")
            b_clear = QPushButton("Очистити")
            b_listen.setObjectName("bindHotkeyRowButton")
            b_clear.setObjectName("bindHotkeyRowButton")
            b_listen.setFixedWidth(80)
            b_clear.setFixedWidth(76)
            b_listen.setMinimumHeight(30)
            b_listen.setMaximumHeight(32)
            b_clear.setMinimumHeight(30)
            b_clear.setMaximumHeight(32)
            b_listen.clicked.connect(lambda checked=False, k=key: self._bind_listen(k))
            b_clear.clicked.connect(lambda checked=False, k=key: self._bind_clear(k))
            self._register_icon_widget(b_listen, "action_listen", "toolbar")
            self._register_icon_widget(b_clear, "action_clear", "toolbar")
            h.addWidget(lbl, 0)
            h.addWidget(le, 1)
            h.addWidget(b_listen, 0)
            h.addWidget(b_clear, 0)
            lay.addWidget(row)
            self._bind_fields[key] = le
        self._load_binds_to_ui()
        return card

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

    def _build_settings_tab(self) -> QWidget:
        outer = QWidget()
        outer_lay = QVBoxLayout(outer)
        outer_lay.setContentsMargins(0, 0, 0, 0)
        outer_lay.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        inner = QWidget()
        inner.setObjectName("settingsTabRoot")
        vl = QVBoxLayout(inner)
        vl.setSpacing(11)
        vl.setContentsMargins(14, 12, 14, 12)

        self._set_theme = QComboBox()
        self._set_theme.addItems(["Темна", "Світла"])
        self._set_theme.setCurrentIndex(0 if self._settings.theme == ThemeMode.DARK else 1)
        self._set_lang = QComboBox()
        for label, code in (
            ("English", "en"),
            ("Українська", "uk"),
            ("Русский", "ru"),
        ):
            self._set_lang.addItem(label, code)
        _lang_cur = normalize_ui_language(self._settings.ui_language)
        for _i in range(self._set_lang.count()):
            if self._set_lang.itemData(_i) == _lang_cur:
                self._set_lang.setCurrentIndex(_i)
                break
        else:
            self._set_lang.setCurrentIndex(1)
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
        self._set_overlay_op.setAlignment(Qt.AlignmentFlag.AlignRight)
        self._set_autosave = QCheckBox("Увімкнути")
        self._set_autosave.setChecked(self._settings.autosave_macros)
        self._set_autosave_sec = QSpinBox()
        self._set_autosave_sec.setRange(5, 600)
        self._set_autosave_sec.setValue(self._settings.autosave_interval_sec)
        self._set_autosave_sec.setAlignment(Qt.AlignmentFlag.AlignRight)
        self._set_macros_dir = QLineEdit(self._settings.macros_folder)
        self._set_macros_dir.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._set_log_level = QComboBox()
        self._set_log_level.addItems([x.value for x in LogLevel])
        self._set_log_level.setCurrentText(self._settings.log_level.value)
        self._set_log_file = QCheckBox("Увімкнути")
        self._set_log_file.setChecked(self._settings.log_to_file)
        self._set_jitter = QDoubleSpinBox()
        self._set_jitter.setRange(0, 50)
        self._set_jitter.setValue(self._settings.jitter_percent)
        self._set_jitter.setAlignment(Qt.AlignmentFlag.AlignRight)

        c1, l1 = self._settings_card("Загальні")
        l1.addWidget(self._settings_inline_row("Тема", self._set_theme))
        l1.addWidget(self._settings_inline_row("Мова інтерфейсу", self._set_lang))

        c2, l2 = self._settings_card("Поведінка")
        ch_wrap = QWidget()
        ch_l = QGridLayout(ch_wrap)
        ch_l.setContentsMargins(0, 0, 0, 0)
        ch_l.setHorizontalSpacing(12)
        ch_l.setVerticalSpacing(3)
        ch_l.addWidget(self._set_top, 0, 0)
        ch_l.addWidget(self._set_sound, 0, 1)
        ch_l.addWidget(self._set_tray, 1, 0)
        ch_l.addWidget(self._set_close_tray, 1, 1)
        ch_l.setColumnStretch(0, 1)
        ch_l.setColumnStretch(1, 1)
        l2.addWidget(self._settings_inline_row("Вікно та трей", ch_wrap))
        l2.addWidget(self._settings_inline_row("Глобальні клавіші (бекенд)", self._set_hk_backend))
        l2.addWidget(self._settings_inline_row("Прозорість оверлею", self._set_overlay_op))

        c3, l3 = self._settings_card("Автоклік / макроси")
        as_row = QWidget()
        as_h = QHBoxLayout(as_row)
        as_h.setContentsMargins(0, 0, 0, 0)
        as_h.setSpacing(6)
        as_h.addWidget(self._set_autosave)
        il_as = QLabel("Інтервал (с)")
        il_as.setObjectName("formInlineLabel")
        as_h.addWidget(il_as)
        as_h.addWidget(self._set_autosave_sec)
        as_h.addStretch(1)
        l3.addWidget(self._settings_inline_row("Автозбереження макросу", as_row))
        l3.addWidget(self._settings_inline_row("Папка макросів (порожньо = типова)", self._set_macros_dir))
        l3.addWidget(self._settings_inline_row("Jitter % (загальний)", self._set_jitter))

        c4, l4 = self._settings_card("Логування")
        l4.addWidget(self._settings_inline_row("Рівень логу", self._set_log_level))
        l4.addWidget(self._settings_inline_row("Лог у файл", self._set_log_file))

        self._field_max_width(self._set_theme, FORM_COMBO_MAX_W)
        self._field_max_width(self._set_hk_backend, FORM_COMBO_MAX_W)
        self._field_max_width(self._set_overlay_op, SETTINGS_NUM_FIELD_MAX_W)
        self._field_max_width(self._set_autosave_sec, 120)
        self._field_max_width(self._set_log_level, FORM_COMBO_MAX_W)
        self._field_max_width(self._set_lang, FORM_COMBO_MAX_W)
        self._field_max_width(self._set_jitter, SETTINGS_NUM_FIELD_MAX_W)

        binds = self._build_binds_section()
        body = _ResponsiveSettingsBody(
            c1,
            c2,
            c3,
            c4,
            binds,
            breakpoint_w=SETTINGS_GRID_BREAKPOINT_W,
        )
        body_wrap = QWidget()
        body_wrap_lay = QHBoxLayout(body_wrap)
        body_wrap_lay.setContentsMargins(0, 0, 0, 0)
        body_wrap_lay.setSpacing(0)
        body_wrap_lay.addStretch(1)
        body_wrap_lay.addWidget(body)
        body_wrap_lay.addStretch(1)
        vl.addWidget(body_wrap)

        scroll.setWidget(inner)
        outer_lay.addWidget(scroll)
        return outer

    def _save_settings_ui(self) -> None:
        self._settings.theme = ThemeMode.DARK if self._set_theme.currentIndex() == 0 else ThemeMode.LIGHT
        _ld = self._set_lang.currentData()
        self._settings.ui_language = (
            str(_ld) if _ld is not None else normalize_ui_language(self._set_lang.currentText())
        )
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
        bind_cfg = self._read_binds_from_ui()
        bind_errs = validate_bindings(bind_cfg)
        if bind_errs:
            QMessageBox.warning(self, "Бинди", "\n".join(bind_errs))
            return
        self._settings.bindings = bind_cfg
        save_settings(self._settings)
        self._presenter.notify_settings_saved()
        self._apply_theme()
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, self._settings.always_on_top)
        self._apply_no_maximize_button()
        self.show()
        self._logging_service.configure(
            self._settings.log_level,
            self._settings.log_to_file,
            lambda m: self.append_log.emit(m),
        )
        if self._settings.minimize_to_tray:
            self._tray.show()
        else:
            self._tray.hide()
        self._overlay.set_opacity(self._settings.overlay_opacity)
        self._apply_hotkeys()
        self._update_ac_button_hotkey_labels()
        logging.getLogger(__name__).info("Налаштування збережено")

    def _build_kb_tab(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setSpacing(10)
        lay.setContentsMargins(0, 0, 0, 0)
        self._kb_panel = KeyboardTestPanel(self._settings.theme, self._settings.ui_language)
        self._mouse_panel = MouseTestPanel(self._settings.theme, self._settings.ui_language)
        lay.addWidget(self._kb_panel, 0)
        lay.addWidget(self._mouse_panel, 0)
        lay.addStretch(1)
        return w

    def _on_nav_id_clicked(self, idx: int) -> None:
        self._stack.setCurrentIndex(idx)
        self._on_nav_changed(idx)

    def _on_nav_changed(self, idx: int) -> None:
        if idx < 0:
            return
        if hasattr(self, "_header_actions_stack"):
            self._header_actions_stack.setCurrentIndex(idx)
        if idx == _NAV_INDEX_KEYBOARD_TEST:
            self._kb_hooks.start()
            self._kb_panel.set_layout_tracking(True)
        else:
            self._kb_hooks.stop()
            self._kb_panel.set_layout_tracking(False)

    def _on_test_key(self, name: str, down: bool) -> None:
        kid = self._kb_panel.normalize(name)
        if kid:
            self._kb_panel.set_key_active(kid, down)
            if down:
                self._kb_panel.record_key_press(kid)

    def _on_test_mouse_btn(self, name: str, down: bool) -> None:
        self._mouse_panel.set_btn(name, down)

    def _on_test_mouse_pos(self, x: int, y: int) -> None:
        self._mouse_panel.set_pos(x, y)

    def _on_test_scroll(self, dx: int, dy: int) -> None:
        self._mouse_panel.set_scroll(dx, dy)

    def _append_log_slot(self, msg: str) -> None:
        self._log_edit.append(msg)

    def _footer_copyright_html(self, lang: str) -> str:
        from app.models.settings import ThemeMode

        L = normalize_ui_language(lang)
        rights = tr(L, "app.footer_rights")
        year = datetime.now().year
        if self._settings.theme == ThemeMode.LIGHT:
            muted, link_c = "#64748B", "#DC2626"
        else:
            muted, link_c = "#94A3B8", "#FB7185"
        return (
            f'<span style="color:{muted};font-weight:600;font-size:12px;letter-spacing:0.02em;">© {year} </span>'
            f'<a href="{STUDIO_URL}" style="color:{link_c};font-weight:600;text-decoration:none;">FLOWAXY SOFTWARE</a>'
            f'<span style="color:{muted};font-weight:600;font-size:12px;letter-spacing:0.02em;"> · {rights} · v{APP_VERSION}</span>'
        )

    def _retranslate_ui(self) -> None:
        L = normalize_ui_language(self._settings.ui_language)
        wt = format_window_title(tr(L, "app.product_subtitle"))
        self.setWindowTitle(wt)
        app_inst = QApplication.instance()
        if app_inst is not None:
            app_inst.setApplicationDisplayName(wt)
        self._overlay.setWindowTitle(wt)
        if getattr(self._tray, "_tray", None):
            self._tray.set_tooltip(wt)
        self._lbl_brand_product.setText(tr(L, "app.product_subtitle"))
        self._lbl_brand_blurb.setText(tr(L, "app.blurb"))
        self._lbl_brand_sec_feat.setText(tr(L, "app.about_features_title"))
        self._lbl_brand_feat.setText(tr(L, "app.about_features"))
        self._lbl_brand_hint.setText(tr(L, "app.disclaimer"))
        for btn, tip_key in self._brand_social_tooltips:
            btn.setToolTip(tr(L, tip_key))
        self._footer_info.setText(self._footer_copyright_html(L))
        for i, nk in enumerate(_NAV_KEYS):
            b = self._nav_group.button(i)
            if b:
                b.setText(_ICON_TEXT_GAP + tr(L, nk))

    def _apply_theme(self) -> None:
        self.setStyleSheet(stylesheet_for(self._settings.theme))
        sync_themed_checkboxes(self, self._settings.theme)
        self._refresh_ui_icons()
        self._retranslate_ui()
        if hasattr(self, "_kb_panel"):
            self._kb_panel.set_theme(self._settings.theme)
            self._kb_panel.set_ui_language(self._settings.ui_language)
        if hasattr(self, "_mouse_panel"):
            self._mouse_panel.set_theme(self._settings.theme)
            self._mouse_panel.set_ui_language(self._settings.ui_language)

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
        self._footer_status.setProperty("state", "idle")
        self._btn_start.setProperty("state", "")
        self._btn_pause.setProperty("state", "")
        self._btn_stop.setProperty("state", "")
        st = self._active_autoclick_state()
        ms = self._macro_engine.get_state()
        if ms == AppRunState.PLAYING_MACRO:
            self._footer_status.setText("Стан: відтворення макросу")
            self._footer_status.setProperty("state", "macro")
        elif st == AutoclickState.RUNNING:
            self._footer_status.setText("Стан: автоклікер активний")
            self._footer_status.setProperty("state", "running")
            self._btn_start.setProperty("state", "on")
            self._btn_stop.setProperty("state", "danger")
        elif st == AutoclickState.PAUSED:
            self._footer_status.setText("Стан: пауза")
            self._footer_status.setProperty("state", "paused")
            self._btn_pause.setProperty("state", "paused")
            self._btn_stop.setProperty("state", "danger")
        else:
            self._footer_status.setText("Стан: зупинено")
        for w in (self._footer_status, self._btn_start, self._btn_pause, self._btn_stop):
            w.style().unpolish(w)
            w.style().polish(w)
        self._update_overlay_visibility()

    def _apply_hotkeys(self) -> None:
        cb = {
            "toggle_autoclick": self._hk_toggle_ac,
            "pause_autoclick": self._hk_pause_ac,
            "toggle_macro_play": self._hk_toggle_macro_play,
            "toggle_record_macro": self._hk_toggle_rec,
            "toggle_tray": self._hk_toggle_tray,
            "emergency_stop": self._emergency,
        }
        hwnd = 0
        if sys.platform == "win32" and self.isVisible():
            try:
                hwnd = int(self.winId())
            except Exception:
                hwnd = 0
        self._hotkey_manager.apply(
            backend=self._settings.hotkey_backend,
            hwnd=hwnd,
            bindings=self._settings.bindings,
            callbacks=cb,
            log=logging.getLogger(__name__),
        )

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
        self._clicker.stop_all()
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
                        self._hotkey_manager.dispatch_win32_hotkey(int(msg.wParam))
                        return True, 0
            except Exception:
                logging.getLogger(__name__).debug("nativeEvent", exc_info=True)
        return super().nativeEvent(eventType, message)

    def changeEvent(self, event: QEvent) -> None:
        if event.type() == QEvent.Type.WindowStateChange:
            if self.windowState() & Qt.WindowState.WindowMaximized:
                self.showNormal()
                event.accept()
                return
            if self._settings.minimize_to_tray and self.isMinimized():
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
        self._hotkey_manager.stop()
        self._clicker.stop_all()
        self._macro_engine.stop()
        self._kb_hooks.stop()
        self._kb_panel.set_layout_tracking(False)
        self._overlay.hide()
        if self._capture:
            self._capture.stop()
        save_settings(self._settings)
        event.accept()
        QApplication.quit()
