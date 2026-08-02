"""Audit record schema (PRD section 11.5)."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from jarvis.common import new_id, utc_now

__all__ = ["AuditCategory", "AuditEvent"]


class AuditCategory(str, Enum):
    """Why the record exists. Used for filtering in the GUI."""

    LIFECYCLE = "lifecycle"
    CONFIG = "config"
    PERMISSION = "permission"
    TOOL = "tool"
    TASK = "task"
    LOCK = "lock"
    SECURITY = "security"
    HEALTH = "health"
    RECOVERY = "recovery"
    DATA = "data"


class AuditEvent(BaseModel):
    """One append-only audit record.

    Field set follows PRD section 11.5: timestamp, task ID, conversation ID,
    tool, parameters with secret redaction, permission decision, pre-action
    state, result, verification, error, and an optional evidence reference.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    audit_id: str = Field(default_factory=new_id)
    occurred_at: datetime = Field(default_factory=utc_now)
    instance_id: str | None = None
    category: AuditCategory
    actor: str = Field(
        default="system",
        description="Who caused this: 'user', 'system', 'planner', 'schedule', 'recovery'.",
    )
    summary: str = Field(description="One human-readable line. Never contains secrets.")

    task_id: str | None = None
    conversation_id: str | None = None
    tool_id: str | None = None
    capability_id: str | None = None
    risk: str | None = None
    permission_decision: str | None = None

    parameters: dict[str, Any] | None = Field(
        default=None, description="Already redacted by jarvis.core.audit.redaction."
    )
    pre_state: dict[str, Any] | None = None
    result: str | None = None
    verification: str | None = None
    error: str | None = None
    evidence_ref: str | None = None
