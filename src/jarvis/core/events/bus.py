"""In-process typed event bus (ADR-0005).

Deliberately not a message broker: no persistence, no retry, no cross-thread
ordering guarantee. Handlers run on the publishing thread. A handler that raises
is logged and isolated so one bad subscriber cannot break the publisher, the
audit log, or the other subscribers.
"""

from __future__ import annotations

import logging
import threading
from typing import Callable, TypeVar

from jarvis.core.events.types import Event

__all__ = ["EventBus", "Subscription"]

_LOG = logging.getLogger(__name__)

E = TypeVar("E", bound=Event)
Handler = Callable[[Event], None]


class Subscription:
    """Handle returned by :meth:`EventBus.subscribe`. Call it to unsubscribe."""

    __slots__ = ("_unsubscribe", "_active")

    def __init__(self, unsubscribe: Callable[[], None]) -> None:
        self._unsubscribe = unsubscribe
        self._active = True

    def __call__(self) -> None:
        self.unsubscribe()

    def unsubscribe(self) -> None:
        if self._active:
            self._active = False
            self._unsubscribe()

    @property
    def active(self) -> bool:
        return self._active


class EventBus:
    """Thread-safe publish/subscribe with subclass matching."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._handlers: dict[type[Event], list[Handler]] = {}
        self._published_count = 0
        self._handler_error_count = 0

    def subscribe(self, event_type: type[E], handler: Callable[[E], None]) -> Subscription:
        """Receive ``event_type`` and every subclass of it."""
        if not (isinstance(event_type, type) and issubclass(event_type, Event)):
            raise TypeError(f"{event_type!r} is not an Event subclass")

        typed_handler: Handler = handler  # type: ignore[assignment]
        with self._lock:
            self._handlers.setdefault(event_type, []).append(typed_handler)

        def _remove() -> None:
            with self._lock:
                handlers = self._handlers.get(event_type)
                if handlers and typed_handler in handlers:
                    handlers.remove(typed_handler)
                    if not handlers:
                        del self._handlers[event_type]

        return Subscription(_remove)

    def publish(self, event: Event) -> int:
        """Deliver to every matching handler. Returns the number invoked.

        Handler exceptions are swallowed and counted, never propagated: a
        publisher must not fail because a subscriber is broken.
        """
        if not isinstance(event, Event):
            raise TypeError(f"{type(event).__name__} is not an Event")

        with self._lock:
            self._published_count += 1
            matching: list[Handler] = []
            for registered_type, handlers in self._handlers.items():
                if isinstance(event, registered_type):
                    matching.extend(handlers)

        for handler in matching:
            try:
                handler(event)
            except Exception:  # noqa: BLE001 - isolation is the point
                with self._lock:
                    self._handler_error_count += 1
                _LOG.exception(
                    "event handler %r failed for %s",
                    getattr(handler, "__qualname__", handler),
                    type(event).__name__,
                )
        return len(matching)

    def clear(self) -> None:
        with self._lock:
            self._handlers.clear()

    @property
    def published_count(self) -> int:
        with self._lock:
            return self._published_count

    @property
    def handler_error_count(self) -> int:
        with self._lock:
            return self._handler_error_count

    @property
    def subscriber_count(self) -> int:
        with self._lock:
            return sum(len(handlers) for handlers in self._handlers.values())
