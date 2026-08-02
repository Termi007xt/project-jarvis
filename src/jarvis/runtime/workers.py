"""Worker threads and their supervisor (PRD NFR-003, ARCHITECTURE.md section 4.1).

The rule this module exists to keep: audio capture, model inference, automation
and long I/O never run on the Qt main thread. Phase 0 has one real worker (the
periodic health check); Phase 1's audio pipeline and Phase 2's automation
pipeline subclass :class:`Worker` and inherit the same lifecycle.

Every worker must stop cooperatively. ``stop()`` sets an event and joins with a
timeout; a worker that ignores it is reported as failing to stop rather than
being killed, because a half-killed automation thread is worse than a slow
shutdown.
"""

from __future__ import annotations

import logging
import threading
from abc import ABC, abstractmethod
from typing import Callable

from jarvis.core.events.bus import EventBus
from jarvis.core.events.types import WorkerStateChanged

__all__ = ["Worker", "PeriodicWorker", "WorkerSupervisor"]

_LOG = logging.getLogger(__name__)


class Worker(ABC):
    """A named background thread with a cooperative stop."""

    def __init__(self, name: str, event_bus: EventBus | None = None) -> None:
        self.name = name
        self._events = event_bus
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._failure: BaseException | None = None

    # -- lifecycle ---------------------------------------------------------
    def start(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop.clear()
        self._failure = None
        self._publish("starting")
        self._thread = threading.Thread(target=self._main, name=f"jarvis-{self.name}", daemon=True)
        self._thread.start()

    def stop(self, timeout_seconds: float = 5.0) -> bool:
        """Signal and wait. Returns ``True`` when the thread actually stopped."""
        self._stop.set()
        thread = self._thread
        if thread is None:
            self._publish("stopped")
            return True
        self._publish("stopping")
        thread.join(timeout=timeout_seconds)
        stopped = not thread.is_alive()
        if stopped:
            self._thread = None
            self._publish("stopped")
        else:
            self._publish("failed", f"'{self.name}' did not stop within {timeout_seconds}s")
        return stopped

    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    @property
    def failure(self) -> BaseException | None:
        return self._failure

    @property
    def stop_requested(self) -> bool:
        return self._stop.is_set()

    def wait(self, seconds: float) -> bool:
        """Sleep, but wake immediately on stop. Returns ``True`` if stopping."""
        return self._stop.wait(seconds)

    # -- implementation ----------------------------------------------------
    def _main(self) -> None:
        self._publish("running")
        try:
            self.work()
        except BaseException as exc:  # noqa: BLE001 - report rather than vanish
            self._failure = exc
            _LOG.exception("worker %s failed", self.name)
            self._publish("failed", f"{type(exc).__name__}: {exc}")

    @abstractmethod
    def work(self) -> None:
        """Run until :attr:`stop_requested`. Check it often."""

    def _publish(self, state: str, detail: str | None = None) -> None:
        if self._events is not None:
            self._events.publish(
                WorkerStateChanged(
                    source="workers",
                    worker_name=self.name,
                    state=state,  # type: ignore[arg-type]
                    detail=detail,
                )
            )


class PeriodicWorker(Worker):
    """Calls a function on an interval until stopped."""

    def __init__(
        self,
        name: str,
        interval_seconds: float,
        action: Callable[[], object],
        event_bus: EventBus | None = None,
        *,
        run_immediately: bool = True,
    ) -> None:
        super().__init__(name, event_bus)
        self._interval = max(0.05, interval_seconds)
        self._action = action
        self._run_immediately = run_immediately

    def work(self) -> None:
        if self._run_immediately:
            self._invoke()
        while not self.wait(self._interval):
            self._invoke()

    def _invoke(self) -> None:
        try:
            self._action()
        except Exception:  # noqa: BLE001 - one bad tick must not kill the worker
            _LOG.exception("periodic worker %s raised", self.name)


class WorkerSupervisor:
    """Starts and stops workers in a defined order."""

    def __init__(self, event_bus: EventBus | None = None) -> None:
        self._events = event_bus
        self._workers: list[Worker] = []
        self._lock = threading.RLock()

    def add(self, worker: Worker) -> Worker:
        with self._lock:
            if any(existing.name == worker.name for existing in self._workers):
                raise ValueError(f"a worker named '{worker.name}' is already supervised")
            self._workers.append(worker)
        return worker

    def start_all(self) -> None:
        with self._lock:
            workers = list(self._workers)
        for worker in workers:
            worker.start()

    def stop_all(self, timeout_seconds: float = 5.0) -> tuple[str, ...]:
        """Stop in reverse order. Returns the names that stopped cleanly."""
        with self._lock:
            workers = list(reversed(self._workers))
        stopped: list[str] = []
        for worker in workers:
            if worker.stop(timeout_seconds):
                stopped.append(worker.name)
            else:
                _LOG.error("worker %s did not stop within %.1fs", worker.name, timeout_seconds)
        return tuple(stopped)

    @property
    def names(self) -> tuple[str, ...]:
        with self._lock:
            return tuple(worker.name for worker in self._workers)

    def running_names(self) -> tuple[str, ...]:
        with self._lock:
            return tuple(worker.name for worker in self._workers if worker.running)

    def __len__(self) -> int:
        with self._lock:
            return len(self._workers)
