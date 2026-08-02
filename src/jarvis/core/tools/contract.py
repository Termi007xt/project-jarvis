"""The tool contract (PRD section 13.2).

A *tool* is the only way the agent affects anything. Everything a tool needs to
declare is here, so the invoker, the approval dialog, the audit log and the
planner's schema all read from one source.
"""

from __future__ import annotations

import threading
from datetime import datetime
from enum import Enum
from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field, model_validator

from jarvis.common import new_id, utc_now
from jarvis.core.permissions.models import RiskLevel

__all__ = [
    "ToolOutcome",
    "Verification",
    "RetryPolicy",
    "RollbackSpec",
    "ToolSpec",
    "ToolContext",
    "ToolExecution",
    "ToolResult",
    "ToolFailure",
    "Tool",
]


class ToolOutcome(str, Enum):
    """How an invocation ended. There is deliberately no boolean 'worked'."""

    SUCCEEDED = "succeeded"
    FAILED = "failed"
    DENIED = "denied"          # permission engine or user said no
    BLOCKED = "blocked"        # could not start: locks, schema, unknown tool
    TIMED_OUT = "timed_out"
    CANCELLED = "cancelled"


class Verification(str, Enum):
    """Whether the tool confirmed its own effect (PRD FR-048, AT-018)."""

    VERIFIED = "verified"
    UNVERIFIED = "unverified"
    FAILED = "failed"
    NOT_APPLICABLE = "not_applicable"  # read-only tools change nothing to verify


class RetryPolicy(BaseModel):
    """Bounded retries only (PRD FR-133, NFR-012)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    max_attempts: int = Field(default=1, ge=1, le=10)
    backoff_seconds: float = Field(default=0.0, ge=0.0, le=60.0)
    retry_on: tuple[str, ...] = Field(
        default=(), description="Failure codes that may be retried. Empty means none."
    )

    @model_validator(mode="after")
    def _retryable_codes_required(self) -> "RetryPolicy":
        if self.max_attempts > 1 and not self.retry_on:
            raise ValueError(
                "a retry policy with max_attempts > 1 must name the failure codes "
                "it may retry; blanket retries hide real failures"
            )
        return self


class RollbackSpec(BaseModel):
    """Reversibility metadata (PRD FR-221)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    method: str
    expiry_seconds: int | None = None
    requires_approval: bool = True
    restore_fields: tuple[str, ...] = ()


class ToolSpec(BaseModel):
    """Everything a tool declares about itself."""

    model_config = ConfigDict(frozen=True, extra="forbid", arbitrary_types_allowed=True)

    tool_id: str = Field(pattern=r"^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+$")
    version: str
    description: str
    input_model: type[BaseModel]
    output_model: type[BaseModel]
    risk: RiskLevel
    required_capabilities: tuple[str, ...]
    resource_locks: tuple[str, ...] = ()
    timeout_seconds: float = Field(default=30.0, gt=0.0, le=3600.0)
    retry_policy: RetryPolicy = RetryPolicy()
    changes_state: bool
    verification: str = Field(description="How this tool confirms its own effect.")
    redaction_keys: tuple[str, ...] = ()
    supported_applications: tuple[str, ...] = ()
    failure_codes: tuple[str, ...]
    reversible: bool = True
    rollback: RollbackSpec | None = None
    target_parameter: str | None = Field(
        default=None,
        description="Input field supplying the permission target (app id, folder, host).",
    )

    @model_validator(mode="after")
    def _consistency(self) -> "ToolSpec":
        if self.risk is RiskLevel.PROHIBITED:
            raise ValueError(
                f"tool '{self.tool_id}' declares prohibited risk; prohibited "
                "capabilities have no implementation by design"
            )
        if not self.required_capabilities:
            raise ValueError(
                f"tool '{self.tool_id}' must declare at least one required capability"
            )
        if not self.failure_codes:
            raise ValueError(
                f"tool '{self.tool_id}' must declare its failure codes so the invoker "
                "can reject invented ones"
            )
        if self.changes_state and not self.reversible and self.rollback is not None:
            raise ValueError(
                f"tool '{self.tool_id}' is marked irreversible but declares a rollback"
            )
        unknown_retry = set(self.retry_policy.retry_on) - set(self.failure_codes)
        if unknown_retry:
            raise ValueError(
                f"tool '{self.tool_id}' retry policy names undeclared failure codes: "
                f"{sorted(unknown_retry)}"
            )
        return self

    def json_schema_for_model(self) -> dict[str, Any]:
        """Schema the planner sees. Free-form text can never reach the invoker."""
        return {
            "name": self.tool_id,
            "description": self.description,
            "parameters": self.input_model.model_json_schema(),
            "risk": self.risk.value,
            "changes_state": self.changes_state,
            "reversible": self.reversible,
        }


class ToolContext(BaseModel):
    """Per-invocation context handed to a tool. Carries no ambient authority."""

    model_config = ConfigDict(frozen=True, extra="forbid", arbitrary_types_allowed=True)

    invocation_id: str = Field(default_factory=new_id)
    task_id: str | None = None
    session_id: str | None = None
    conversation_id: str | None = None
    initiating_utterance: str | None = None
    cancel_event: threading.Event | None = None

    def cancelled(self) -> bool:
        return self.cancel_event is not None and self.cancel_event.is_set()


class ToolExecution(BaseModel):
    """What a tool returns on success."""

    model_config = ConfigDict(frozen=True, extra="forbid", arbitrary_types_allowed=True)

    output: BaseModel
    verification: Verification
    evidence: dict[str, Any] | None = None
    message: str | None = None


class ToolFailure(Exception):
    """Raised by a tool to report a declared failure. The code must be declared."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


class ToolResult(BaseModel):
    """The invoker's typed answer. Success requires verification."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    invocation_id: str
    tool_id: str
    tool_version: str
    outcome: ToolOutcome
    verification: Verification
    failure_code: str | None = None
    message: str = ""
    output: dict[str, Any] | None = None
    evidence: dict[str, Any] | None = None
    attempts: int = 1
    task_id: str | None = None
    started_at: datetime = Field(default_factory=utc_now)
    ended_at: datetime = Field(default_factory=utc_now)

    @property
    def duration_ms(self) -> int:
        return int((self.ended_at - self.started_at).total_seconds() * 1000)

    @property
    def succeeded(self) -> bool:
        """True only when the tool ran *and* confirmed its effect."""
        return self.outcome is ToolOutcome.SUCCEEDED and self.verification in (
            Verification.VERIFIED,
            Verification.NOT_APPLICABLE,
        )


@runtime_checkable
class Tool(Protocol):
    """What an implementation must provide."""

    spec: ToolSpec

    def run(self, context: ToolContext, parameters: BaseModel) -> ToolExecution:
        ...
