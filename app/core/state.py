"""Runtime state enums."""

from __future__ import annotations

from enum import Enum, auto


class AutoclickState(Enum):
    STOPPED = auto()
    RUNNING = auto()
    PAUSED = auto()


class AppRunState(Enum):
    IDLE = auto()
    RECORDING_MACRO = auto()
    PLAYING_MACRO = auto()
