"""Centralized logging to UI and optional file."""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Callable

from app.models.settings import LogLevel
from app.utils.paths import config_dir


class UiLogHandler(logging.Handler):
    def __init__(self, emit_ui: Callable[[str], None]) -> None:
        super().__init__()
        self._emit_ui = emit_ui

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
            self._emit_ui(msg)
        except Exception:
            pass


def setup_logging(
    level: LogLevel,
    to_file: bool,
    ui_emit: Callable[[str], None] | None,
) -> None:
    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(getattr(logging, level.value, logging.INFO))

    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", "%H:%M:%S")
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(fmt)
    root.addHandler(sh)

    if ui_emit:
        uh = UiLogHandler(ui_emit)
        uh.setFormatter(fmt)
        root.addHandler(uh)

    if to_file:
        log_path = config_dir() / "app.log"
        fh = logging.FileHandler(log_path, encoding="utf-8")
        fh.setFormatter(fmt)
        root.addHandler(fh)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
