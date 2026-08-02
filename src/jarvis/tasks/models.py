"""Task records (PRD FR-120 .. FR-133)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from jarvis.common import new_id, utc_now
from jarvis.tasks.states import TaskState

__all__ = ["Task", "TaskCheckpoint", "TaskEvidence", "TaskTransition", "ResourceLockRecord"]


class Task(BaseModel):
    """One unit of work with a durable state machine."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    task_id: str = Field(default_factory=new_id)
    parent_task_id: str | None = None
    conversation_id: str | None = None
    name: str
    goal: str
    runner_id: str = Field(description="Which registered runner executes this task.")
    state: TaskState = TaskState.DRAFT
    priority: int = Field(default=100, ge=0, le=1000, description="Lower runs first.")
    required_locks: tuple[str, ...] = ()
    payload: dict[str, Any] = Field(default_factory=dict)

    attempts: int = 0
    max_retries: int = Field(default=3, ge=0, le=50)

    waiting_on: str | None = Field(
        default=None, description="Why the task is not running, shown in the Tasks screen."
    )
    blocked_reason: str | None = None
    failure_code: str | None = None
    result_summary: str | None = None

    #: True when a restart moved this task out of an interrupted state.
    recovered: bool = False
    instance_id: str | None = None

    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    started_at: datetime | None = None
    ended_at: datetime | None = None

    @property
    def is_terminal(self) -> bool:
        from jarvis.tasks.states import TERMINAL_STATES

        return self.state in TERMINAL_STATES

    @property
    def retries_remaining(self) -> int:
        return max(0, self.max_retries - max(0, self.attempts - 1))


class TaskTransition(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    transition_id: str = Field(default_factory=new_id)
    task_id: str
    from_state: TaskState | None
    to_state: TaskState
    reason: str | None = None
    occurred_at: datetime = Field(default_factory=utc_now)


class TaskCheckpoint(BaseModel):
    """Durable resume point (PRD FR-128)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    checkpoint_id: str = Field(default_factory=new_id)
    task_id: str
    sequence: int
    label: str
    state: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)


class TaskEvidence(BaseModel):
    """Support for a completion claim (PRD FR-132)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    evidence_id: str = Field(default_factory=new_id)
    task_id: str
    kind: str = Field(
        description="window_title | process_state | file_exists | ui_text | screenshot "
        "| test_result | browser_state | user_confirmation"
    )
    summary: str
    detail: dict[str, Any] | None = None
    artefact_path: str | None = None
    created_at: datetime = Field(default_factory=utc_now)


class ResourceLockRecord(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    lock_name: str
    task_id: str
    instance_id: str
    acquired_at: datetime = Field(default_factory=utc_now)
