"""The six-step invoker pipeline (PRD section 13.4, ARCHITECTURE.md 6.6)."""

from __future__ import annotations

import time

import pytest
from pydantic import BaseModel

from jarvis.core.permissions.models import Decision, GrantScope, RiskLevel
from jarvis.core.tools.contract import (
    RetryPolicy,
    ToolExecution,
    ToolFailure,
    ToolOutcome,
    ToolSpec,
    Verification,
)
from jarvis.core.tools.invoker import ToolCall
from jarvis.core.tools.ports import ApprovalOutcome, AutoApprovalPort


class Params(BaseModel):
    value: str = "x"
    target: str | None = None


class Result(BaseModel):
    echoed: str = ""


def make_tool(
    tool_id: str = "test.tool",
    *,
    risk: RiskLevel = RiskLevel.LOW,
    capabilities: tuple[str, ...] = ("system.read_health",),
    locks: tuple[str, ...] = (),
    changes_state: bool = False,
    verification: Verification = Verification.NOT_APPLICABLE,
    behaviour=None,
    timeout: float = 5.0,
    retry: RetryPolicy | None = None,
    failure_codes: tuple[str, ...] = ("boom", "transient"),
    target_parameter: str | None = None,
):
    class _Tool:
        spec = ToolSpec(
            tool_id=tool_id,
            version="1.0.0",
            description="a test tool",
            input_model=Params,
            output_model=Result,
            risk=risk,
            required_capabilities=capabilities,
            resource_locks=locks,
            timeout_seconds=timeout,
            retry_policy=retry or RetryPolicy(max_attempts=1),
            changes_state=changes_state,
            verification="test",
            failure_codes=failure_codes,
            target_parameter=target_parameter,
        )

        def __init__(self) -> None:
            self.calls = 0

        def run(self, context, parameters):
            self.calls += 1
            if behaviour is not None:
                return behaviour(self, context, parameters)
            return ToolExecution(
                output=Result(echoed=parameters.value), verification=verification
            )

    return _Tool()


def allow(permissions, capability="system.read_health"):
    permissions.grant(capability, Decision.ALLOW, GrantScope.ALWAYS, created_by="test")


# -- step 1: allow-list -----------------------------------------------------
def test_an_unregistered_tool_is_blocked(invoker) -> None:
    result = invoker.invoke(ToolCall(tool_id="does.not.exist"))
    assert result.outcome is ToolOutcome.BLOCKED
    assert result.failure_code == "unknown_tool"
    assert not result.succeeded


def test_an_unknown_tool_is_recorded_as_a_security_event(invoker, audit) -> None:
    invoker.invoke(ToolCall(tool_id="hallucinated.tool"))
    categories = [record["category"] for record in audit.read_all()]
    assert "security" in categories


# -- step 2: schema ---------------------------------------------------------
def test_invalid_parameters_are_blocked_before_permission_evaluation(
    registry, invoker, permissions, audit
) -> None:
    registry.register(make_tool())
    result = invoker.invoke(ToolCall(tool_id="test.tool", parameters={"value": 123, "bogus": 1}))
    assert result.outcome is ToolOutcome.BLOCKED
    assert result.failure_code == "invalid_parameters"
    assert "bogus" in result.message or "value" in result.message


# -- step 3: permission -----------------------------------------------------
def test_a_denied_capability_stops_the_call(registry, invoker, permissions) -> None:
    registry.register(make_tool())
    permissions.grant(
        "system.read_health", Decision.DENY, GrantScope.ALWAYS, created_by="test"
    )
    result = invoker.invoke(ToolCall(tool_id="test.tool"))
    assert result.outcome is ToolOutcome.DENIED
    assert result.failure_code == "permission_denied"


def test_the_tool_never_runs_when_permission_is_denied(registry, invoker, permissions) -> None:
    tool = make_tool()
    registry.register(tool)
    permissions.grant(
        "system.read_health", Decision.DENY, GrantScope.ALWAYS, created_by="test"
    )
    invoker.invoke(ToolCall(tool_id="test.tool"))
    assert tool.calls == 0


def test_the_permission_target_comes_from_the_declared_parameter(
    registry, invoker, permissions
) -> None:
    registry.register(
        make_tool(
            tool_id="test.scoped",
            capabilities=("fs.read_approved",),
            risk=RiskLevel.MEDIUM,
            target_parameter="target",
        )
    )
    permissions.grant(
        "fs.read_approved",
        Decision.ALLOW,
        GrantScope.APPLICATION,
        scope_ref="allowed-target",
        created_by="test",
    )
    ok = invoker.invoke(
        ToolCall(tool_id="test.scoped", parameters={"target": "allowed-target"})
    )
    assert ok.outcome is ToolOutcome.SUCCEEDED

    denied = invoker.invoke(
        ToolCall(tool_id="test.scoped", parameters={"target": "other-target"})
    )
    assert denied.outcome is ToolOutcome.DENIED


# -- step 4: locks ----------------------------------------------------------
def test_a_held_lock_blocks_the_call(registry, invoker, permissions, locks) -> None:
    registry.register(make_tool(locks=("foreground_desktop",)))
    allow(permissions)
    locks.acquire("someone-else", ["foreground_desktop"])

    result = invoker.invoke(ToolCall(tool_id="test.tool"))
    assert result.outcome is ToolOutcome.BLOCKED
    assert result.failure_code == "resource_busy"


def test_locks_are_released_after_the_call(registry, invoker, permissions, locks) -> None:
    registry.register(make_tool(locks=("clipboard",)))
    allow(permissions)
    invoker.invoke(ToolCall(tool_id="test.tool", task_id="t1"))
    assert not locks.is_held("clipboard")


def test_locks_are_released_even_when_the_tool_raises(
    registry, invoker, permissions, locks
) -> None:
    def explode(_self, _ctx, _params):
        raise RuntimeError("kaboom")

    registry.register(make_tool(locks=("clipboard",), behaviour=explode))
    allow(permissions)
    result = invoker.invoke(ToolCall(tool_id="test.tool", task_id="t1"))
    assert result.outcome is ToolOutcome.FAILED
    assert not locks.is_held("clipboard")


# -- step 5: approval -------------------------------------------------------
def test_without_an_approval_interface_nothing_requiring_approval_runs(
    registry, invoker, permissions
) -> None:
    """ADR-0010: silence is never consent."""
    tool = make_tool()
    registry.register(tool)
    result = invoker.invoke(ToolCall(tool_id="test.tool"))
    assert result.outcome is ToolOutcome.DENIED
    assert "no approval interface" in result.message
    assert tool.calls == 0


def test_an_approved_call_runs(registry, approving_invoker, permissions) -> None:
    tool = make_tool()
    registry.register(tool)
    result = approving_invoker.invoke(ToolCall(tool_id="test.tool"))
    assert result.outcome is ToolOutcome.SUCCEEDED
    assert tool.calls == 1


def test_high_risk_is_never_auto_approved(registry, approving_invoker, permissions) -> None:
    tool = make_tool(
        tool_id="test.dangerous",
        risk=RiskLevel.HIGH,
        capabilities=("fs.delete_or_overwrite",),
        changes_state=True,
        verification=Verification.VERIFIED,
    )
    registry.register(tool)
    result = approving_invoker.invoke(ToolCall(tool_id="test.dangerous"))
    assert result.outcome is ToolOutcome.DENIED
    assert tool.calls == 0


def test_the_approval_request_carries_the_prd_11_2_fields(
    registry, approving_invoker, permissions
) -> None:
    port = approving_invoker._approvals  # noqa: SLF001 - inspecting the test double
    assert isinstance(port, AutoApprovalPort)
    registry.register(
        make_tool(
            tool_id="test.scoped",
            capabilities=("fs.read_approved",),
            risk=RiskLevel.MEDIUM,
            target_parameter="target",
        )
    )
    approving_invoker.invoke(
        ToolCall(
            tool_id="test.scoped",
            parameters={"target": "C:/approved"},
            initiating_utterance="read my notes",
        )
    )
    request = port.requests[-1]
    assert request.capability_id == "fs.read_approved"
    assert request.risk is RiskLevel.MEDIUM
    assert request.tool_id == "test.scoped"
    assert request.initiating_utterance == "read my notes"
    assert request.target == "C:/approved"
    assert request.scope_description
    assert GrantScope.ONCE in request.offerable_scopes


def test_high_risk_approval_offers_only_a_single_use(registry, permissions, audit, locks, events, database) -> None:
    from jarvis.core.tools.invoker import ToolInvoker

    port = AutoApprovalPort(decision=Decision.DENY)
    inv = ToolInvoker(registry, permissions, audit, locks=locks, approvals=port,
                      event_bus=events, database=database)
    registry.register(
        make_tool(
            tool_id="test.dangerous",
            risk=RiskLevel.HIGH,
            capabilities=("fs.delete_or_overwrite",),
            changes_state=True,
        )
    )
    inv.invoke(ToolCall(tool_id="test.dangerous"))
    assert port.requests[-1].offerable_scopes == (GrantScope.ONCE,)
    inv.shutdown(wait=False)


def test_the_offered_scopes_follow_the_adr_0027_table(
    registry, permissions, audit, locks, events, database
) -> None:
    """Low may be always, medium may be per-task, high is single use only."""
    from jarvis.core.tools.invoker import ToolInvoker

    port = AutoApprovalPort(decision=Decision.DENY)
    inv = ToolInvoker(registry, permissions, audit, locks=locks, approvals=port,
                      event_bus=events, database=database)
    registry.register(make_tool(tool_id="test.low", capabilities=("notify.show",)))
    registry.register(
        make_tool(tool_id="test.medium", risk=RiskLevel.MEDIUM, capabilities=("clipboard.read",))
    )

    inv.invoke(ToolCall(tool_id="test.low"))
    assert port.requests[-1].offerable_scopes == (GrantScope.ONCE, GrantScope.ALWAYS)

    inv.invoke(ToolCall(tool_id="test.medium"))
    assert port.requests[-1].offerable_scopes == (GrantScope.ONCE, GrantScope.TASK)

    for request in port.requests:
        assert GrantScope.SESSION not in request.offerable_scopes
    inv.shutdown(wait=False)


def test_a_scoped_capability_offers_to_remember_the_denial(
    registry, permissions, audit, locks, events, database
) -> None:
    from jarvis.core.tools.invoker import ToolInvoker

    port = AutoApprovalPort(decision=Decision.DENY)
    inv = ToolInvoker(registry, permissions, audit, locks=locks, approvals=port,
                      event_bus=events, database=database)
    registry.register(
        make_tool(
            tool_id="test.scoped_deny",
            risk=RiskLevel.MEDIUM,
            capabilities=("fs.read_approved",),
            target_parameter="target",
        )
    )
    inv.invoke(ToolCall(tool_id="test.scoped_deny", parameters={"target": "C:/notes"}))
    options = port.requests[-1].denial_options
    assert len(options) == 1
    assert options[0].scope is GrantScope.FOLDER
    assert options[0].scope_ref == "C:/notes"
    inv.shutdown(wait=False)


def test_a_remembered_denial_stops_jarvis_asking_again(
    registry, permissions, audit, locks, events, database, tmp_path
) -> None:
    """ADR-0027: a refusal the user asked to be remembered has to stick."""
    from jarvis.core.tools.approvals import ApprovalQueue
    from jarvis.core.tools.invoker import ToolInvoker
    from jarvis.core.tools.ports import RememberDenialOption

    folder = str(tmp_path / "notes")

    class RememberingPort:
        def __init__(self) -> None:
            self.requests = []

        def request_approval(self, request):
            self.requests.append(request)
            return ApprovalOutcome(
                decision=Decision.DENY,
                reason="not this folder",
                remember_denial=request.denial_options[0],
            )

    port = RememberingPort()
    inv = ToolInvoker(registry, permissions, audit, locks=locks, approvals=port,
                      event_bus=events, database=database)
    registry.register(
        make_tool(
            tool_id="test.remembered",
            risk=RiskLevel.MEDIUM,
            capabilities=("fs.read_approved",),
            target_parameter="target",
        )
    )

    first = inv.invoke(ToolCall(tool_id="test.remembered", parameters={"target": folder}))
    assert first.outcome is ToolOutcome.DENIED
    assert len(port.requests) == 1

    second = inv.invoke(ToolCall(tool_id="test.remembered", parameters={"target": folder}))
    assert second.outcome is ToolOutcome.DENIED
    assert len(port.requests) == 1, "the remembered denial should prevent a second prompt"
    assert "denied by grant" in second.message

    assert ApprovalQueue and RememberDenialOption  # imported for the reader's benefit
    inv.shutdown(wait=False)


def test_a_timed_out_approval_denies_the_invocation(
    registry, permissions, audit, locks, events, database
) -> None:
    """End to end: nobody answers, and the tool does not run."""
    from jarvis.core.tools.approvals import ApprovalQueue
    from jarvis.core.tools.invoker import ToolInvoker

    queue = ApprovalQueue(audit=audit, event_bus=events, timeout_seconds=0.2)
    queue.set_interactive(True)
    inv = ToolInvoker(registry, permissions, audit, locks=locks, approvals=queue,
                      event_bus=events, database=database)
    tool = make_tool(tool_id="test.ignored", risk=RiskLevel.MEDIUM,
                     capabilities=("clipboard.read",))
    registry.register(tool)

    result = inv.invoke(ToolCall(tool_id="test.ignored"))
    assert result.outcome is ToolOutcome.DENIED
    assert tool.calls == 0
    inv.shutdown(wait=False)


def test_a_broader_approval_scope_is_persisted_as_a_grant(
    registry, permissions, audit, locks, events, database
) -> None:
    from jarvis.core.tools.invoker import ToolInvoker

    port = AutoApprovalPort(decision=Decision.ALLOW, scope=GrantScope.SESSION)
    inv = ToolInvoker(registry, permissions, audit, locks=locks, approvals=port,
                      event_bus=events, database=database)
    registry.register(make_tool(capabilities=("clipboard.read",), risk=RiskLevel.MEDIUM))

    inv.invoke(ToolCall(tool_id="test.tool", session_id="s1"))
    assert len(port.requests) == 1

    inv.invoke(ToolCall(tool_id="test.tool", session_id="s1"))
    assert len(port.requests) == 1, "the session grant should avoid a second prompt"
    inv.shutdown(wait=False)


# -- step 6: execution ------------------------------------------------------
def test_a_declared_failure_is_reported_with_its_code(
    registry, approving_invoker, permissions
) -> None:
    def fail(_self, _ctx, _params):
        raise ToolFailure("boom", "it went wrong")

    registry.register(make_tool(behaviour=fail))
    result = approving_invoker.invoke(ToolCall(tool_id="test.tool"))
    assert result.outcome is ToolOutcome.FAILED
    assert result.failure_code == "boom"


def test_an_undeclared_failure_code_is_rejected(registry, approving_invoker) -> None:
    """A tool cannot invent a vague error."""

    def fail(_self, _ctx, _params):
        raise ToolFailure("mystery", "undeclared")

    registry.register(make_tool(behaviour=fail))
    result = approving_invoker.invoke(ToolCall(tool_id="test.tool"))
    assert result.failure_code == "undeclared_failure_code"


def test_an_unexpected_exception_becomes_a_typed_result(registry, approving_invoker) -> None:
    def explode(_self, _ctx, _params):
        raise ValueError("unexpected")

    registry.register(make_tool(behaviour=explode))
    result = approving_invoker.invoke(ToolCall(tool_id="test.tool"))
    assert result.outcome is ToolOutcome.FAILED
    assert result.failure_code == "unhandled_exception"


def test_retries_are_bounded_and_only_for_declared_codes(
    registry, approving_invoker
) -> None:
    attempts = {"n": 0}

    def flaky(_self, _ctx, _params):
        attempts["n"] += 1
        raise ToolFailure("transient", "try again")

    registry.register(
        make_tool(
            behaviour=flaky,
            retry=RetryPolicy(max_attempts=3, backoff_seconds=0.0, retry_on=("transient",)),
        )
    )
    result = approving_invoker.invoke(ToolCall(tool_id="test.tool"))
    assert attempts["n"] == 3
    assert result.attempts == 3
    assert result.outcome is ToolOutcome.FAILED


def test_a_non_retryable_failure_is_not_retried(registry, approving_invoker) -> None:
    attempts = {"n": 0}

    def fail(_self, _ctx, _params):
        attempts["n"] += 1
        raise ToolFailure("boom", "permanent")

    registry.register(
        make_tool(
            behaviour=fail,
            retry=RetryPolicy(max_attempts=3, backoff_seconds=0.0, retry_on=("transient",)),
        )
    )
    approving_invoker.invoke(ToolCall(tool_id="test.tool"))
    assert attempts["n"] == 1


def test_a_retry_policy_must_name_the_codes_it_retries() -> None:
    with pytest.raises(ValueError, match="must name the failure codes"):
        RetryPolicy(max_attempts=3)


def test_a_slow_tool_times_out(registry, approving_invoker) -> None:
    def slow(_self, _ctx, _params):
        time.sleep(2.0)
        return ToolExecution(output=Result(), verification=Verification.NOT_APPLICABLE)

    registry.register(make_tool(behaviour=slow, timeout=0.2))
    result = approving_invoker.invoke(ToolCall(tool_id="test.tool"))
    assert result.outcome is ToolOutcome.TIMED_OUT
    assert result.verification is Verification.UNVERIFIED


# -- honesty ----------------------------------------------------------------
def test_a_state_changing_tool_that_cannot_verify_is_not_a_success(
    registry, approving_invoker
) -> None:
    """PRD FR-048 and AT-018: 'I clicked it' is not 'it worked'."""
    registry.register(
        make_tool(
            tool_id="test.changer",
            capabilities=("fs.write_approved",),
            risk=RiskLevel.MEDIUM,
            changes_state=True,
            verification=Verification.NOT_APPLICABLE,
        )
    )
    result = approving_invoker.invoke(ToolCall(tool_id="test.changer"))
    assert result.verification is Verification.UNVERIFIED
    assert not result.succeeded, "unverified must never count as success"


def test_a_verified_state_change_is_a_success(registry, approving_invoker) -> None:
    registry.register(
        make_tool(
            tool_id="test.changer",
            capabilities=("fs.write_approved",),
            risk=RiskLevel.MEDIUM,
            changes_state=True,
            verification=Verification.VERIFIED,
        )
    )
    result = approving_invoker.invoke(ToolCall(tool_id="test.changer"))
    assert result.succeeded


def test_failed_verification_makes_the_outcome_failed(registry, approving_invoker) -> None:
    registry.register(
        make_tool(
            tool_id="test.changer",
            capabilities=("fs.write_approved",),
            risk=RiskLevel.MEDIUM,
            changes_state=True,
            verification=Verification.FAILED,
        )
    )
    result = approving_invoker.invoke(ToolCall(tool_id="test.changer"))
    assert result.outcome is ToolOutcome.FAILED
    assert not result.succeeded


def test_a_tool_returning_the_wrong_type_is_rejected(registry, approving_invoker) -> None:
    class Other(BaseModel):
        pass

    def wrong(_self, _ctx, _params):
        return ToolExecution(output=Other(), verification=Verification.NOT_APPLICABLE)

    registry.register(make_tool(behaviour=wrong))
    result = approving_invoker.invoke(ToolCall(tool_id="test.tool"))
    assert result.failure_code == "invalid_tool_return"


# -- auditing and persistence ----------------------------------------------
def test_every_invocation_is_audited_and_persisted(
    registry, approving_invoker, database, audit
) -> None:
    registry.register(make_tool())
    result = approving_invoker.invoke(ToolCall(tool_id="test.tool"))

    rows = database.query_all("SELECT * FROM tool_invocation WHERE invocation_id = ?",
                              (result.invocation_id,))
    assert len(rows) == 1
    assert rows[0]["outcome"] == "succeeded"
    assert any(record["tool_id"] == "test.tool" for record in audit.read_all())


def test_cancellation_before_execution_is_reported(registry, approving_invoker) -> None:
    import threading

    tool = make_tool()
    registry.register(tool)
    cancel = threading.Event()
    cancel.set()

    result = approving_invoker.invoke(ToolCall(tool_id="test.tool"), cancel_event=cancel)
    assert result.outcome is ToolOutcome.CANCELLED
    assert tool.calls == 0


def test_describe_for_model_exposes_only_registered_tools(registry, approving_invoker) -> None:
    registry.register(make_tool())
    described = approving_invoker.describe_tools()
    assert [entry["name"] for entry in described] == ["test.tool"]
    assert "parameters" in described[0]
