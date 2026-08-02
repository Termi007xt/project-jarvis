"""Permission evaluation (ARCHITECTURE.md section 6.4).

The engine answers one question — *may this capability run, in this scope, right
now?* — and never executes anything.

Evaluation order, short-circuiting at the first decisive step:

1. capability unknown            -> DENY
2. risk is PROHIBITED            -> DENY, unconditionally, ignoring all grants
3. risk is HIGH                  -> ASK, always (fresh confirmation every time)
4. a matching active grant       -> that grant's decision
5. otherwise                     -> the configured default policy for the risk level
"""

from __future__ import annotations

import os
import threading
from datetime import timedelta
from pathlib import Path

from jarvis.common import from_iso, to_iso, utc_now
from jarvis.core.audit.log import AuditLog
from jarvis.core.audit.models import AuditCategory
from jarvis.core.events.bus import EventBus
from jarvis.core.events.types import (
    PermissionEvaluated,
    PermissionGranted,
    PermissionRevoked,
    ProhibitedCapabilityBlocked,
)
from jarvis.core.permissions.catalogue import CAPABILITIES
from jarvis.core.permissions.models import (
    Capability,
    Decision,
    GrantScope,
    PermissionError,
    PermissionEvaluation,
    PermissionGrant,
    PermissionRequest,
    ProhibitedCapabilityError,
    RiskLevel,
)
from jarvis.storage.database import Database

__all__ = ["PermissionEngine", "DefaultPolicy"]


class DefaultPolicy:
    """Fallback decisions when no grant matches. High risk is fixed at ASK."""

    __slots__ = ("low", "medium", "allow_always_for_low_risk", "session_grant_ttl_seconds")

    def __init__(
        self,
        low: Decision = Decision.ASK,
        medium: Decision = Decision.ASK,
        *,
        allow_always_for_low_risk: bool = True,
        session_grant_ttl_seconds: int = 3600,
    ) -> None:
        if medium is Decision.ALLOW:
            # PRD 11.1: medium risk is "ask every time, per task, per app or per
            # folder". A blanket allow default would erase that.
            raise PermissionError("medium-risk capabilities cannot default to allow")
        self.low = low
        self.medium = medium
        self.allow_always_for_low_risk = allow_always_for_low_risk
        self.session_grant_ttl_seconds = session_grant_ttl_seconds


def _canonical_folder(value: str) -> str:
    """Normalise a folder scope reference for prefix comparison.

    Phase 0 handles relative paths, environment variables, case and separators.
    Full canonicalisation of junctions, symlinks and 8.3 short names is a
    filesystem-tool concern and lands with the filesystem scope in Phase 2
    (THREAT_MODEL.md, filesystem section).
    """
    expanded = os.path.expandvars(os.path.expanduser(value))
    resolved = Path(expanded).resolve()
    text = str(resolved)
    return text.casefold() if os.name == "nt" else text


def _folder_contains(root: str, candidate: str) -> bool:
    root_path = Path(_canonical_folder(root))
    candidate_path = Path(_canonical_folder(candidate))
    return candidate_path == root_path or root_path in candidate_path.parents


class PermissionEngine:
    """Evaluates capability requests against persisted grants."""

    def __init__(
        self,
        database: Database,
        audit: AuditLog,
        event_bus: EventBus | None = None,
        policy: DefaultPolicy | None = None,
        catalogue: dict[str, Capability] | None = None,
    ) -> None:
        self._database = database
        self._audit = audit
        self._events = event_bus
        self._policy = policy or DefaultPolicy()
        self._catalogue = catalogue if catalogue is not None else CAPABILITIES
        self._lock = threading.RLock()

    @property
    def policy(self) -> DefaultPolicy:
        return self._policy

    def capability(self, capability_id: str) -> Capability | None:
        """The catalogue entry, or ``None`` if it is not a declared capability."""
        return self._catalogue.get(capability_id)

    # -- evaluation --------------------------------------------------------
    def evaluate(self, request: PermissionRequest) -> PermissionEvaluation:
        with self._lock:
            evaluation = self._evaluate_locked(request)

        self._audit.record(
            AuditCategory.PERMISSION,
            f"permission {evaluation.decision.value} for {request.capability_id}",
            actor="system",
            task_id=request.task_id,
            capability_id=request.capability_id,
            risk=evaluation.risk.value,
            permission_decision=evaluation.decision.value,
            parameters={
                "target": request.target,
                "session_id": request.session_id,
                "initiating_utterance": request.initiating_utterance,
                "matched_grant_id": evaluation.matched_grant_id,
            },
            result=evaluation.reason,
        )
        if self._events is not None:
            self._events.publish(
                PermissionEvaluated(
                    source="permissions",
                    capability_id=request.capability_id,
                    risk=evaluation.risk.value,
                    decision=evaluation.decision.value,
                    requires_user_approval=evaluation.requires_user_approval,
                    reason=evaluation.reason,
                    task_id=request.task_id,
                    matched_grant_id=evaluation.matched_grant_id,
                )
            )
            if evaluation.risk is RiskLevel.PROHIBITED:
                self._events.publish(
                    ProhibitedCapabilityBlocked(
                        source="permissions",
                        identifier=request.capability_id,
                        origin="permission_request",
                        detail=evaluation.reason,
                    )
                )
        return evaluation

    def _evaluate_locked(self, request: PermissionRequest) -> PermissionEvaluation:
        capability = self._catalogue.get(request.capability_id)

        # 1. Unknown capability. Absence is never permission.
        if capability is None:
            return PermissionEvaluation(
                capability_id=request.capability_id,
                risk=RiskLevel.PROHIBITED,
                decision=Decision.DENY,
                requires_user_approval=False,
                reason="unknown capability; not present in the catalogue",
            )

        # 2. Prohibited. No grant, setting or approval can reach past this.
        if capability.risk is RiskLevel.PROHIBITED:
            return PermissionEvaluation(
                capability_id=capability.capability_id,
                risk=capability.risk,
                decision=Decision.DENY,
                requires_user_approval=False,
                reason="capability is prohibited in this product and cannot be granted",
            )

        # An explicit deny-grant outranks everything below, including the
        # high-risk ASK path: a user who denied something should not be asked
        # about it again in the same scope.
        deny_grant = self._match_grant(request, decision=Decision.DENY)
        if deny_grant is not None:
            return PermissionEvaluation(
                capability_id=capability.capability_id,
                risk=capability.risk,
                decision=Decision.DENY,
                requires_user_approval=False,
                reason=f"denied by grant scoped to {deny_grant.scope.value}",
                matched_grant_id=deny_grant.grant_id,
            )

        # 3. High risk always asks. Grant validation guarantees no persisted
        #    allow-grant broader than ONCE exists for high-risk capabilities.
        if capability.risk is RiskLevel.HIGH:
            once_grant = self._match_grant(
                request, decision=Decision.ALLOW, only_scope=GrantScope.ONCE
            )
            if once_grant is not None:
                self._consume_grant(once_grant, "single-use approval consumed")
                return PermissionEvaluation(
                    capability_id=capability.capability_id,
                    risk=capability.risk,
                    decision=Decision.ALLOW,
                    requires_user_approval=False,
                    reason="single-use approval for this high-risk action",
                    matched_grant_id=once_grant.grant_id,
                )
            return PermissionEvaluation(
                capability_id=capability.capability_id,
                risk=capability.risk,
                decision=Decision.ASK,
                requires_user_approval=True,
                reason="high-risk capability requires fresh confirmation every time",
            )

        # 4. A matching allow-grant.
        allow_grant = self._match_grant(request, decision=Decision.ALLOW)
        if allow_grant is not None:
            if allow_grant.scope is GrantScope.ONCE:
                self._consume_grant(allow_grant, "single-use approval consumed")
            return PermissionEvaluation(
                capability_id=capability.capability_id,
                risk=capability.risk,
                decision=Decision.ALLOW,
                requires_user_approval=False,
                reason=f"allowed by grant scoped to {allow_grant.scope.value}",
                matched_grant_id=allow_grant.grant_id,
            )

        # 5. Default policy for the risk level.
        default = self._policy.low if capability.risk is RiskLevel.LOW else self._policy.medium
        return PermissionEvaluation(
            capability_id=capability.capability_id,
            risk=capability.risk,
            decision=default,
            requires_user_approval=default is Decision.ASK,
            reason=f"no matching grant; default policy for {capability.risk.value} risk",
        )

    # -- granting ----------------------------------------------------------
    def grant(
        self,
        capability_id: str,
        decision: Decision,
        scope: GrantScope,
        *,
        scope_ref: str | None = None,
        session_id: str | None = None,
        task_id: str | None = None,
        created_by: str = "user",
        expires_at: object | None = None,
        reason: str | None = None,
    ) -> PermissionGrant:
        """Record a permission decision. Validates the permission model first."""
        capability = self._catalogue.get(capability_id)
        if capability is None:
            raise PermissionError(f"unknown capability '{capability_id}'")

        if capability.risk is RiskLevel.PROHIBITED:
            self._audit.record(
                AuditCategory.SECURITY,
                f"refused to grant prohibited capability {capability_id}",
                actor=created_by,
                capability_id=capability_id,
                risk=capability.risk.value,
                permission_decision="deny",
                error="prohibited capability",
            )
            raise ProhibitedCapabilityError(
                f"'{capability_id}' is prohibited and can never be granted"
            )

        if decision is Decision.ALLOW:
            self._validate_allow_scope(capability, scope, scope_ref, session_id, task_id)

        computed_expiry = expires_at
        if (
            computed_expiry is None
            and scope is GrantScope.SESSION
            and self._policy.session_grant_ttl_seconds > 0
        ):
            computed_expiry = utc_now() + timedelta(
                seconds=self._policy.session_grant_ttl_seconds
            )

        grant = PermissionGrant(
            capability_id=capability_id,
            decision=decision,
            scope=scope,
            scope_ref=scope_ref,
            session_id=session_id,
            task_id=task_id,
            created_by=created_by,
            expires_at=computed_expiry,  # type: ignore[arg-type]
            reason=reason,
        )
        self._insert_grant(grant)

        self._audit.record(
            AuditCategory.PERMISSION,
            f"granted {decision.value} for {capability_id} scoped to {scope.value}",
            actor=created_by,
            task_id=task_id,
            capability_id=capability_id,
            risk=capability.risk.value,
            permission_decision=decision.value,
            parameters={"scope": scope.value, "scope_ref": scope_ref, "reason": reason},
        )
        if self._events is not None:
            self._events.publish(
                PermissionGranted(
                    source="permissions",
                    grant_id=grant.grant_id,
                    capability_id=capability_id,
                    scope=scope.value,
                    scope_ref=scope_ref,
                    expires_at=grant.expires_at,
                )
            )
        return grant

    def _validate_allow_scope(
        self,
        capability: Capability,
        scope: GrantScope,
        scope_ref: str | None,
        session_id: str | None,
        task_id: str | None,
    ) -> None:
        if capability.risk is RiskLevel.HIGH and scope is not GrantScope.ONCE:
            # PRD 9.9: high-risk permissions must not offer "always allow";
            # 11.1: they require fresh confirmation every time.
            raise PermissionError(
                f"high-risk capability '{capability.capability_id}' may only be "
                f"allowed with scope 'once', not '{scope.value}'"
            )

        if scope is GrantScope.ALWAYS:
            if capability.risk is not RiskLevel.LOW:
                raise PermissionError(
                    f"'always' allow is only available for low-risk capabilities; "
                    f"'{capability.capability_id}' is {capability.risk.value} risk"
                )
            if not self._policy.allow_always_for_low_risk:
                raise PermissionError("'always' allow is disabled by policy")

        if scope in (GrantScope.APPLICATION, GrantScope.FOLDER) and not scope_ref:
            raise PermissionError(f"scope '{scope.value}' requires a scope_ref")
        if scope is GrantScope.SESSION and not session_id:
            raise PermissionError("scope 'session' requires a session_id")
        if scope is GrantScope.TASK and not task_id:
            raise PermissionError("scope 'task' requires a task_id")

    # -- revocation --------------------------------------------------------
    def revoke(self, grant_id: str, reason: str = "revoked by user") -> bool:
        with self._lock, self._database.transaction() as connection:
            cursor = connection.execute(
                "UPDATE permission_grant SET revoked_at = ?, reason = ? "
                "WHERE grant_id = ? AND revoked_at IS NULL",
                (to_iso(utc_now()), reason, grant_id),
            )
            changed = cursor.rowcount > 0
            capability_id = None
            if changed:
                row = connection.execute(
                    "SELECT capability_id FROM permission_grant WHERE grant_id = ?",
                    (grant_id,),
                ).fetchone()
                capability_id = row["capability_id"] if row else None

        if changed:
            self._audit.record(
                AuditCategory.PERMISSION,
                f"revoked grant {grant_id}",
                actor="user",
                capability_id=capability_id,
                permission_decision="revoked",
                parameters={"reason": reason},
            )
            if self._events is not None:
                self._events.publish(
                    PermissionRevoked(
                        source="permissions",
                        grant_id=grant_id,
                        capability_id=capability_id or "",
                        reason=reason,
                    )
                )
        return changed

    def revoke_session(self, session_id: str) -> int:
        """Revoke every grant tied to a session. Called at shutdown."""
        grants = [g for g in self.list_grants(active_only=True) if g.session_id == session_id]
        for grant in grants:
            self.revoke(grant.grant_id, reason="session ended")
        return len(grants)

    def revoke_task(self, task_id: str) -> int:
        grants = [g for g in self.list_grants(active_only=True) if g.task_id == task_id]
        for grant in grants:
            self.revoke(grant.grant_id, reason="task ended")
        return len(grants)

    # -- persistence -------------------------------------------------------
    def _insert_grant(self, grant: PermissionGrant) -> None:
        with self._database.transaction() as connection:
            connection.execute(
                """
                INSERT INTO permission_grant (
                    grant_id, capability_id, decision, scope, scope_ref, session_id,
                    task_id, created_at, created_by, expires_at, revoked_at, reason
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    grant.grant_id,
                    grant.capability_id,
                    grant.decision.value,
                    grant.scope.value,
                    grant.scope_ref,
                    grant.session_id,
                    grant.task_id,
                    to_iso(grant.created_at),
                    grant.created_by,
                    to_iso(grant.expires_at),
                    to_iso(grant.revoked_at),
                    grant.reason,
                ),
            )

    def _consume_grant(self, grant: PermissionGrant, reason: str) -> None:
        with self._database.transaction() as connection:
            connection.execute(
                "UPDATE permission_grant SET revoked_at = ?, reason = ? WHERE grant_id = ?",
                (to_iso(utc_now()), reason, grant.grant_id),
            )

    def list_grants(
        self, capability_id: str | None = None, *, active_only: bool = False
    ) -> list[PermissionGrant]:
        sql = "SELECT * FROM permission_grant"
        parameters: list[object] = []
        if capability_id is not None:
            sql += " WHERE capability_id = ?"
            parameters.append(capability_id)
        sql += " ORDER BY created_at DESC"
        grants = [self._row_to_grant(row) for row in self._database.query_all(sql, parameters)]
        if active_only:
            now = utc_now()
            grants = [g for g in grants if g.is_active(now)]
        return grants

    @staticmethod
    def _row_to_grant(row: object) -> PermissionGrant:
        data = dict(row)  # type: ignore[arg-type]
        return PermissionGrant(
            grant_id=data["grant_id"],
            capability_id=data["capability_id"],
            decision=Decision(data["decision"]),
            scope=GrantScope(data["scope"]),
            scope_ref=data["scope_ref"],
            session_id=data["session_id"],
            task_id=data["task_id"],
            created_at=from_iso(data["created_at"]),  # type: ignore[arg-type]
            created_by=data["created_by"],
            expires_at=from_iso(data["expires_at"]),
            revoked_at=from_iso(data["revoked_at"]),
            reason=data["reason"],
        )

    # -- matching ----------------------------------------------------------
    def _match_grant(
        self,
        request: PermissionRequest,
        *,
        decision: Decision,
        only_scope: GrantScope | None = None,
    ) -> PermissionGrant | None:
        now = utc_now()
        candidates = [
            grant
            for grant in self.list_grants(request.capability_id)
            if grant.decision is decision and grant.is_active(now)
        ]
        if only_scope is not None:
            candidates = [grant for grant in candidates if grant.scope is only_scope]

        # Narrowest scope first, so a task-scoped decision beats a session one.
        precedence = {
            GrantScope.ONCE: 0,
            GrantScope.TASK: 1,
            GrantScope.FOLDER: 2,
            GrantScope.APPLICATION: 3,
            GrantScope.SESSION: 4,
            GrantScope.ALWAYS: 5,
        }
        candidates.sort(key=lambda grant: precedence[grant.scope])

        for grant in candidates:
            if self._scope_matches(grant, request):
                return grant
        return None

    @staticmethod
    def _scope_matches(grant: PermissionGrant, request: PermissionRequest) -> bool:
        if grant.scope is GrantScope.ALWAYS:
            return True
        if grant.scope is GrantScope.ONCE:
            # A single-use grant may be pinned to a task or target; if it is,
            # the request must match.
            if grant.task_id is not None and grant.task_id != request.task_id:
                return False
            if grant.scope_ref is not None and grant.scope_ref != request.target:
                return False
            return True
        if grant.scope is GrantScope.SESSION:
            return grant.session_id is not None and grant.session_id == request.session_id
        if grant.scope is GrantScope.TASK:
            return grant.task_id is not None and grant.task_id == request.task_id
        if grant.scope is GrantScope.APPLICATION:
            return grant.scope_ref is not None and grant.scope_ref == request.target
        if grant.scope is GrantScope.FOLDER:
            if grant.scope_ref is None or request.target is None:
                return False
            try:
                return _folder_contains(grant.scope_ref, request.target)
            except (OSError, ValueError):
                return False
        return False  # pragma: no cover - GrantScope is exhaustive above
