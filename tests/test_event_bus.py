from app.core.event_bus import AppEvent, EventBus, EventType


def test_event_bus_publish_subscribe() -> None:
    bus = EventBus()
    seen: list[EventType] = []

    def h(ev: AppEvent) -> None:
        seen.append(ev.type)

    bus.subscribe(EventType.CLICK_STARTED, h)
    bus.publish(AppEvent(EventType.CLICK_STARTED))
    assert seen == [EventType.CLICK_STARTED]


def test_event_bus_unsubscribe() -> None:
    bus = EventBus()
    seen: list[EventType] = []

    def h(ev: AppEvent) -> None:
        seen.append(ev.type)

    bus.subscribe(EventType.CLICK_STARTED, h)
    bus.unsubscribe(EventType.CLICK_STARTED, h)
    bus.publish(AppEvent(EventType.CLICK_STARTED))

    assert seen == []


def test_event_bus_continues_after_handler_error(caplog) -> None:
    bus = EventBus()
    seen: list[EventType] = []

    def bad(_: AppEvent) -> None:
        raise RuntimeError("boom")

    def good(ev: AppEvent) -> None:
        seen.append(ev.type)

    bus.subscribe(EventType.CLICK_STARTED, bad)
    bus.subscribe(EventType.CLICK_STARTED, good)

    bus.publish(AppEvent(EventType.CLICK_STARTED))

    assert seen == [EventType.CLICK_STARTED]
    assert "Event handler failed" in caplog.text
