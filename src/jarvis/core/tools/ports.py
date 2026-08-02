"""Ports the tool invoker depends on, so ``jarvis.core`` stays free of Qt and
of the task layer (ARCHITECTURE.md section 5).

Adapters implementing these live elsewhere: ``jarvis.tasks.locks`` provides the
lock port, and ``jarvis.ui`` will provide the approval port in Phase 1.
"""

from __future__ import annotations

from typing import Any, Protocol, Sequence, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field

from jarvis.core.permissions.models import Decision, GrantScope, RiskLevel

__all__ = [
    "LockPort",
    "LockLease",
    "ApprovalRequest",
    "ApprovalOutcome",
    "ApprovalPort",
    "DenyingApprovalPort",
    "AutoApprovalPort",
]


@runtime_checkable
class LockLease(Protocol):
    """A held set of resource locks."""

    owner_id: str
    lock_names: tuple[str, ...]

    def release(self) -> None:
        ...


@runtime_checkable
class LockPort(Protocol):
    """All-or-nothing acquisition of a declared lock set (PRD FR-124)."""

    def acquire(
        self, owner_id: str, lock_names: Sequence[str], timeout_seconds: float = 0.0
    ) -> LockLease | None:
        """Return a lease, or ``None`` if the whole set could not be taken."""


class ApprovalRequest(BaseModel):
    """What the user is shown before a consequential action (PRD section 11.2)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    capability_id: str
    risk: RiskLevel
    tool_id: str
    action_summary: str = Field(description="The requested action, in plain language.")
    initiating_utterance: str | None = Field(
        default=None, description="What the user actually asked for."
    )
    target: str | None = Field(default=None, description="Application, file or destination.")
    parameters: dict[str, Any] = Field(
        default_factory=dict, description="Already redacted; safe to display."
    )
    data_involved: str | None = None
    scope_description: str = Field(description="Exactly how far the permission would extend.")
    reversible: bool = True
    rollback_method: str | None = None
    task_id: str | None = None
    offerable_scopes: tuple[GrantScope, ...] = Field(
        default=(GrantScope.ONCE,),
        description="Scopes the dialog may offer. High risk offers ONCE only.",
    )


class ApprovalOutcome(BaseModel):
    """The user's answer."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    decision: Decision
    scope: GrantScope = GrantScope.ONCE
    stop_task: bool = False
    reason: str = ""

    @property
    def allowed(self) -> bool:
        return self.decision is Decision.ALLOW


@runtime_checkable
class ApprovalPort(Protocol):
    """Asks the user. The core asks; the shell answers."""

    def request_approval(self, request: ApprovalRequest) -> ApprovalOutcome:
        ...


class DenyingApprovalPort:
    """The Phase 0 default: no approval interface, therefore no approval.

    Silence is never consent (ADR-0010). Until a real dialog exists, anything
    requiring approval simply cannot run, and says why.
    """

    def request_approval(self, request: ApprovalRequest) -> ApprovalOutcome:
        return ApprovalOutcome(
            decision=Decision.DENY,
            reason=(
                "no approval interface is connected, so this action cannot be "
                "authorised. The approval dialog arrives in Phase 1."
            ),
        )


class AutoApprovalPort:
    """Test double. Never wire this into a running application.

    Guarded so a mistake is loud: it refuses to approve anything high risk.
    """

    def __init__(self, decision: Decision = Decision.ALLOW, scope: GrantScope = GrantScope.ONCE) -> None:
        self._decision = decision
        self._scope = scope
        self.requests: list[ApprovalRequest] = []

    def request_approval(self, request: ApprovalRequest) -> ApprovalOutcome:
        self.requests.append(request)
        if request.risk is RiskLevel.HIGH and self._decision is Decision.ALLOW:
            return ApprovalOutcome(
                decision=Decision.DENY,
                reason="AutoApprovalPort refuses to auto-approve high-risk actions",
            )
        return ApprovalOutcome(decision=self._decision, scope=self._scope, reason="automated")
