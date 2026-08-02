"""Task state machine (PRD FR-122).

Every transition is validated against an explicit table. An illegal transition
raises rather than silently correcting itself, because a task quietly moving to
a state nobody designed is exactly how a "completed" task ends up never having
run.
"""

from __future__ import annotations

from enum import Enum

__all__ = [
    "TaskState",
    "TERMINAL_STATES",
    "ACTIVE_STATES",
    "RESUMABLE_STATES",
    "ALLOWED_TRANSITIONS",
    "InvalidTransitionError",
    "can_transition",
    "assert_transition",
]


class TaskState(str, Enum):
    DRAFT = "draft"
    AWAITING_APPROVAL = "awaiting_approval"
    QUEUED = "queued"
    RUNNING = "running"
    WAITING = "waiting"
    PAUSED = "paused"
    BLOCKED = "blocked"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


TERMINAL_STATES: frozenset[TaskState] = frozenset(
    {TaskState.SUCCEEDED, TaskState.FAILED, TaskState.CANCELLED}
)

#: States a task occupies while it still owns resources or attention.
ACTIVE_STATES: frozenset[TaskState] = frozenset(
    {TaskState.QUEUED, TaskState.RUNNING, TaskState.WAITING}
)

#: States from which a user may resume work.
RESUMABLE_STATES: frozenset[TaskState] = frozenset({TaskState.PAUSED, TaskState.BLOCKED})


ALLOWED_TRANSITIONS: dict[TaskState, frozenset[TaskState]] = {
    TaskState.DRAFT: frozenset(
        {TaskState.AWAITING_APPROVAL, TaskState.QUEUED, TaskState.CANCELLED, TaskState.FAILED}
    ),
    TaskState.AWAITING_APPROVAL: frozenset(
        {TaskState.QUEUED, TaskState.BLOCKED, TaskState.CANCELLED, TaskState.FAILED}
    ),
    TaskState.QUEUED: frozenset(
        {TaskState.RUNNING, TaskState.PAUSED, TaskState.BLOCKED, TaskState.CANCELLED}
    ),
    TaskState.RUNNING: frozenset(
        {
            TaskState.WAITING,
            TaskState.PAUSED,
            TaskState.BLOCKED,
            TaskState.QUEUED,  # released the foreground lock, back in the queue
            TaskState.SUCCEEDED,
            TaskState.FAILED,
            TaskState.CANCELLED,
        }
    ),
    TaskState.WAITING: frozenset(
        {
            TaskState.RUNNING,
            TaskState.PAUSED,
            TaskState.BLOCKED,
            TaskState.FAILED,
            TaskState.CANCELLED,
        }
    ),
    TaskState.PAUSED: frozenset({TaskState.QUEUED, TaskState.RUNNING, TaskState.CANCELLED}),
    TaskState.BLOCKED: frozenset(
        {
            TaskState.QUEUED,
            TaskState.AWAITING_APPROVAL,
            TaskState.PAUSED,
            TaskState.FAILED,
            TaskState.CANCELLED,
        }
    ),
    # Terminal states have no outgoing edges. A finished task is finished; a
    # repeat is a new task, so recovery can never silently re-run one.
    TaskState.SUCCEEDED: frozenset(),
    TaskState.FAILED: frozenset(),
    TaskState.CANCELLED: frozenset(),
}


class InvalidTransitionError(Exception):
    """An attempt was made to move a task between incompatible states."""


def can_transition(current: TaskState, target: TaskState) -> bool:
    return target in ALLOWED_TRANSITIONS[current]


def assert_transition(current: TaskState, target: TaskState) -> None:
    if not can_transition(current, target):
        allowed = sorted(state.value for state in ALLOWED_TRANSITIONS[current])
        raise InvalidTransitionError(
            f"cannot move a task from '{current.value}' to '{target.value}'. "
            f"Allowed from '{current.value}': {allowed or ['(terminal)']}"
        )
