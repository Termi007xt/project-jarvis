"""The approval queue — step 5 of the invoker pipeline, made answerable.

ADR-0027 chose a **tray-anchored, non-modal** approval surface. A modal dialog
would steal keyboard focus, and in Phase 2, when Jarvis is driving another
application, stealing focus mid-action can break the very automation the user is
being asked to approve.

Non-modal has a consequence: the requesting thread and the answering thread are
different, and the request has to survive in between. That is what this queue is.
It lives in L2 with no Qt anywhere near it, so the whole approval flow — including
the timeout path, which is the security-critical one — is testable headlessly.

Three rules the implementation exists to enforce:

* **Silence is never consent** (ADR-0010). An unanswered request expires and is
  recorded as denied-by-timeout. There is no code path from "nobody answered" to
  ``ALLOW``.
* **The dialog cannot widen a grant.** ``answer`` refuses any scope the request
  did not offer, so a UI defect cannot turn a high-risk single-use approval into
  a standing one.
* **A refusal can be made to stick.** Denying with a ``RememberDenialOption``
  writes a scoped ``DENY`` grant, which already outranks allow-grants and
  short-circuits the high-risk ASK path.
"""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Callable

from jarvis.common import utc_now
from jarvis.core.audit.log import AuditLog
from jarvis.core.audit.models import AuditCategory
from jarvis.core.events.bus import EventBus
from jarvis.core.events.types import ApprovalRequested, ApprovalResolved
from jarvis.core.permissions.models import Decision, GrantScope
from jarvis.core.tools.ports import ApprovalOutcome, ApprovalRequest, RememberDenialOption

__all__ = ["ApprovalQueue", "PendingApproval", "DEFAULT_APPROVAL_TIMEOUT_SECONDS"]

_LOG = logging.getLogger(__name__)

#: How long a request waits before it is denied by timeout. Long enough that a
#: user who stepped away can still answer; short enough that a task does not sit
#: blocked indefinitely holding resource locks.
DEFAULT_APPROVAL_TIMEOUT_SECONDS = 120.0


@dataclass
class PendingApproval:
    """One unanswered request. Mutable, unlike everything on the event bus."""

    request: ApprovalRequest
    requested_at: datetime
    expires_at: datetime
    _answered: threading.Event = field(default_factory=threading.Event)
    outcome: ApprovalOutcome | None = None

    @property
    def approval_id(self) -> str:
        return self.request.approval_id

    def seconds_remaining(self, now: datetime | None = None) -> float:
        return max(0.0, (self.expires_at - (now or utc_now())).total_seconds())


class ApprovalQueue:
    """Holds requests between the thread that needs an answer and the user.

    Implements :class:`~jarvis.core.tools.ports.ApprovalPort`, so it drops
    straight into ``ToolInvoker``.
    """

    def __init__(
        self,
        *,
        audit: AuditLog | None = None,
        event_bus: EventBus | None = None,
        timeout_seconds: float = DEFAULT_APPROVAL_TIMEOUT_SECONDS,
        clock: Callable[[], datetime] = utc_now,
    ) -> None:
        if timeout_seconds <= 0:
            # PRD NFR-013: every wait is bounded. A zero or negative timeout
            # would mean either an instant denial or an unbounded wait, and
            # neither is a defensible default.
            raise ValueError("approval timeout must be positive")
        self._audit = audit
        self._events = event_bus
        self._timeout_seconds = timeout_seconds
        self._clock = clock
        self._lock = threading.RLock()
        self._pending: dict[str, PendingApproval] = {}
        self._listeners: list[Callable[[], None]] = []
        self._interactive = False

    # -- attachment --------------------------------------------------------
    def set_interactive(self, interactive: bool) -> None:
        """Declare whether a user interface is actually connected.

        Until one is, queueing a request would mean waiting the full timeout for
        an answer nobody can give. Denying immediately is both faster and more
        honest, and it keeps ``--check`` and the headless engine behaving exactly
        as they did in Phase 0 (ADR-0010).
        """
        with self._lock:
            self._interactive = interactive
        if not interactive:
            self.deny_all("the approval interface was disconnected")

    @property
    def interactive(self) -> bool:
        with self._lock:
            return self._interactive

    # -- the port ----------------------------------------------------------
    def request_approval(self, request: ApprovalRequest) -> ApprovalOutcome:
        """Block the calling thread until answered, or until the request expires.

        Called on a scheduler or invoker worker thread, never on the UI thread —
        blocking the UI thread here would deadlock the very interface that has to
        answer.
        """
        if not self.interactive:
            outcome = ApprovalOutcome(
                decision=Decision.DENY,
                reason=(
                    "no approval interface is connected, so this action cannot be "
                    "authorised. Open the Jarvis window and try again."
                ),
            )
            self._record(
                f"approval unavailable for {request.capability_id}",
                request,
                result="denied",
                error=outcome.reason,
            )
            self._publish_resolution(request, outcome)
            return outcome

        now = self._clock()
        pending = PendingApproval(
            request=request,
            requested_at=now,
            expires_at=now + timedelta(seconds=self._timeout_seconds),
        )

        # Announce before making it answerable. The other order lets a fast
        # answer publish its resolution first, so an observer would see a
        # decision for a request it had never been told about.
        self._record(
            f"approval requested for {request.capability_id}",
            request,
            result="pending",
        )
        if self._events is not None:
            self._events.publish(
                ApprovalRequested(
                    source="approvals",
                    approval_id=request.approval_id,
                    capability_id=request.capability_id,
                    risk=request.risk.value,
                    tool_id=request.tool_id,
                    action_summary=request.action_summary,
                    expires_at=pending.expires_at,
                    task_id=request.task_id,
                )
            )

        with self._lock:
            self._pending[request.approval_id] = pending
        self._notify()

        answered = pending._answered.wait(timeout=self._timeout_seconds)  # noqa: SLF001

        with self._lock:
            self._pending.pop(request.approval_id, None)
            outcome = pending.outcome

        if not answered or outcome is None:
            outcome = ApprovalOutcome(
                decision=Decision.DENY,
                reason=(
                    f"no answer within {self._timeout_seconds:.0f}s, so the request "
                    "expired. An unanswered approval is a denial, never an allowance."
                ),
                timed_out=True,
            )
            self._publish_resolution(request, outcome)
            self._record(
                f"approval timed out for {request.capability_id}",
                request,
                result="denied_by_timeout",
                error=outcome.reason,
            )
        self._notify()
        return outcome

    # -- the user's side ---------------------------------------------------
    def answer(
        self,
        approval_id: str,
        decision: Decision,
        *,
        scope: GrantScope = GrantScope.ONCE,
        remember_denial: RememberDenialOption | None = None,
        stop_task: bool = False,
        reason: str = "",
    ) -> bool:
        """Record the user's decision. Returns False if nothing was waiting.

        Raises :class:`ValueError` for a scope the request did not offer, so a
        defect in the dialog cannot widen a grant past what the permission model
        allows.
        """
        with self._lock:
            pending = self._pending.get(approval_id)
            if pending is None or pending.outcome is not None:
                return False
            request = pending.request

            if decision is Decision.ALLOW and scope not in request.offerable_scopes:
                raise ValueError(
                    f"scope '{scope.value}' was not offered for "
                    f"{request.capability_id} ({request.risk.value} risk); "
                    f"offered: {[s.value for s in request.offerable_scopes]}"
                )
            if remember_denial is not None:
                if decision is not Decision.DENY:
                    raise ValueError("a remembered denial only accompanies a denial")
                if remember_denial not in request.denial_options:
                    raise ValueError(
                        f"'{remember_denial.label}' was not offered for "
                        f"{request.capability_id}"
                    )

            outcome = ApprovalOutcome(
                decision=decision,
                scope=scope if decision is Decision.ALLOW else GrantScope.ONCE,
                stop_task=stop_task,
                reason=reason or ("approved by the user" if decision is Decision.ALLOW
                                  else "denied by the user"),
                remember_denial=remember_denial,
            )
            pending.outcome = outcome
            pending._answered.set()  # noqa: SLF001

        self._publish_resolution(request, outcome)
        self._record(
            f"approval {decision.value} for {request.capability_id}",
            request,
            actor="user",
            result=decision.value,
        )
        return True

    def deny_all(self, reason: str = "emergency stop") -> int:
        """Deny everything outstanding. Used by emergency stop and by shutdown."""
        with self._lock:
            waiting = [p for p in self._pending.values() if p.outcome is None]
            for pending in waiting:
                pending.outcome = ApprovalOutcome(decision=Decision.DENY, reason=reason)
                pending._answered.set()  # noqa: SLF001
        for pending in waiting:
            self._publish_resolution(pending.request, pending.outcome)  # type: ignore[arg-type]
            self._record(
                f"approval cancelled for {pending.request.capability_id}",
                pending.request,
                actor="user",
                result="denied",
                error=reason,
            )
        return len(waiting)

    # -- observation -------------------------------------------------------
    def pending(self) -> tuple[PendingApproval, ...]:
        with self._lock:
            return tuple(
                sorted(
                    (p for p in self._pending.values() if p.outcome is None),
                    key=lambda p: p.requested_at,
                )
            )

    @property
    def has_pending(self) -> bool:
        return bool(self.pending())

    def oldest_pending(self) -> PendingApproval | None:
        waiting = self.pending()
        return waiting[0] if waiting else None

    def subscribe(self, listener: Callable[[], None]) -> None:
        """Called whenever the pending set changes. Used by the tray."""
        with self._lock:
            self._listeners.append(listener)

    # -- internals ---------------------------------------------------------
    def _notify(self) -> None:
        with self._lock:
            listeners = list(self._listeners)
        for listener in listeners:
            try:
                listener()
            except Exception:  # noqa: BLE001 - a bad listener must not block approval
                _LOG.exception("an approval listener raised")

    def _publish_resolution(self, request: ApprovalRequest, outcome: ApprovalOutcome) -> None:
        if self._events is None:
            return
        self._events.publish(
            ApprovalResolved(
                source="approvals",
                approval_id=request.approval_id,
                capability_id=request.capability_id,
                decision=outcome.decision.value,
                scope=outcome.scope.value,
                timed_out=outcome.timed_out,
                remembered_denial_scope=(
                    outcome.remember_denial.scope.value if outcome.remember_denial else None
                ),
                task_id=request.task_id,
            )
        )

    def _record(
        self,
        summary: str,
        request: ApprovalRequest,
        *,
        actor: str = "system",
        result: str | None = None,
        error: str | None = None,
    ) -> None:
        if self._audit is None:
            return
        self._audit.record(
            AuditCategory.PERMISSION,
            summary,
            actor=actor,
            task_id=request.task_id,
            tool_id=request.tool_id,
            capability_id=request.capability_id,
            risk=request.risk.value,
            parameters={"approval_id": request.approval_id, "target": request.target},
            result=result,
            error=error,
        )
