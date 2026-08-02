"""The one place the domain and Qt threading models meet (ADR-0005).

Domain events are published on whichever thread did the work — a scheduler
thread, a worker thread, a tool thread. Qt widgets may only be touched from the
GUI thread.

:class:`EventBridge` subscribes to the bus once and re-emits each event as a Qt
signal. Because the bridge lives in the GUI thread and the connection type is
``AutoConnection``, an emission from another thread is queued and delivered on
the GUI thread. Nothing else in ``jarvis.ui`` subscribes to the bus directly.
"""

from __future__ import annotations

from PySide6.QtCore import QObject, Signal

from jarvis.core.events.bus import EventBus, Subscription
from jarvis.core.events.types import Event

__all__ = ["EventBridge"]


class EventBridge(QObject):
    """Re-emits domain events as Qt signals on the GUI thread."""

    #: Every event, in publication order per thread.
    eventReceived = Signal(object)

    def __init__(self, bus: EventBus, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._bus = bus
        self._subscription: Subscription | None = bus.subscribe(Event, self._on_event)

    def _on_event(self, event: Event) -> None:
        # Called on the publishing thread. Emitting is thread-safe; delivery is
        # queued onto the thread this QObject lives in.
        self.eventReceived.emit(event)

    def detach(self) -> None:
        if self._subscription is not None:
            self._subscription.unsubscribe()
            self._subscription = None

    @property
    def attached(self) -> bool:
        return self._subscription is not None and self._subscription.active
