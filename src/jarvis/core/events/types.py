"""Typed domain events (ADR-0005).

Every event is a frozen pydantic model deriving from :class:`Event`. Subscribers
match by type, and subclass matching means subscribing to ``Event`` sees
everything.

Events are notifications, not commands. Nothing durable depends on an event
being delivered; anything that must survive a crash goes through the task store.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from jarvis.common import new_id, utc_now

__all__ = [
    "Event",
    "AppStarted",
    "AppStopping",
    "ConfigChanged",
    "NetworkModeChanged",
    "PermissionEvaluated",
    "PermissionGranted",
    "PermissionRevoked",
    "ToolRegistered",
    "ToolInvocationStarted",
    "ToolInvocationFinished",
    "ProhibitedCapabilityBlocked",
    "ApprovalRequested",
    "ApprovalResolved",
    "TaskCreated",
    "TaskStateChanged",
    "TaskCheckpointSaved",
    "LockAcquired",
    "LockReleased",
    "LockContended",
    "StaleLockReclaimed",
    "TaskRecovered",
    "EmergencyStopRequested",
    "EmergencyStopCompleted",
    "HealthChecked",
    "WorkerStateChanged",
    "AuditRecorded",
    "UntrustedContentObserved",
]


class Event(BaseModel):
    """Base class for everything on the bus."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    event_id: str = Field(default_factory=new_id)
    occurred_at: datetime = Field(default_factory=utc_now)
    source: str = "core"


# -- lifecycle -------------------------------------------------------------
class AppStarted(Event):
    instance_id: str
    app_version: str
    schema_version: int
    vault_root: str
    network_mode: str


class AppStopping(Event):
    instance_id: str
    reason: str


class ConfigChanged(Event):
    key_path: str
    previous: Any = None
    current: Any = None


class NetworkModeChanged(Event):
    previous: str
    current: str


# -- permissions -----------------------------------------------------------
class PermissionEvaluated(Event):
    capability_id: str
    risk: str
    decision: str
    requires_user_approval: bool
    reason: str
    task_id: str | None = None
    matched_grant_id: str | None = None


class PermissionGranted(Event):
    grant_id: str
    capability_id: str
    scope: str
    scope_ref: str | None = None
    expires_at: datetime | None = None


class PermissionRevoked(Event):
    grant_id: str
    capability_id: str
    reason: str


# -- tools -----------------------------------------------------------------
class ToolRegistered(Event):
    tool_id: str
    version: str
    risk: str
    changes_state: bool


class ToolInvocationStarted(Event):
    invocation_id: str
    tool_id: str
    task_id: str | None = None


class ToolInvocationFinished(Event):
    invocation_id: str
    tool_id: str
    outcome: str
    verification: str
    failure_code: str | None = None
    attempts: int = 1
    task_id: str | None = None


class ProhibitedCapabilityBlocked(Event):
    """A prohibited tool or capability was requested. Always a security signal."""

    identifier: str
    origin: str
    detail: str


# -- approvals (ADR-0027) --------------------------------------------------
class ApprovalRequested(Event):
    """A tool is waiting on the user. The tray must make this impossible to miss.

    Carries no parameter values: the request itself is held by the approval
    queue, and only redacted fields are ever displayed from there.
    """

    approval_id: str
    capability_id: str
    risk: str
    tool_id: str
    action_summary: str
    expires_at: datetime
    task_id: str | None = None


class ApprovalResolved(Event):
    approval_id: str
    capability_id: str
    decision: str
    scope: str
    timed_out: bool = False
    remembered_denial_scope: str | None = None
    task_id: str | None = None


# -- tasks -----------------------------------------------------------------
class TaskCreated(Event):
    task_id: str
    name: str
    runner_id: str
    parent_task_id: str | None = None


class TaskStateChanged(Event):
    task_id: str
    from_state: str | None
    to_state: str
    reason: str | None = None


class TaskCheckpointSaved(Event):
    task_id: str
    checkpoint_id: str
    sequence: int
    label: str


class TaskRecovered(Event):
    task_id: str
    previous_state: str
    new_state: str
    detail: str


# -- locks -----------------------------------------------------------------
class LockAcquired(Event):
    task_id: str
    lock_names: tuple[str, ...]


class LockReleased(Event):
    task_id: str
    lock_names: tuple[str, ...]


class LockContended(Event):
    task_id: str
    lock_name: str
    held_by_task_id: str


class StaleLockReclaimed(Event):
    lock_name: str
    previous_task_id: str
    previous_instance_id: str


# -- control ---------------------------------------------------------------
class EmergencyStopRequested(Event):
    origin: Literal["tray", "hotkey", "window", "voice", "api"]


class EmergencyStopCompleted(Event):
    cancelled_task_ids: tuple[str, ...]
    released_locks: tuple[str, ...]
    stopped_workers: tuple[str, ...]


class WorkerStateChanged(Event):
    worker_name: str
    state: Literal["starting", "running", "stopping", "stopped", "failed"]
    detail: str | None = None


class HealthChecked(Event):
    component: str
    healthy: bool
    detail: str
    skipped_reason: str | None = None


class AuditRecorded(Event):
    audit_id: str
    category: str
    summary: str


class UntrustedContentObserved(Event):
    """Content from outside the trust boundary entered the system (PRD 11.4).

    Emitted so the audit log and GUI can show that a plan was influenced by
    untrusted data. The content itself never travels on the bus.
    """

    origin: str
    content_class: str
    byte_length: int
    task_id: str | None = None
