"""Application-wide logging configuration (UI + stdout + optional file)."""

from __future__ import annotations

import logging
from typing import Callable

from app.models.settings import LogLevel
from app.services.log_service import setup_logging


class LoggingService:
    """Thin wrapper around root logging setup for a single application instance."""

    def __init__(self) -> None:
        self._level = LogLevel.INFO
        self._to_file = False

    def configure(
        self,
        level: LogLevel,
        to_file: bool,
        ui_emit: Callable[[str], None] | None,
    ) -> None:
        self._level = level
        self._to_file = to_file
        setup_logging(level, to_file, ui_emit)

    def get_logger(self, name: str) -> logging.Logger:
        return logging.getLogger(name)
