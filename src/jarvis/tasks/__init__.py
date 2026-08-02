"""Task subsystem (L3): state machine, durable store, locks, scheduler, recovery."""

from __future__ import annotations

from jarvis.tasks.locks import (
    FOREGROUND_DESKTOP,
    KNOWN_LOCK_PREFIXES,
    LockSetLease,
    ResourceLockManager,
)
from jarvis.tasks.models import Task, TaskCheckpoint, TaskEvidence, TaskTransition
from jarvis.tasks.recovery import (
    RecoveryReport,
    close_instance,
    recover_interrupted_work,
    register_instance,
)
from jarvis.tasks.runner import StopReason, TaskOutcome, TaskRunContext, TaskRunner
from jarvis.tasks.scheduler import SchedulerError, TaskScheduler
from jarvis.tasks.states import (
    ACTIVE_STATES,
    ALLOWED_TRANSITIONS,
    RESUMABLE_STATES,
    TERMINAL_STATES,
    InvalidTransitionError,
    TaskState,
    assert_transition,
    can_transition,
)
from jarvis.tasks.store import TaskNotFoundError, TaskStore

__all__ = [
    "ACTIVE_STATES",
    "ALLOWED_TRANSITIONS",
    "FOREGROUND_DESKTOP",
    "InvalidTransitionError",
    "KNOWN_LOCK_PREFIXES",
    "LockSetLease",
    "RESUMABLE_STATES",
    "RecoveryReport",
    "ResourceLockManager",
    "SchedulerError",
    "StopReason",
    "TERMINAL_STATES",
    "Task",
    "TaskCheckpoint",
    "TaskEvidence",
    "TaskNotFoundError",
    "TaskOutcome",
    "TaskRunContext",
    "TaskRunner",
    "TaskScheduler",
    "TaskState",
    "TaskStore",
    "TaskTransition",
    "assert_transition",
    "can_transition",
    "close_instance",
    "recover_interrupted_work",
    "register_instance",
]
