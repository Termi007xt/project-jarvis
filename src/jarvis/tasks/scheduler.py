"""Task scheduler (ARCHITECTURE.md section 6.7).

One background thread selects queued tasks, arbitrates resource locks and
dispatches acquirable work to a bounded runner pool.

The property that matters: a task whose locks are unavailable stays ``QUEUED``
with a visible ``waiting_on`` reason. Two tasks that both need the foreground
desktop never run together — one runs and the other waits, observably (PRD
section 7.1, AT-009).
"""

from __future__ import annotations

import logging
import threading
from concurrent.futures import Future, ThreadPoolExecutor
from typing import Any

from jarvis.core.audit.log import AuditLog
from jarvis.core.audit.models import AuditCategory
from jarvis.core.events.bus import EventBus
from jarvis.storage.database import DatabaseError
from jarvis.tasks.locks import LockSetLease, ResourceLockManager
from jarvis.tasks.models import Task
from jarvis.tasks.runner import StopReason, TaskOutcome, TaskRunContext, TaskRunner
from jarvis.tasks.states import TERMINAL_STATES, TaskState
from jarvis.tasks.store import TaskStore

__all__ = ["TaskScheduler", "SchedulerError"]

_LOG = logging.getLogger(__name__)


class SchedulerError(Exception):
    """The scheduler was asked to do something it cannot."""


class _TaskControl:
    __slots__ = ("pause", "cancel", "future", "lease")

    def __init__(self) -> None:
        self.pause = threading.Event()
        self.cancel = threading.Event()
        self.future: Future[None] | None = None
        self.lease: LockSetLease | None = None


class TaskScheduler:
    """Queue, lock arbitration, cooperative pause/cancel and bounded retries."""

    def __init__(
        self,
        store: TaskStore,
        locks: ResourceLockManager,
        *,
        audit: AuditLog | None = None,
        event_bus: EventBus | None = None,
        max_concurrent: int = 2,
        poll_interval_seconds: float = 0.1,
        lock_timeout_seconds: float = 0.0,
    ) -> None:
        self._store = store
        self._locks = locks
        self._audit = audit
        self._events = event_bus
        self._max_concurrent = max(1, max_concurrent)
        self._poll_interval = poll_interval_seconds
        self._lock_timeout = lock_timeout_seconds

        self._runners: dict[str, TaskRunner] = {}
        self._controls: dict[str, _TaskControl] = {}
        self._state_lock = threading.RLock()
        self._shutdown = threading.Event()
        self._wake = threading.Event()
        self._thread: threading.Thread | None = None
        self._executor: ThreadPoolExecutor | None = None

    # -- registration ------------------------------------------------------
    def register_runner(self, runner: TaskRunner) -> None:
        with self._state_lock:
            if runner.runner_id in self._runners:
                raise SchedulerError(f"runner '{runner.runner_id}' is already registered")
            self._runners[runner.runner_id] = runner

    def runner_ids(self) -> tuple[str, ...]:
        with self._state_lock:
            return tuple(sorted(self._runners))

    # -- lifecycle ---------------------------------------------------------
    def start(self) -> None:
        with self._state_lock:
            if self._thread is not None:
                return
            self._shutdown.clear()
            self._executor = ThreadPoolExecutor(
                max_workers=self._max_concurrent, thread_name_prefix="jarvis-task"
            )
            self._thread = threading.Thread(
                target=self._loop, name="jarvis-scheduler", daemon=True
            )
            self._thread.start()

    def stop(self, timeout_seconds: float = 10.0) -> None:
        """Signal every runner to stop, then wait for in-flight work."""
        self._shutdown.set()
        self._wake.set()
        with self._state_lock:
            thread, executor = self._thread, self._executor
            self._thread, self._executor = None, None
        if thread is not None:
            thread.join(timeout=timeout_seconds)
        if executor is not None:
            executor.shutdown(wait=True, cancel_futures=True)

    @property
    def running(self) -> bool:
        with self._state_lock:
            return self._thread is not None and self._thread.is_alive()

    def nudge(self) -> None:
        """Wake the loop immediately instead of waiting for the next poll."""
        self._wake.set()

    # -- queueing ----------------------------------------------------------
    def submit(self, task: Task, reason: str = "queued for execution") -> Task:
        """Move a task into the queue. Does not run it."""
        with self._state_lock:
            if task.runner_id not in self._runners:
                raise SchedulerError(
                    f"no runner registered for '{task.runner_id}'; "
                    f"registered runners are {sorted(self._runners)}"
                )
        queued = self._store.transition(task.task_id, TaskState.QUEUED, reason=reason)
        self.nudge()
        return queued

    # -- control -----------------------------------------------------------
    def pause(self, task_id: str, reason: str = "paused by user") -> Task:
        """Cooperative pause. A running task stops at its next checkpoint."""
        task = self._store.require(task_id)
        if task.state is TaskState.QUEUED:
            return self._store.transition(task_id, TaskState.PAUSED, reason=reason, actor="user")
        if task.state in (TaskState.RUNNING, TaskState.WAITING):
            control = self._control_for(task_id)
            control.pause.set()
            return self._store.update(task_id, waiting_on="pausing at the next checkpoint")
        raise SchedulerError(f"cannot pause a task in state '{task.state.value}'")

    def resume(self, task_id: str, reason: str = "resumed by user") -> Task:
        """Resume re-queues the task; the runner re-observes before acting (FR-126)."""
        task = self._store.require(task_id)
        if task.state not in (TaskState.PAUSED, TaskState.BLOCKED):
            raise SchedulerError(f"cannot resume a task in state '{task.state.value}'")
        with self._state_lock:
            control = self._controls.get(task_id)
            if control is not None:
                control.pause.clear()
        resumed = self._store.transition(
            task_id, TaskState.QUEUED, reason=reason, actor="user", blocked_reason=None
        )
        self.nudge()
        return resumed

    def cancel(self, task_id: str, reason: str = "cancelled by user") -> Task:
        """Cancel. Releases locks; does not reverse completed external actions."""
        task = self._store.require(task_id)
        if task.state in TERMINAL_STATES:
            return task
        control = self._control_for(task_id)
        control.cancel.set()
        if task.state in (TaskState.RUNNING, TaskState.WAITING):
            # The runner stops at its next safe point and the loop finalises it.
            return self._store.update(task_id, waiting_on="cancelling at the next checkpoint")
        cancelled = self._store.transition(
            task_id, TaskState.CANCELLED, reason=reason, actor="user"
        )
        self._release(task_id)
        return cancelled

    def emergency_stop(self, reason: str = "emergency stop") -> tuple[str, ...]:
        """Cancel everything active and release every lock (PRD section 11.3)."""
        active = self._store.list(
            [TaskState.QUEUED, TaskState.RUNNING, TaskState.WAITING, TaskState.AWAITING_APPROVAL]
        )
        stopped: list[str] = []
        for task in active:
            try:
                control = self._control_for(task.task_id)
                control.cancel.set()
                if task.state in (TaskState.RUNNING, TaskState.WAITING):
                    self._store.update(task.task_id, waiting_on="emergency stop requested")
                else:
                    self._store.transition(
                        task.task_id, TaskState.CANCELLED, reason=reason, actor="user"
                    )
                stopped.append(task.task_id)
            except Exception:  # noqa: BLE001 - stop must not be stoppable
                _LOG.exception("emergency stop could not cancel task %s", task.task_id)

        if self._audit is not None:
            self._audit.record(
                AuditCategory.SECURITY,
                f"emergency stop cancelled {len(stopped)} task(s)",
                actor="user",
                parameters={"task_ids": stopped, "reason": reason},
            )
        return tuple(stopped)

    # -- the loop ----------------------------------------------------------
    def _loop(self) -> None:
        while not self._shutdown.is_set():
            try:
                self._tick()
            except DatabaseError:
                # The vault has gone away, which means the runtime is shutting
                # down or has crashed. Spinning on a closed database would fill
                # the log with identical failures and achieve nothing.
                _LOG.info("scheduler stopping: the database is no longer available")
                self._shutdown.set()
                break
            except Exception:  # noqa: BLE001 - one bad tick must not kill the scheduler
                _LOG.exception("scheduler tick failed")
            self._wake.wait(self._poll_interval)
            self._wake.clear()

        # Shutdown: signal every in-flight runner to stop cooperatively.
        with self._state_lock:
            for control in self._controls.values():
                control.pause.set()

    def _tick(self) -> None:
        with self._state_lock:
            in_flight = sum(
                1
                for control in self._controls.values()
                if control.future is not None and not control.future.done()
            )
            capacity = self._max_concurrent - in_flight
        if capacity <= 0:
            return

        for task in self._store.list([TaskState.QUEUED]):
            if capacity <= 0 or self._shutdown.is_set():
                return
            if self._dispatch(task):
                capacity -= 1

    def _dispatch(self, task: Task) -> bool:
        with self._state_lock:
            runner = self._runners.get(task.runner_id)
            if runner is None:
                self._store.transition(
                    task.task_id,
                    TaskState.BLOCKED,
                    reason="no registered runner",
                    blocked_reason=f"no runner registered for '{task.runner_id}'",
                )
                return False
            control = self._controls.setdefault(task.task_id, _TaskControl())
            if control.future is not None and not control.future.done():
                return False
            if control.cancel.is_set():
                self._store.transition(
                    task.task_id, TaskState.CANCELLED, reason="cancelled before start"
                )
                return False

        lease = self._locks.acquire(
            task.task_id, task.required_locks, timeout_seconds=self._lock_timeout
        )
        if lease is None:
            held_by = {
                name: self._locks.holder(name)
                for name in task.required_locks
                if self._locks.holder(name) not in (None, task.task_id)
            }
            self._store.update(
                task.task_id,
                waiting_on=(
                    "waiting for resource lock(s): "
                    + ", ".join(f"{name} (held by {owner})" for name, owner in held_by.items())
                ),
            )
            return False

        control.lease = lease
        running = self._store.transition(
            task.task_id,
            TaskState.RUNNING,
            reason="dispatched",
            attempts=task.attempts + 1,
            waiting_on=None,
        )

        executor = self._executor
        if executor is None:  # pragma: no cover - stop() raced with dispatch
            lease.release()
            return False
        control.future = executor.submit(self._run, runner, running, control)
        return True

    def _run(self, runner: TaskRunner, task: Task, control: _TaskControl) -> None:
        context = TaskRunContext(
            task,
            self._store,
            pause_event=control.pause,
            cancel_event=control.cancel,
            shutdown_event=self._shutdown,
        )
        try:
            outcome = runner.run(context)
        except Exception as exc:  # noqa: BLE001 - a runner fault is a task failure
            _LOG.exception("runner %s failed for task %s", runner.runner_id, task.task_id)
            outcome = TaskOutcome(
                state=TaskState.FAILED,
                summary=f"{type(exc).__name__}: {exc}",
                failure_code="runner_exception",
                retryable=False,
            )
        finally:
            self._release(task.task_id)

        try:
            self._finalise(task.task_id, outcome, context.stop_reason())
        except Exception:  # noqa: BLE001
            _LOG.exception("could not finalise task %s", task.task_id)
        self.nudge()

    def _finalise(self, task_id: str, outcome: TaskOutcome, stop_reason: StopReason) -> None:
        current = self._store.require(task_id)
        if current.state in TERMINAL_STATES:
            return

        for item in outcome.evidence:
            self._store.add_evidence(
                task_id,
                str(item.get("kind", "unspecified")),
                str(item.get("summary", "")),
                detail=item.get("detail"),
                artefact_path=item.get("artefact_path"),
            )

        # A stop request wins over a reported outcome: the runner was
        # interrupted, so whatever it returned is not a completed result.
        if stop_reason is StopReason.CANCEL:
            self._store.transition(
                task_id, TaskState.CANCELLED, reason="cancelled at checkpoint", actor="user"
            )
            return
        if stop_reason in (StopReason.PAUSE, StopReason.SHUTDOWN):
            self._store.transition(
                task_id,
                TaskState.PAUSED,
                reason=f"paused at checkpoint ({stop_reason.value})",
                actor="user" if stop_reason is StopReason.PAUSE else "system",
                waiting_on=None,
            )
            return

        if outcome.state is TaskState.SUCCEEDED:
            self._store.transition(
                task_id,
                TaskState.SUCCEEDED,
                reason="completed",
                result_summary=outcome.summary,
                waiting_on=None,
            )
            return

        if outcome.state is TaskState.WAITING:
            self._store.transition(
                task_id,
                TaskState.WAITING,
                reason=outcome.waiting_on or "waiting",
                waiting_on=outcome.waiting_on,
            )
            return

        if outcome.state is TaskState.BLOCKED:
            self._store.transition(
                task_id,
                TaskState.BLOCKED,
                reason=outcome.blocked_reason or "blocked",
                blocked_reason=outcome.blocked_reason or outcome.summary,
                waiting_on=None,
            )
            return

        # Failed. Retry only if the runner said the failure is retryable and the
        # bound has not been reached (PRD FR-133, NFR-012).
        if outcome.retryable and current.attempts <= current.max_retries:
            self._store.transition(
                task_id,
                TaskState.QUEUED,
                reason=(
                    f"retrying after '{outcome.failure_code}' "
                    f"(attempt {current.attempts} of {current.max_retries + 1})"
                ),
                failure_code=outcome.failure_code,
                waiting_on=f"retry {current.attempts} of {current.max_retries + 1}",
            )
            return

        self._store.transition(
            task_id,
            TaskState.FAILED,
            reason=outcome.summary or "failed",
            failure_code=outcome.failure_code,
            result_summary=outcome.summary,
            waiting_on=None,
        )

    # -- helpers -----------------------------------------------------------
    def _control_for(self, task_id: str) -> _TaskControl:
        with self._state_lock:
            return self._controls.setdefault(task_id, _TaskControl())

    def _release(self, task_id: str) -> None:
        with self._state_lock:
            control = self._controls.get(task_id)
            lease = control.lease if control is not None else None
            if control is not None:
                control.lease = None
        if lease is not None:
            lease.release()
        else:
            self._locks.release(task_id)

    def status(self) -> dict[str, Any]:
        with self._state_lock:
            in_flight = [
                task_id
                for task_id, control in self._controls.items()
                if control.future is not None and not control.future.done()
            ]
        return {
            "running": self.running,
            "max_concurrent": self._max_concurrent,
            "in_flight": sorted(in_flight),
            "registered_runners": self.runner_ids(),
            "held_locks": [record.lock_name for record in self._locks.held()],
        }
