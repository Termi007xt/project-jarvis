"""Typed event bus (ADR-0005)."""

from __future__ import annotations

import threading

import pytest

from jarvis.core.events.bus import EventBus
from jarvis.core.events.types import (
    AppStarted,
    Event,
    TaskStateChanged,
    ToolInvocationFinished,
)


def _app_started() -> AppStarted:
    return AppStarted(
        instance_id="i",
        app_version="0.0.0",
        schema_version=1,
        vault_root="C:/vault",
        network_mode="offline",
    )


def test_subscriber_receives_its_event_type() -> None:
    bus = EventBus()
    received: list[Event] = []
    bus.subscribe(AppStarted, received.append)
    bus.publish(_app_started())
    assert len(received) == 1


def test_subclass_matching_means_event_sees_everything() -> None:
    bus = EventBus()
    everything: list[Event] = []
    bus.subscribe(Event, everything.append)

    bus.publish(_app_started())
    bus.publish(TaskStateChanged(task_id="t", from_state="queued", to_state="running"))
    assert len(everything) == 2


def test_a_subscriber_does_not_receive_unrelated_events() -> None:
    bus = EventBus()
    tasks: list[Event] = []
    bus.subscribe(TaskStateChanged, tasks.append)
    bus.publish(_app_started())
    assert tasks == []


def test_a_failing_handler_does_not_break_the_publisher_or_others() -> None:
    """The audit log and the GUI both subscribe; one must not break the other."""
    bus = EventBus()
    survivor: list[Event] = []

    def explode(_event: Event) -> None:
        raise RuntimeError("subscriber is broken")

    bus.subscribe(Event, explode)
    bus.subscribe(Event, survivor.append)

    delivered = bus.publish(_app_started())  # must not raise
    assert delivered == 2
    assert len(survivor) == 1
    assert bus.handler_error_count == 1


def test_unsubscribe_stops_delivery() -> None:
    bus = EventBus()
    received: list[Event] = []
    subscription = bus.subscribe(Event, received.append)

    bus.publish(_app_started())
    subscription.unsubscribe()
    bus.publish(_app_started())

    assert len(received) == 1
    assert not subscription.active
    assert bus.subscriber_count == 0


def test_unsubscribe_is_idempotent() -> None:
    bus = EventBus()
    subscription = bus.subscribe(Event, lambda _e: None)
    subscription.unsubscribe()
    subscription.unsubscribe()
    assert bus.subscriber_count == 0


def test_publishing_a_non_event_is_rejected() -> None:
    bus = EventBus()
    with pytest.raises(TypeError):
        bus.publish("not an event")  # type: ignore[arg-type]


def test_subscribing_to_a_non_event_type_is_rejected() -> None:
    bus = EventBus()
    with pytest.raises(TypeError):
        bus.subscribe(str, lambda _e: None)  # type: ignore[arg-type]


def test_publishing_is_thread_safe() -> None:
    bus = EventBus()
    received: list[Event] = []
    lock = threading.Lock()

    def collect(event: Event) -> None:
        with lock:
            received.append(event)

    bus.subscribe(Event, collect)

    def publisher() -> None:
        for _ in range(50):
            bus.publish(
                ToolInvocationFinished(
                    invocation_id="i", tool_id="t", outcome="succeeded", verification="verified"
                )
            )

    threads = [threading.Thread(target=publisher) for _ in range(4)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert len(received) == 200
    assert bus.published_count == 200


def test_events_are_immutable() -> None:
    event = _app_started()
    with pytest.raises(Exception):
        event.instance_id = "changed"  # type: ignore[misc]


def test_events_carry_identity_and_time() -> None:
    first, second = _app_started(), _app_started()
    assert first.event_id != second.event_id
    assert first.occurred_at.tzinfo is not None
