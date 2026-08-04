"""The approval queue (ADR-0027).

The timeout path is the security-critical one and gets the most attention here:
a non-modal surface can be missed, and what happens when it is missed decides
whether "silence is never consent" is a policy or a slogan.
"""

from __future__ import annotations

import threading
import time

import pytest

from jarvis.core.permissions.catalogue import CAPABILITIES
from jarvis.core.permissions.models import Decision, GrantScope, RiskLevel
from jarvis.core.tools.approvals import ApprovalQueue
from jarvis.core.tools.ports import (
    ApprovalRequest,
    RememberDenialOption,
    denial_options_for,
    offerable_scopes_for,
)


def make_request(
    *,
    risk: RiskLevel = RiskLevel.MEDIUM,
    capability_id: str = "clipboard.read",
    target: str | None = None,
    task_id: str | None = None,
) -> ApprovalRequest:
    capability = CAPABILITIES.get(capability_id)
    return ApprovalRequest(
        capability_id=capability_id,
        capability_title=capability.title if capability else capability_id,
        risk=risk,
        tool_id="test.tool",
        action_summary="do the thing",
        scope_description="the thing, once",
        task_id=task_id,
        target=target,
        offerable_scopes=offerable_scopes_for(risk),
        denial_options=denial_options_for(capability, target),
    )


@pytest.fixture
def queue(audit, events) -> ApprovalQueue:
    q = ApprovalQueue(audit=audit, event_bus=events, timeout_seconds=0.3)
    q.set_interactive(True)
    return q


# -- the offered-scope table (ADR-0027) -------------------------------------
def test_low_risk_may_be_allowed_always() -> None:
    assert offerable_scopes_for(RiskLevel.LOW) == (GrantScope.ONCE, GrantScope.ALWAYS)


def test_low_risk_loses_always_when_policy_forbids_it() -> None:
    scopes = offerable_scopes_for(RiskLevel.LOW, allow_always_for_low_risk=False)
    assert scopes == (GrantScope.ONCE,)


def test_medium_risk_is_offered_once_or_for_this_task() -> None:
    assert offerable_scopes_for(RiskLevel.MEDIUM) == (GrantScope.ONCE, GrantScope.TASK)


def test_high_risk_is_offered_single_use_only() -> None:
    """PRD 9.9 and 11.1: fresh confirmation every time."""
    assert offerable_scopes_for(RiskLevel.HIGH) == (GrantScope.ONCE,)


def test_allow_for_this_session_is_never_offered() -> None:
    """The engine still supports SESSION; the dialog deliberately does not."""
    for risk in (RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH):
        assert GrantScope.SESSION not in offerable_scopes_for(risk)


def test_a_prohibited_capability_is_offered_nothing() -> None:
    assert offerable_scopes_for(RiskLevel.PROHIBITED) == ()


# -- rememberable denials ---------------------------------------------------
def test_an_application_scoped_capability_offers_to_remember_the_denial() -> None:
    options = denial_options_for(CAPABILITIES["app.open_approved"], "Brave")
    assert len(options) == 1
    assert options[0].scope is GrantScope.APPLICATION
    assert options[0].scope_ref == "Brave"
    assert "application" in options[0].label


def test_a_folder_scoped_capability_offers_a_folder_denial() -> None:
    options = denial_options_for(CAPABILITIES["fs.read_approved"], "C:/notes")
    assert options[0].scope is GrantScope.FOLDER


def test_a_url_capability_says_site_rather_than_application() -> None:
    """The button must not overstate what a remembered denial covers."""
    options = denial_options_for(CAPABILITIES["web.open_approved_url"], "youtube.com")
    assert "site" in options[0].label


def test_nothing_is_offered_without_a_target() -> None:
    assert denial_options_for(CAPABILITIES["app.open_approved"], None) == ()


def test_nothing_is_offered_for_a_capability_with_no_scope_kind() -> None:
    assert denial_options_for(CAPABILITIES["clipboard.read"], "anything") == ()


# -- answering --------------------------------------------------------------
def test_an_answered_request_returns_the_users_decision(queue: ApprovalQueue) -> None:
    request = make_request()
    outcomes = []

    thread = threading.Thread(target=lambda: outcomes.append(queue.request_approval(request)))
    thread.start()
    _wait_for_pending(queue)

    assert queue.answer(request.approval_id, Decision.ALLOW, scope=GrantScope.TASK)
    thread.join(timeout=2)

    assert outcomes[0].allowed
    assert outcomes[0].scope is GrantScope.TASK
    assert not outcomes[0].timed_out


def test_the_dialog_cannot_offer_a_scope_the_request_did_not(queue: ApprovalQueue) -> None:
    """A UI defect must not be able to widen a high-risk approval."""
    request = make_request(risk=RiskLevel.HIGH, capability_id="fs.delete_or_overwrite")
    thread = threading.Thread(target=lambda: queue.request_approval(request))
    thread.start()
    _wait_for_pending(queue)

    with pytest.raises(ValueError, match="was not offered"):
        queue.answer(request.approval_id, Decision.ALLOW, scope=GrantScope.ALWAYS)

    queue.answer(request.approval_id, Decision.DENY)
    thread.join(timeout=2)


def test_a_denial_can_carry_a_remembered_scope(queue: ApprovalQueue) -> None:
    request = make_request(capability_id="fs.read_approved", target="C:/notes")
    outcomes = []
    thread = threading.Thread(target=lambda: outcomes.append(queue.request_approval(request)))
    thread.start()
    _wait_for_pending(queue)

    queue.answer(
        request.approval_id,
        Decision.DENY,
        remember_denial=request.denial_options[0],
    )
    thread.join(timeout=2)

    assert outcomes[0].decision is Decision.DENY
    assert outcomes[0].remember_denial is not None
    assert outcomes[0].remember_denial.scope is GrantScope.FOLDER


def test_an_unoffered_denial_scope_is_refused(queue: ApprovalQueue) -> None:
    request = make_request(capability_id="fs.read_approved", target="C:/notes")
    thread = threading.Thread(target=lambda: queue.request_approval(request))
    thread.start()
    _wait_for_pending(queue)

    forged = RememberDenialOption(
        scope=GrantScope.ALWAYS, scope_ref="everything", label="Never ask again about anything"
    )
    with pytest.raises(ValueError, match="was not offered"):
        queue.answer(request.approval_id, Decision.DENY, remember_denial=forged)

    queue.answer(request.approval_id, Decision.DENY)
    thread.join(timeout=2)


def test_a_remembered_denial_cannot_accompany_an_allow(queue: ApprovalQueue) -> None:
    request = make_request(capability_id="fs.read_approved", target="C:/notes")
    thread = threading.Thread(target=lambda: queue.request_approval(request))
    thread.start()
    _wait_for_pending(queue)

    with pytest.raises(ValueError, match="only accompanies a denial"):
        queue.answer(
            request.approval_id,
            Decision.ALLOW,
            remember_denial=request.denial_options[0],
        )
    queue.answer(request.approval_id, Decision.DENY)
    thread.join(timeout=2)


def test_answering_an_unknown_request_reports_that_nothing_was_waiting(
    queue: ApprovalQueue,
) -> None:
    assert queue.answer("no-such-approval", Decision.ALLOW) is False


# -- the timeout path -------------------------------------------------------
def test_an_unanswered_request_is_denied_not_allowed(queue: ApprovalQueue) -> None:
    """ADR-0010 and ADR-0027: silence is never consent."""
    outcome = queue.request_approval(make_request())
    assert outcome.decision is Decision.DENY
    assert outcome.timed_out
    assert not outcome.allowed
    assert "denial" in outcome.reason


def test_a_timed_out_request_stops_being_pending(queue: ApprovalQueue) -> None:
    queue.request_approval(make_request())
    assert queue.pending() == ()
    assert not queue.has_pending


def test_a_timeout_is_audited_as_denied(queue: ApprovalQueue, audit) -> None:
    queue.request_approval(make_request())
    summaries = [record.get("result") for record in audit.query(limit=50)]
    assert "denied_by_timeout" in summaries


def test_no_timeout_can_be_configured_away(audit, events) -> None:
    """A zero or negative timeout would mean an unbounded wait (NFR-013)."""
    with pytest.raises(ValueError):
        ApprovalQueue(audit=audit, event_bus=events, timeout_seconds=0)


# -- no interface attached --------------------------------------------------
def test_without_an_attached_interface_everything_is_denied_immediately(audit, events) -> None:
    queue = ApprovalQueue(audit=audit, event_bus=events, timeout_seconds=30)
    started = time.monotonic()
    outcome = queue.request_approval(make_request())
    assert outcome.decision is Decision.DENY
    assert "no approval interface" in outcome.reason
    # It must not have waited out the 30s timeout to say so.
    assert time.monotonic() - started < 5


def test_detaching_the_interface_denies_what_was_waiting(queue: ApprovalQueue) -> None:
    request = make_request()
    outcomes = []
    thread = threading.Thread(target=lambda: outcomes.append(queue.request_approval(request)))
    thread.start()
    _wait_for_pending(queue)

    queue.set_interactive(False)
    thread.join(timeout=2)
    assert outcomes[0].decision is Decision.DENY


def test_deny_all_reports_how_many_it_stopped(queue: ApprovalQueue) -> None:
    requests = [make_request(), make_request()]
    threads = [
        threading.Thread(target=lambda r=r: queue.request_approval(r)) for r in requests
    ]
    for thread in threads:
        thread.start()
    _wait_for_pending(queue, count=2)

    assert queue.deny_all("emergency stop") == 2
    for thread in threads:
        thread.join(timeout=2)


# -- events -----------------------------------------------------------------
def test_a_request_and_its_resolution_are_both_announced(queue: ApprovalQueue, events) -> None:
    from jarvis.core.events.types import ApprovalRequested, ApprovalResolved

    seen: list[object] = []
    events.subscribe(ApprovalRequested, seen.append)
    events.subscribe(ApprovalResolved, seen.append)

    request = make_request()
    thread = threading.Thread(target=lambda: queue.request_approval(request))
    thread.start()
    _wait_for_pending(queue)
    queue.answer(request.approval_id, Decision.DENY)
    thread.join(timeout=2)

    assert isinstance(seen[0], ApprovalRequested)
    assert isinstance(seen[1], ApprovalResolved)
    assert seen[1].decision == "deny"


def test_the_announcement_carries_no_parameter_values(queue: ApprovalQueue, events) -> None:
    """Events are notifications. Redacted or not, values stay in the queue."""
    from jarvis.core.events.types import ApprovalRequested

    seen: list[ApprovalRequested] = []
    events.subscribe(ApprovalRequested, seen.append)
    queue.request_approval(make_request())
    assert not hasattr(seen[0], "parameters")


# -- helpers ----------------------------------------------------------------
def _wait_for_pending(queue: ApprovalQueue, count: int = 1, timeout: float = 2.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if len(queue.pending()) >= count:
            return
        time.sleep(0.005)
    raise AssertionError(f"expected {count} pending approval(s), saw {len(queue.pending())}")
