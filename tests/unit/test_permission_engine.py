"""Permission evaluation (PRD sections 9.9 and 11.1, ARCHITECTURE.md 6.4)."""

from __future__ import annotations

from datetime import timedelta

import pytest

from jarvis.common import utc_now
from jarvis.core.permissions.catalogue import CAPABILITIES, capabilities_by_risk
from jarvis.core.permissions.engine import DefaultPolicy, PermissionEngine
from jarvis.core.permissions.models import (
    Decision,
    GrantScope,
    PermissionError,
    PermissionRequest,
    RiskLevel,
)

LOW = "system.read_health"
MEDIUM = "fs.read_approved"
HIGH = "fs.delete_or_overwrite"
PROHIBITED = "prohibited.generic_shell"


# -- the evaluation ladder -------------------------------------------------
def test_unknown_capability_is_denied(permissions) -> None:
    result = permissions.evaluate(PermissionRequest(capability_id="nope.not.real"))
    assert result.decision is Decision.DENY


def test_prohibited_is_denied_before_anything_else(permissions) -> None:
    result = permissions.evaluate(PermissionRequest(capability_id=PROHIBITED))
    assert result.decision is Decision.DENY
    assert not result.requires_user_approval


def test_high_risk_always_asks(permissions) -> None:
    """PRD 11.1: fresh confirmation every time."""
    result = permissions.evaluate(PermissionRequest(capability_id=HIGH))
    assert result.decision is Decision.ASK
    assert result.requires_user_approval


def test_medium_risk_asks_by_default(permissions) -> None:
    result = permissions.evaluate(PermissionRequest(capability_id=MEDIUM))
    assert result.decision is Decision.ASK


def test_low_risk_asks_by_default_but_may_be_always_allowed(permissions) -> None:
    assert permissions.evaluate(PermissionRequest(capability_id=LOW)).decision is Decision.ASK
    permissions.grant(LOW, Decision.ALLOW, GrantScope.ALWAYS, created_by="user")
    assert permissions.evaluate(PermissionRequest(capability_id=LOW)).decision is Decision.ALLOW


# -- the high-risk invariant ----------------------------------------------
@pytest.mark.parametrize(
    "scope", [GrantScope.ALWAYS, GrantScope.SESSION, GrantScope.TASK, GrantScope.APPLICATION,
              GrantScope.FOLDER]
)
def test_high_risk_cannot_be_allowed_beyond_a_single_use(permissions, scope) -> None:
    """PRD 9.9: high-risk permissions must not offer 'always allow'."""
    with pytest.raises(PermissionError, match="may only be allowed with scope 'once'"):
        permissions.grant(
            HIGH,
            Decision.ALLOW,
            scope,
            scope_ref="C:/tmp",
            session_id="s1",
            task_id="t1",
            created_by="user",
        )


def test_high_risk_single_use_grant_is_consumed(permissions) -> None:
    permissions.grant(HIGH, Decision.ALLOW, GrantScope.ONCE, created_by="user")
    first = permissions.evaluate(PermissionRequest(capability_id=HIGH))
    assert first.decision is Decision.ALLOW

    second = permissions.evaluate(PermissionRequest(capability_id=HIGH))
    assert second.decision is Decision.ASK, "a single-use approval must not be reusable"


def test_every_high_risk_capability_refuses_a_broad_allow(permissions) -> None:
    for capability in capabilities_by_risk(RiskLevel.HIGH):
        with pytest.raises(PermissionError):
            permissions.grant(
                capability.capability_id, Decision.ALLOW, GrantScope.ALWAYS, created_by="user"
            )


def test_always_allow_is_low_risk_only(permissions) -> None:
    with pytest.raises(PermissionError, match="only available for low-risk"):
        permissions.grant(MEDIUM, Decision.ALLOW, GrantScope.ALWAYS, created_by="user")


def test_medium_risk_cannot_default_to_allow() -> None:
    with pytest.raises(PermissionError, match="cannot default to allow"):
        DefaultPolicy(medium=Decision.ALLOW)


# -- scope matching --------------------------------------------------------
def test_session_scope_matches_only_its_session(permissions) -> None:
    permissions.grant(
        MEDIUM, Decision.ALLOW, GrantScope.SESSION, session_id="session-a", created_by="user"
    )
    same = permissions.evaluate(
        PermissionRequest(capability_id=MEDIUM, session_id="session-a")
    )
    other = permissions.evaluate(
        PermissionRequest(capability_id=MEDIUM, session_id="session-b")
    )
    assert same.decision is Decision.ALLOW
    assert other.decision is Decision.ASK


def test_task_scope_matches_only_its_task(permissions) -> None:
    permissions.grant(
        MEDIUM, Decision.ALLOW, GrantScope.TASK, task_id="task-a", created_by="user"
    )
    assert (
        permissions.evaluate(PermissionRequest(capability_id=MEDIUM, task_id="task-a")).decision
        is Decision.ALLOW
    )
    assert (
        permissions.evaluate(PermissionRequest(capability_id=MEDIUM, task_id="task-b")).decision
        is Decision.ASK
    ), "one task must not inherit another task's grant"


def test_application_scope_matches_only_that_application(permissions) -> None:
    permissions.grant(
        "app.monitor",
        Decision.ALLOW,
        GrantScope.APPLICATION,
        scope_ref="brave",
        created_by="user",
    )
    assert (
        permissions.evaluate(
            PermissionRequest(capability_id="app.monitor", target="brave")
        ).decision
        is Decision.ALLOW
    )
    assert (
        permissions.evaluate(
            PermissionRequest(capability_id="app.monitor", target="notepad")
        ).decision
        is Decision.ASK
    )


def test_folder_scope_covers_children_but_not_siblings(permissions, tmp_path) -> None:
    root = tmp_path / "workspace"
    child = root / "project" / "notes"
    sibling = tmp_path / "elsewhere"
    child.mkdir(parents=True)
    sibling.mkdir()

    permissions.grant(
        MEDIUM, Decision.ALLOW, GrantScope.FOLDER, scope_ref=str(root), created_by="user"
    )
    assert (
        permissions.evaluate(PermissionRequest(capability_id=MEDIUM, target=str(child))).decision
        is Decision.ALLOW
    )
    assert (
        permissions.evaluate(
            PermissionRequest(capability_id=MEDIUM, target=str(sibling))
        ).decision
        is Decision.ASK
    ), "a folder grant must not extend outside its root"


def test_folder_scope_rejects_traversal_out_of_the_root(permissions, tmp_path) -> None:
    root = tmp_path / "workspace"
    root.mkdir()
    (tmp_path / "secrets").mkdir()
    permissions.grant(
        MEDIUM, Decision.ALLOW, GrantScope.FOLDER, scope_ref=str(root), created_by="user"
    )
    escape = str(root / ".." / "secrets")
    assert (
        permissions.evaluate(PermissionRequest(capability_id=MEDIUM, target=escape)).decision
        is Decision.ASK
    )


def test_scopes_requiring_a_reference_are_rejected_without_one(permissions) -> None:
    for scope in (GrantScope.APPLICATION, GrantScope.FOLDER):
        with pytest.raises(PermissionError, match="requires a scope_ref"):
            permissions.grant(MEDIUM, Decision.ALLOW, scope, created_by="user")
    with pytest.raises(PermissionError, match="requires a session_id"):
        permissions.grant(MEDIUM, Decision.ALLOW, GrantScope.SESSION, created_by="user")
    with pytest.raises(PermissionError, match="requires a task_id"):
        permissions.grant(MEDIUM, Decision.ALLOW, GrantScope.TASK, created_by="user")


# -- expiry and revocation -------------------------------------------------
def test_an_expired_grant_does_not_apply(permissions) -> None:
    permissions.grant(
        LOW,
        Decision.ALLOW,
        GrantScope.ALWAYS,
        created_by="user",
        expires_at=utc_now() - timedelta(seconds=1),
    )
    assert permissions.evaluate(PermissionRequest(capability_id=LOW)).decision is Decision.ASK


def test_session_grants_get_a_ttl(database, audit, events) -> None:
    engine = PermissionEngine(
        database, audit, events, policy=DefaultPolicy(session_grant_ttl_seconds=60)
    )
    grant = engine.grant(
        MEDIUM, Decision.ALLOW, GrantScope.SESSION, session_id="s", created_by="user"
    )
    assert grant.expires_at is not None


def test_revoking_a_grant_takes_effect_immediately(permissions) -> None:
    grant = permissions.grant(LOW, Decision.ALLOW, GrantScope.ALWAYS, created_by="user")
    assert permissions.evaluate(PermissionRequest(capability_id=LOW)).decision is Decision.ALLOW

    assert permissions.revoke(grant.grant_id) is True
    assert permissions.evaluate(PermissionRequest(capability_id=LOW)).decision is Decision.ASK


def test_revoking_a_session_revokes_all_its_grants(permissions) -> None:
    permissions.grant(
        MEDIUM, Decision.ALLOW, GrantScope.SESSION, session_id="s1", created_by="user"
    )
    permissions.grant(
        "clipboard.read", Decision.ALLOW, GrantScope.SESSION, session_id="s1", created_by="user"
    )
    assert permissions.revoke_session("s1") == 2
    assert (
        permissions.evaluate(PermissionRequest(capability_id=MEDIUM, session_id="s1")).decision
        is Decision.ASK
    )


def test_a_deny_grant_outranks_an_allow_grant(permissions) -> None:
    permissions.grant(LOW, Decision.ALLOW, GrantScope.ALWAYS, created_by="user")
    permissions.grant(LOW, Decision.DENY, GrantScope.ALWAYS, created_by="user")
    result = permissions.evaluate(PermissionRequest(capability_id=LOW))
    assert result.decision is Decision.DENY


def test_a_deny_grant_suppresses_the_high_risk_prompt(permissions) -> None:
    """A user who denied something should not be asked again in the same scope."""
    permissions.grant(HIGH, Decision.DENY, GrantScope.SESSION, session_id="s", created_by="user")
    result = permissions.evaluate(PermissionRequest(capability_id=HIGH, session_id="s"))
    assert result.decision is Decision.DENY
    assert not result.requires_user_approval


def test_narrower_scope_wins_over_broader(permissions) -> None:
    permissions.grant(LOW, Decision.ALLOW, GrantScope.ALWAYS, created_by="user")
    permissions.grant(
        LOW, Decision.ALLOW, GrantScope.TASK, task_id="t1", created_by="user"
    )
    result = permissions.evaluate(PermissionRequest(capability_id=LOW, task_id="t1"))
    matched = next(g for g in permissions.list_grants(LOW) if g.grant_id == result.matched_grant_id)
    assert matched.scope is GrantScope.TASK


# -- auditing --------------------------------------------------------------
def test_every_evaluation_is_audited(permissions, audit) -> None:
    before = audit.count()
    permissions.evaluate(PermissionRequest(capability_id=HIGH))
    assert audit.count() > before
    latest = audit.read_all()[-1]
    assert latest["capability_id"] == HIGH
    assert latest["permission_decision"] == "ask"


def test_grants_persist_across_engine_instances(database, audit, events) -> None:
    first = PermissionEngine(database, audit, events)
    first.grant(LOW, Decision.ALLOW, GrantScope.ALWAYS, created_by="user")

    second = PermissionEngine(database, audit, events)
    assert second.evaluate(PermissionRequest(capability_id=LOW)).decision is Decision.ALLOW


# -- the catalogue ---------------------------------------------------------
def test_catalogue_ids_are_unique_and_well_formed() -> None:
    assert len(CAPABILITIES) == len({c.capability_id for c in CAPABILITIES.values()})
    for capability_id, capability in CAPABILITIES.items():
        assert capability_id == capability.capability_id
        assert capability.title and capability.description


@pytest.mark.parametrize(
    ("capability_id", "expected"),
    [
        ("app.open_approved", RiskLevel.LOW),
        ("notify.show", RiskLevel.LOW),
        ("media.playback_control", RiskLevel.LOW),
        ("input.automate", RiskLevel.MEDIUM),
        ("screen.capture", RiskLevel.MEDIUM),
        ("clipboard.read", RiskLevel.MEDIUM),
        ("browser.automate_logged_in", RiskLevel.MEDIUM),
        ("fs.delete_or_overwrite", RiskLevel.HIGH),
        ("app.force_close", RiskLevel.HIGH),
        ("messages.send_or_delete", RiskLevel.HIGH),
        ("system.elevate", RiskLevel.HIGH),
        ("prohibited.generic_shell", RiskLevel.PROHIBITED),
    ],
)
def test_risk_classification_matches_the_prd(capability_id: str, expected: RiskLevel) -> None:
    assert CAPABILITIES[capability_id].risk is expected
