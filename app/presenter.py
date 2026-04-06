"""Application-level orchestration (extend with logic moved from UI)."""

from __future__ import annotations

from app.core.event_bus import AppEvent, EventBus, EventType
from app.services.logging_service import LoggingService


class AppPresenter:
    def __init__(self, event_bus: EventBus, logging_service: LoggingService) -> None:
        self._bus = event_bus
        self._logging = logging_service

    @property
    def event_bus(self) -> EventBus:
        return self._bus

    @property
    def logging(self) -> LoggingService:
        return self._logging

    def notify_settings_saved(self) -> None:
        self._bus.publish(AppEvent(EventType.SETTINGS_SAVED))
