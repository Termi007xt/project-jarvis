"""The tool invoker — the single choke point (ARCHITECTURE.md section 6.6).

PRD section 13.4 requires six checks before any model-proposed action runs. They
happen here, in this order, and every failure is audited with its reason:

1. allow-list      — registry lookup; an unknown tool is rejected
2. schema          — parameters parsed into the tool's typed input model
3. permission      — PermissionEngine.evaluate for each required capability
4. resource locks  — all-or-nothing acquisition of the declared lock set
5. approval        — if the decision is ASK, the ApprovalPort presents PRD 11.2
6. execute         — bounded timeout, bounded retries, audited before and after

Nothing bypasses this. There is no second path from a plan to an effect.
"""

from __future__ import annotations

import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from typing import Any, Mapping

from pydantic import BaseModel, ValidationError

from jarvis.common import json_dumps, new_id, to_iso, utc_now
from jarvis.core.audit.log import AuditLog
from jarvis.core.audit.models import AuditCategory
from jarvis.core.audit.redaction import redact
from jarvis.core.events.bus import EventBus
from jarvis.core.events.types import ToolInvocationFinished, ToolInvocationStarted
from jarvis.core.permissions.engine import PermissionEngine
from jarvis.core.permissions.models import (
    Decision,
    GrantScope,
    PermissionError as JarvisPermissionError,
    PermissionRequest,
    RiskLevel,
)
from jarvis.core.tools.contract import (
    Tool,
    ToolContext,
    ToolExecution,
    ToolFailure,
    ToolOutcome,
    ToolResult,
    ToolSpec,
    Verification,
)
from jarvis.core.tools.ports import ApprovalPort, ApprovalRequest, DenyingApprovalPort, LockPort
from jarvis.storage.database import Database

__all__ = ["ToolInvoker", "ToolCall"]

_LOG = logging.getLogger(__name__)


class ToolCall(BaseModel):
    """A proposed action. Comes from the planner, the GUI, a skill or a schedule."""

    tool_id: str
    parameters: dict[str, Any] = {}
    task_id: str | None = None
    session_id: str | None = None
    conversation_id: str | None = None
    initiating_utterance: str | None = None
    origin: str = "system"


class ToolInvoker:
    """Validates, permits, locks, approves, executes and audits. In that order."""

    def __init__(
        self,
        registry: Any,
        permissions: PermissionEngine,
        audit: AuditLog,
        *,
        locks: LockPort | None = None,
        approvals: ApprovalPort | None = None,
        event_bus: EventBus | None = None,
        database: Database | None = None,
    ) -> None:
        self._registry = registry
        self._permissions = permissions
        self._audit = audit
        self._locks = locks
        self._approvals = approvals or DenyingApprovalPort()
        self._events = event_bus
        self._database = database
        self._executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="jarvis-tool")

    def shutdown(self, wait: bool = True) -> None:
        self._executor.shutdown(wait=wait, cancel_futures=not wait)

    # -- public API --------------------------------------------------------
    def invoke(self, call: ToolCall, cancel_event: threading.Event | None = None) -> ToolResult:
        invocation_id = new_id()
        started_at = utc_now()

        # --- 1. allow-list -------------------------------------------------
        tool: Tool | None = self._registry.get(call.tool_id)
        if tool is None:
            return self._blocked(
                invocation_id,
                call,
                started_at,
                tool_version="unknown",
                failure_code="unknown_tool",
                message=(
                    f"'{call.tool_id}' is not a registered tool. Only tools in the "
                    f"registry can be called; there is no generic execution path."
                ),
                audit_category=AuditCategory.SECURITY,
            )
        spec = tool.spec

        # --- 2. schema -----------------------------------------------------
        try:
            parameters = spec.input_model.model_validate(call.parameters)
        except ValidationError as exc:
            problems = "; ".join(
                f"{'.'.join(str(p) for p in e['loc'])}: {e['msg']}" for e in exc.errors()
            )
            return self._blocked(
                invocation_id,
                call,
                started_at,
                tool_version=spec.version,
                failure_code="invalid_parameters",
                message=f"parameter validation failed: {problems}",
            )

        target = self._resolve_target(spec, parameters)

        # --- 3. permission -------------------------------------------------
        pending_approval: list[tuple[str, RiskLevel]] = []
        for capability_id in spec.required_capabilities:
            evaluation = self._permissions.evaluate(
                PermissionRequest(
                    capability_id=capability_id,
                    task_id=call.task_id,
                    session_id=call.session_id,
                    target=target,
                    initiating_utterance=call.initiating_utterance,
                    parameters=redact(call.parameters),
                )
            )
            if evaluation.decision is Decision.DENY:
                return self._denied(
                    invocation_id,
                    call,
                    spec,
                    started_at,
                    reason=evaluation.reason,
                    capability_id=capability_id,
                )
            if evaluation.decision is Decision.ASK:
                pending_approval.append((capability_id, evaluation.risk))

        # --- 4. resource locks ---------------------------------------------
        lease = None
        if spec.resource_locks:
            if self._locks is None:
                return self._blocked(
                    invocation_id,
                    call,
                    started_at,
                    tool_version=spec.version,
                    failure_code="locks_unavailable",
                    message=(
                        f"'{spec.tool_id}' declares resource locks {list(spec.resource_locks)} "
                        "but no lock manager is connected"
                    ),
                )
            owner_id = call.task_id or f"invocation:{invocation_id}"
            lease = self._locks.acquire(owner_id, spec.resource_locks, timeout_seconds=0.0)
            if lease is None:
                return self._blocked(
                    invocation_id,
                    call,
                    started_at,
                    tool_version=spec.version,
                    failure_code="resource_busy",
                    message=(
                        f"could not acquire {list(spec.resource_locks)}; another task holds "
                        "them. The request is not lost: queue it behind the holder."
                    ),
                )

        try:
            # --- 5. approval -----------------------------------------------
            for capability_id, risk in pending_approval:
                outcome = self._approvals.request_approval(
                    self._build_approval_request(
                        spec, capability_id, risk, call, parameters, target
                    )
                )
                if not outcome.allowed:
                    return self._denied(
                        invocation_id,
                        call,
                        spec,
                        started_at,
                        reason=outcome.reason or "user denied the request",
                        capability_id=capability_id,
                        actor="user",
                    )
                self._persist_approval(capability_id, risk, outcome, call, target)

            # --- 6. execute -------------------------------------------------
            return self._execute(
                invocation_id, tool, spec, call, parameters, started_at, cancel_event
            )
        finally:
            if lease is not None:
                lease.release()

    # -- step 5 helpers ----------------------------------------------------
    def _build_approval_request(
        self,
        spec: ToolSpec,
        capability_id: str,
        risk: RiskLevel,
        call: ToolCall,
        parameters: BaseModel,
        target: str | None,
    ) -> ApprovalRequest:
        # PRD 9.9 and 11.1: high risk may only ever be approved once.
        offerable = (
            (GrantScope.ONCE,)
            if risk is RiskLevel.HIGH
            else (GrantScope.ONCE, GrantScope.TASK, GrantScope.SESSION)
        )
        return ApprovalRequest(
            capability_id=capability_id,
            risk=risk,
            tool_id=spec.tool_id,
            action_summary=spec.description,
            initiating_utterance=call.initiating_utterance,
            target=target,
            parameters=redact(parameters.model_dump()),
            scope_description=(
                f"{capability_id} for {target}" if target else f"{capability_id} (no target)"
            ),
            reversible=spec.reversible,
            rollback_method=spec.rollback.method if spec.rollback else None,
            task_id=call.task_id,
            offerable_scopes=offerable,
        )

    def _persist_approval(
        self,
        capability_id: str,
        risk: RiskLevel,
        outcome: Any,
        call: ToolCall,
        target: str | None,
    ) -> None:
        """Record the user's decision so a broader scope is honoured next time."""
        scope = outcome.scope
        if risk is RiskLevel.HIGH:
            scope = GrantScope.ONCE  # never widen a high-risk approval
        if scope is GrantScope.ONCE:
            return  # nothing to persist: it was consumed by this invocation
        try:
            self._permissions.grant(
                capability_id,
                Decision.ALLOW,
                scope,
                scope_ref=target,
                session_id=call.session_id,
                task_id=call.task_id,
                created_by="user",
                reason="approved in the approval dialog",
            )
        except JarvisPermissionError as exc:
            # The dialog offered a scope the model forbids. Honour the action
            # for this invocation only, and record why nothing was persisted.
            self._audit.record(
                AuditCategory.SECURITY,
                f"approval scope '{scope.value}' rejected for {capability_id}",
                actor="user",
                capability_id=capability_id,
                risk=risk.value,
                error=str(exc),
            )

    # -- step 6 ------------------------------------------------------------
    def _execute(
        self,
        invocation_id: str,
        tool: Tool,
        spec: ToolSpec,
        call: ToolCall,
        parameters: BaseModel,
        started_at: Any,
        cancel_event: threading.Event | None,
    ) -> ToolResult:
        context = ToolContext(
            invocation_id=invocation_id,
            task_id=call.task_id,
            session_id=call.session_id,
            conversation_id=call.conversation_id,
            initiating_utterance=call.initiating_utterance,
            cancel_event=cancel_event,
        )

        self._audit.record(
            AuditCategory.TOOL,
            f"invoking {spec.tool_id}",
            actor=call.origin,
            task_id=call.task_id,
            conversation_id=call.conversation_id,
            tool_id=spec.tool_id,
            risk=spec.risk.value,
            parameters=parameters.model_dump(),
            pre_state={"changes_state": spec.changes_state, "locks": list(spec.resource_locks)},
        )
        if self._events is not None:
            self._events.publish(
                ToolInvocationStarted(
                    source="tool_invoker",
                    invocation_id=invocation_id,
                    tool_id=spec.tool_id,
                    task_id=call.task_id,
                )
            )

        attempts = 0
        last_failure: ToolFailure | None = None

        while attempts < spec.retry_policy.max_attempts:
            attempts += 1

            if cancel_event is not None and cancel_event.is_set():
                return self._finish(
                    invocation_id, call, spec, started_at, ToolOutcome.CANCELLED,
                    Verification.NOT_APPLICABLE, None, "cancelled before execution", attempts,
                )

            try:
                execution = self._run_with_timeout(tool, context, parameters, spec.timeout_seconds)
            except FutureTimeoutError:
                # A Python thread cannot be forcibly killed. The call is
                # abandoned and reported honestly; the tool's own timeout is the
                # real defence, and this is the backstop.
                return self._finish(
                    invocation_id, call, spec, started_at, ToolOutcome.TIMED_OUT,
                    Verification.UNVERIFIED, "timeout",
                    f"'{spec.tool_id}' exceeded {spec.timeout_seconds}s and was abandoned",
                    attempts,
                )
            except ToolFailure as failure:
                last_failure = failure
                if failure.code not in spec.failure_codes:
                    return self._finish(
                        invocation_id, call, spec, started_at, ToolOutcome.FAILED,
                        Verification.FAILED, "undeclared_failure_code",
                        f"'{spec.tool_id}' reported undeclared failure code "
                        f"'{failure.code}'; declared codes are {list(spec.failure_codes)}",
                        attempts,
                    )
                retryable = failure.code in spec.retry_policy.retry_on
                if retryable and attempts < spec.retry_policy.max_attempts:
                    if spec.retry_policy.backoff_seconds:
                        time.sleep(spec.retry_policy.backoff_seconds)
                    continue
                return self._finish(
                    invocation_id, call, spec, started_at, ToolOutcome.FAILED,
                    Verification.FAILED, failure.code, failure.message, attempts,
                )
            except Exception as exc:  # noqa: BLE001 - an unexpected fault is still a result
                _LOG.exception("tool %s raised an unexpected exception", spec.tool_id)
                return self._finish(
                    invocation_id, call, spec, started_at, ToolOutcome.FAILED,
                    Verification.FAILED, "unhandled_exception",
                    f"{type(exc).__name__}: {exc}", attempts,
                )

            if not isinstance(execution, ToolExecution):
                return self._finish(
                    invocation_id, call, spec, started_at, ToolOutcome.FAILED,
                    Verification.FAILED, "invalid_tool_return",
                    f"'{spec.tool_id}' returned {type(execution).__name__}, expected ToolExecution",
                    attempts,
                )
            if not isinstance(execution.output, spec.output_model):
                return self._finish(
                    invocation_id, call, spec, started_at, ToolOutcome.FAILED,
                    Verification.FAILED, "invalid_tool_return",
                    f"'{spec.tool_id}' returned {type(execution.output).__name__}, "
                    f"expected {spec.output_model.__name__}",
                    attempts,
                )

            # A state-changing tool that could not confirm its effect has not
            # succeeded (PRD FR-048, AT-018).
            outcome = ToolOutcome.SUCCEEDED
            if spec.changes_state and execution.verification is Verification.NOT_APPLICABLE:
                execution = execution.model_copy(update={"verification": Verification.UNVERIFIED})
            if execution.verification is Verification.FAILED:
                outcome = ToolOutcome.FAILED

            return self._finish(
                invocation_id, call, spec, started_at, outcome, execution.verification,
                None, execution.message or "", attempts,
                output=execution.output.model_dump(),
                evidence=execution.evidence,
            )

        # Unreachable while max_attempts >= 1, but keep the failure explicit.
        return self._finish(  # pragma: no cover
            invocation_id, call, spec, started_at, ToolOutcome.FAILED, Verification.FAILED,
            last_failure.code if last_failure else "exhausted",
            "retry attempts exhausted", attempts,
        )

    def _run_with_timeout(
        self, tool: Tool, context: ToolContext, parameters: BaseModel, timeout: float
    ) -> ToolExecution:
        future = self._executor.submit(tool.run, context, parameters)
        return future.result(timeout=timeout)

    # -- result construction ----------------------------------------------
    @staticmethod
    def _resolve_target(spec: ToolSpec, parameters: BaseModel) -> str | None:
        if spec.target_parameter is None:
            return None
        value = getattr(parameters, spec.target_parameter, None)
        return None if value is None else str(value)

    def _blocked(
        self,
        invocation_id: str,
        call: ToolCall,
        started_at: Any,
        *,
        tool_version: str,
        failure_code: str,
        message: str,
        audit_category: AuditCategory = AuditCategory.TOOL,
    ) -> ToolResult:
        self._audit.record(
            audit_category,
            f"blocked {call.tool_id}: {failure_code}",
            actor=call.origin,
            task_id=call.task_id,
            tool_id=call.tool_id,
            parameters=call.parameters,
            result="blocked",
            verification=Verification.NOT_APPLICABLE.value,
            error=message,
        )
        return self._emit(
            ToolResult(
                invocation_id=invocation_id,
                tool_id=call.tool_id,
                tool_version=tool_version,
                outcome=ToolOutcome.BLOCKED,
                verification=Verification.NOT_APPLICABLE,
                failure_code=failure_code,
                message=message,
                attempts=0,
                task_id=call.task_id,
                started_at=started_at,
                ended_at=utc_now(),
            )
        )

    def _denied(
        self,
        invocation_id: str,
        call: ToolCall,
        spec: ToolSpec,
        started_at: Any,
        *,
        reason: str,
        capability_id: str,
        actor: str = "system",
    ) -> ToolResult:
        self._audit.record(
            AuditCategory.PERMISSION,
            f"denied {spec.tool_id} ({capability_id})",
            actor=actor,
            task_id=call.task_id,
            tool_id=spec.tool_id,
            capability_id=capability_id,
            risk=spec.risk.value,
            permission_decision=Decision.DENY.value,
            parameters=call.parameters,
            result="denied",
            error=reason,
        )
        return self._emit(
            ToolResult(
                invocation_id=invocation_id,
                tool_id=spec.tool_id,
                tool_version=spec.version,
                outcome=ToolOutcome.DENIED,
                verification=Verification.NOT_APPLICABLE,
                failure_code="permission_denied",
                message=reason,
                attempts=0,
                task_id=call.task_id,
                started_at=started_at,
                ended_at=utc_now(),
            )
        )

    def _finish(
        self,
        invocation_id: str,
        call: ToolCall,
        spec: ToolSpec,
        started_at: Any,
        outcome: ToolOutcome,
        verification: Verification,
        failure_code: str | None,
        message: str,
        attempts: int,
        output: dict[str, Any] | None = None,
        evidence: dict[str, Any] | None = None,
    ) -> ToolResult:
        result = ToolResult(
            invocation_id=invocation_id,
            tool_id=spec.tool_id,
            tool_version=spec.version,
            outcome=outcome,
            verification=verification,
            failure_code=failure_code,
            message=message,
            output=output,
            evidence=evidence,
            attempts=attempts,
            task_id=call.task_id,
            started_at=started_at,
            ended_at=utc_now(),
        )

        self._audit.record(
            AuditCategory.TOOL,
            f"{spec.tool_id} {outcome.value} ({verification.value})",
            actor=call.origin,
            task_id=call.task_id,
            conversation_id=call.conversation_id,
            tool_id=spec.tool_id,
            risk=spec.risk.value,
            parameters={"attempts": attempts},
            result=outcome.value,
            verification=verification.value,
            error=message if outcome is not ToolOutcome.SUCCEEDED else None,
            evidence_ref=json_dumps(evidence) if evidence else None,
        )
        self._persist_invocation(result)
        return self._emit(result)

    def _persist_invocation(self, result: ToolResult) -> None:
        if self._database is None:
            return
        try:
            with self._database.transaction() as connection:
                connection.execute(
                    """
                    INSERT INTO tool_invocation (
                        invocation_id, tool_id, tool_version, task_id, outcome,
                        failure_code, verification, attempts, started_at, ended_at,
                        duration_ms
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        result.invocation_id,
                        result.tool_id,
                        result.tool_version,
                        result.task_id,
                        result.outcome.value,
                        result.failure_code,
                        result.verification.value,
                        result.attempts,
                        to_iso(result.started_at),
                        to_iso(result.ended_at),
                        result.duration_ms,
                    ),
                )
        except Exception:  # noqa: BLE001 - metrics must never break an invocation
            _LOG.exception("could not persist tool invocation %s", result.invocation_id)

    def _emit(self, result: ToolResult) -> ToolResult:
        if self._events is not None:
            self._events.publish(
                ToolInvocationFinished(
                    source="tool_invoker",
                    invocation_id=result.invocation_id,
                    tool_id=result.tool_id,
                    outcome=result.outcome.value,
                    verification=result.verification.value,
                    failure_code=result.failure_code,
                    attempts=result.attempts,
                    task_id=result.task_id,
                )
            )
        return result

    # -- introspection -----------------------------------------------------
    def describe_tools(self) -> list[Mapping[str, Any]]:
        return self._registry.describe_for_model()
