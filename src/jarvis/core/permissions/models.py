"""Permission vocabulary (PRD sections 9.9 and 11.1)."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from jarvis.common import new_id, utc_now

__all__ = [
    "Decision",
    "GrantScope",
    "RiskLevel",
    "Capability",
    "PermissionGrant",
    "PermissionRequest",
    "PermissionEvaluation",
    "PermissionError",
    "ProhibitedCapabilityError",
]


class RiskLevel(str, Enum):
    """PRD section 11.1 capability classes."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    PROHIBITED = "prohibited"


class Decision(str, Enum):
    ALLOW = "allow"
    ASK = "ask"
    DENY = "deny"


class GrantScope(str, Enum):
    """PRD section 9.9 permission options."""

    ONCE = "once"
    SESSION = "session"
    TASK = "task"
    APPLICATION = "application"
    FOLDER = "folder"
    ALWAYS = "always"


class PermissionError(Exception):
    """A grant was refused because it would violate the permission model."""


class ProhibitedCapabilityError(PermissionError):
    """A capability in the prohibited class was requested. Never recoverable."""


class Capability(BaseModel):
    """One thing the agent might be permitted to do."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    capability_id: str
    title: str
    risk: RiskLevel
    description: str
    reversible: bool = True
    scope_kind: str | None = Field(
        default=None,
        description="What scope_ref means for this capability: 'application', 'folder', 'url_host'.",
    )
    phase: int = Field(description="PRD section 21 phase that first implements this.")


class PermissionGrant(BaseModel):
    """A recorded permission decision that may apply to future requests."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    grant_id: str = Field(default_factory=new_id)
    capability_id: str
    decision: Decision
    scope: GrantScope
    scope_ref: str | None = None
    session_id: str | None = None
    task_id: str | None = None
    created_at: datetime = Field(default_factory=utc_now)
    created_by: str = "user"
    expires_at: datetime | None = None
    revoked_at: datetime | None = None
    reason: str | None = None

    def is_active(self, now: datetime | None = None) -> bool:
        moment = now or utc_now()
        if self.revoked_at is not None:
            return False
        if self.expires_at is not None and self.expires_at <= moment:
            return False
        return True


class PermissionRequest(BaseModel):
    """A question put to the permission engine. Contains no side effects."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    capability_id: str
    task_id: str | None = None
    session_id: str | None = None
    target: str | None = Field(
        default=None,
        description="Application id, folder path or URL host the request applies to.",
    )
    initiating_utterance: str | None = Field(
        default=None, description="What the user asked for, shown in the approval dialog."
    )
    parameters: dict[str, Any] | None = None


class PermissionEvaluation(BaseModel):
    """The engine's answer. Never executes anything."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    capability_id: str
    risk: RiskLevel
    decision: Decision
    requires_user_approval: bool
    reason: str
    matched_grant_id: str | None = None
    evaluated_at: datetime = Field(default_factory=utc_now)

    @property
    def allowed(self) -> bool:
        return self.decision is Decision.ALLOW
