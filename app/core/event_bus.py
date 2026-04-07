"""In-process synchronous event bus for decoupling UI from core."""

from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable


class EventType(str, Enum):
    CLICK_STARTED = "click_started"
    CLICK_STOPPED = "click_stopped"
    CLICK_PAUSED = "click_paused"
    CLICK_RESUMED = "click_resumed"
    MACRO_RECORD_STARTED = "macro_record_started"
    MACRO_RECORD_STOPPED = "macro_record_stopped"
    MACRO_PLAY_STARTED = "macro_play_started"
    MACRO_PLAY_STOPPED = "macro_play_stopped"
    KEY_CHORD = "key_chord"
    SETTINGS_SAVED = "settings_saved"
    ERROR = "error"
    UPDATE_AVAILABLE = "update_available"


@dataclass(frozen=True)
class AppEvent:
    type: EventType
    payload: Any = None


Handler = Callable[[AppEvent], None]


class EventBus:
    def __init__(self) -> None:
        self._subs: dict[EventType, list[Handler]] = defaultdict(list)
        self._log = logging.getLogger(__name__)

    def subscribe(self, kind: EventType, handler: Handler) -> None:
        self._subs[kind].append(handler)

    def unsubscribe(self, kind: EventType, handler: Handler) -> None:
        lst = self._subs.get(kind)
        if not lst or handler not in lst:
            return
        lst.remove(handler)

    def publish(self, event: AppEvent) -> None:
        for h in list(self._subs.get(event.type, [])):
            try:
                h(event)
            except Exception:
                self._log.exception("Event handler failed for %s", event.type)
