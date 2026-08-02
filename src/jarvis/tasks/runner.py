"""What a task actually does.

Runners are the extension point that later phases plug work into. Phase 0 ships
one (the health-check runner in ``jarvis.toolbox``); everything else the
scheduler needs is here.

Cooperative control is the contract: a runner must call
:meth:`TaskRunContext.should_stop` at every point where stopping is safe, and
:meth:`TaskRunContext.checkpoint` at every point it could resume from. A runner
that never yields cannot be paused, which is a bug in the runner, not in the
scheduler.
"""

from __future__ import annotations

import threading
from enum import Enum
from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field

from jarvis.tasks.models import Task, TaskCheckpoint
from jarvis.tasks.states import TaskState

__all__ = ["StopReason", "TaskRunContext", "TaskOutcome", "TaskRunner"]


class StopReason(str, Enum):
    """Why a runner was asked to stop."""

    NONE = "none"
    PAUSE = "pause"
    CANCEL = "cancel"
    SHUTDOWN = "shutdown"


class TaskOutcome(BaseModel):
    """What a runner reports when it returns."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    state: TaskState = Field(description="One of succeeded, failed, waiting or blocked.")
    summary: str = ""
    failure_code: str | None = None
    retryable: bool = False
    waiting_on: str | None = None
    blocked_reason: str | None = None
    evidence: tuple[dict[str, Any], ...] = ()

    def model_post_init(self, _context: Any) -> None:
        permitted = {
            TaskState.SUCCEEDED,
            TaskState.FAILED,
            TaskState.WAITING,
            TaskState.BLOCKED,
        }
        if self.state not in permitted:
            raise ValueError(
                f"a runner may only report {sorted(s.value for s in permitted)}, "
                f"not '{self.state.value}'"
            )


class TaskRunContext:
    """Everything a runner is allowed to touch. No ambient authority."""

    def __init__(
        self,
        task: Task,
        store: Any,
        *,
        pause_event: threading.Event,
        cancel_event: threading.Event,
        shutdown_event: threading.Event,
    ) -> None:
        self.task = task
        self._store = store
        self._pause = pause_event
        self._cancel = cancel_event
        self._shutdown = shutdown_event

    # -- cooperative control ----------------------------------------------
    def stop_reason(self) -> StopReason:
        if self._cancel.is_set():
            return StopReason.CANCEL
        if self._shutdown.is_set():
            return StopReason.SHUTDOWN
        if self._pause.is_set():
            return StopReason.PAUSE
        return StopReason.NONE

    def should_stop(self) -> bool:
        """Call this at every safe point. Pause lands here (PRD FR-125)."""
        return self.stop_reason() is not StopReason.NONE

    @property
    def cancel_event(self) -> threading.Event:
        return self._cancel

    # -- durability --------------------------------------------------------
    def checkpoint(self, label: str, state: dict[str, Any] | None = None) -> TaskCheckpoint:
        """Persist a resume point (PRD FR-128)."""
        return self._store.save_checkpoint(self.task.task_id, label, state)

    def last_checkpoint(self) -> TaskCheckpoint | None:
        return self._store.latest_checkpoint(self.task.task_id)

    def add_evidence(
        self,
        kind: str,
        summary: str,
        detail: dict[str, Any] | None = None,
        artefact_path: str | None = None,
    ) -> None:
        """Record support for a completion claim (PRD FR-132)."""
        self._store.add_evidence(
            self.task.task_id, kind, summary, detail=detail, artefact_path=artefact_path
        )

    def progress(self, message: str) -> None:
        """Report a milestone. Visible in the Tasks screen (PRD FR-131)."""
        self._store.update(self.task.task_id, waiting_on=message)


@runtime_checkable
class TaskRunner(Protocol):
    """A registered unit of work."""

    runner_id: str

    def run(self, context: TaskRunContext) -> TaskOutcome:
        ...
