from app.core.event_bus import AppEvent, EventBus, EventType


def test_event_bus_publish_subscribe() -> None:
    bus = EventBus()
    seen: list[EventType] = []

    def h(ev: AppEvent) -> None:
        seen.append(ev.type)

    bus.subscribe(EventType.CLICK_STARTED, h)
    bus.publish(AppEvent(EventType.CLICK_STARTED))
    assert seen == [EventType.CLICK_STARTED]
