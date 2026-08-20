"""Ports the tool invoker depends on, so ``jarvis.core`` stays free of Qt and
of the task layer (ARCHITECTURE.md section 5).

Adapters implementing these live elsewhere: ``jarvis.tasks.locks`` provides the
lock port, and ``jarvis.ui`` will provide the approval port in Phase 1.
"""

from __future__ import annotations

from typing import Any, Protocol, Sequence, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field

from jarvis.common import new_id
from jarvis.core.permissions.models import Capability, Decision, GrantScope, RiskLevel

__all__ = [
    "LockPort",
    "LockLease",
    "RememberDenialOption",
    "ApprovalRequest",
    "ApprovalOutcome",
    "ApprovalPort",
    "DenyingApprovalPort",
    "AutoApprovalPort",
    "offerable_scopes_for",
    "denial_options_for",
]

#: How a capability's ``scope_kind`` maps to a rememberable denial (ADR-0027).
#: ``url_host`` reuses ``APPLICATION``, which matches on an exact ``scope_ref``,
#: and is labelled "this site" so the button never overstates what it covers.
_DENIAL_SCOPES: dict[str, tuple[GrantScope, str]] = {
    "application": (GrantScope.APPLICATION, "this application"),
    "folder": (GrantScope.FOLDER, "this folder"),
    "url_host": (GrantScope.APPLICATION, "this site"),
}


def offerable_scopes_for(
    risk: RiskLevel,
    *,
    allow_always_for_low_risk: bool = True,
    always_allowable: bool = False,
) -> tuple[GrantScope, ...]:
    """The allow-scopes the dialog may offer, per the ADR-0027 table.

    Low offers "always", medium offers "for this task", high offers single use
    and nothing else. ``SESSION`` is deliberately absent: the engine still
    supports it programmatically, but its lifetime is invisible to a user, and
    "this task" already covers approving a multi-step operation once.

    ``always_allowable`` adds "always" for one named medium-risk capability
    (ADR-0032). It is passed per capability rather than per risk band, because
    the exception is the owner naming a capability they use constantly, not a
    reclassification of everything that shares its risk level.

    **Whatever this returns, the engine must be able to grant.** The dialog once
    offered "Allow for this task" for a request that carried no task id; the
    engine rejected the scope, the owner's choice was discarded, and they were
    asked again on the very next sentence — four times in seven minutes on
    2026-08-05. `test_approval_scopes_that_stick.py` now walks this table and
    grants each entry, so the two cannot drift apart again.
    """
    if risk is RiskLevel.HIGH:
        # PRD 9.9 and 11.1: fresh confirmation every time. Not a UX choice, and
        # `always_allowable` does not reach here.
        return (GrantScope.ONCE,)
    if risk is RiskLevel.MEDIUM:
        if always_allowable:
            return (GrantScope.ONCE, GrantScope.TASK, GrantScope.ALWAYS)
        return (GrantScope.ONCE, GrantScope.TASK)
    if risk is RiskLevel.LOW:
        return (GrantScope.ONCE, GrantScope.ALWAYS) if allow_always_for_low_risk else (GrantScope.ONCE,)
    return ()  # PROHIBITED never reaches a dialog at all.


def denial_options_for(
    capability: Capability | None, target: str | None
) -> tuple["RememberDenialOption", ...]:
    """"Don't ask again" options, when the capability has a meaningful target.

    A remembered denial is a ``DENY`` grant. Deny-grants already outrank
    allow-grants and short-circuit the high-risk ASK path, so no engine change
    is needed to make a refusal stick (ADR-0027).
    """
    if capability is None or not target or capability.scope_kind is None:
        return ()
    mapped = _DENIAL_SCOPES.get(capability.scope_kind)
    if mapped is None:
        return ()
    scope, noun = mapped
    return (
        RememberDenialOption(
            scope=scope, scope_ref=target, label=f"Don't ask again for {noun}"
        ),
    )


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


class RememberDenialOption(BaseModel):
    """A "don't ask again" choice offered alongside Deny (ADR-0027)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    scope: GrantScope
    scope_ref: str
    label: str


class ApprovalRequest(BaseModel):
    """What the user is shown before a consequential action (PRD section 11.2)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    approval_id: str = Field(default_factory=new_id)
    capability_id: str
    capability_title: str = ""
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
    denial_options: tuple[RememberDenialOption, ...] = Field(
        default=(),
        description="Rememberable denials, when the capability has a real target.",
    )


class ApprovalOutcome(BaseModel):
    """The user's answer."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    decision: Decision
    scope: GrantScope = GrantScope.ONCE
    stop_task: bool = False
    reason: str = ""
    remember_denial: RememberDenialOption | None = Field(
        default=None,
        description="Set only alongside DENY, to persist a scoped deny-grant.",
    )
    timed_out: bool = Field(
        default=False,
        description="The request expired unanswered. Recorded as denied, never allowed.",
    )

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
