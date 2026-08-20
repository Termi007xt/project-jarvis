"""An approval the owner gave must survive to the next sentence.

From `logs/audit.jsonl`, 2026-08-05, four times in seven minutes:

    07:06:24 security   approval scope 'task' rejected for browser.automate_logged_in
             error: scope 'task' requires a task_id
    07:06:24 permission approval allow for browser.automate_logged_in

The owner chose **Allow for this task**. The dialog offered it, the engine threw
it away, and the invocation ran once under a scope nobody had asked for — so the
very next utterance asked again. Four prompts, four identical answers, and the
owner's report of it was simply *"permissions ... are kind of blockers"*.

Two rules come out of that, and both are asserted here:

1. **A scope the dialog offers must be one the engine can honour.** ADR-0010's
   rule for controls — an enabled control either does something or says why it
   cannot — applies to a button in an approval dialog exactly as it applies to a
   menu item.
2. **"Always" is now available for browser automation**, by the owner's explicit
   decision on 2026-08-05 (ADR-0032), because it is offered as a choice they
   make once and can revoke, not as a default that quietly weakens the model.
"""

from __future__ import annotations

import pytest

from jarvis.core.permissions.engine import DefaultPolicy, PermissionEngine  # noqa: F401
from jarvis.core.permissions.models import (
    Decision,
    GrantScope,
    PermissionError,
    PermissionRequest,
    RiskLevel,
)
from jarvis.core.tools.ports import offerable_scopes_for

BROWSER = "browser.automate_logged_in"
OTHER_MEDIUM = "fs.read_approved"


# =========================================================================
# The scope the dialog offered and the engine refused
# =========================================================================
def test_every_offered_scope_can_actually_be_granted(permissions) -> None:
    """The rule, asserted directly rather than one scope at a time.

    This is the test that would have caught the defect on the day it shipped:
    it walks what the dialog would show and grants each one, which is precisely
    the sequence the owner performed by hand four times.
    """
    for risk, capability_id in (
        (RiskLevel.LOW, "app.open_approved"),
        (RiskLevel.MEDIUM, OTHER_MEDIUM),
    ):
        for scope in offerable_scopes_for(risk):
            if scope is GrantScope.ONCE:
                continue  # consumed by the invocation; never persisted
            permissions.grant(
                capability_id,
                Decision.ALLOW,
                scope,
                # Exactly what the invoker has available when a conversation —
                # not a scheduled task — is what asked.
                task_id="conversation-turn-1",
                session_id="session-1",
                scope_ref="example.com",
                created_by="user",
            )


def test_a_conversation_turn_carries_a_task_id(invoker, registry, permissions) -> None:
    """"For this task" has to mean something when the task is a spoken request.

    `ToolCall.task_id` was only ever set by the scheduler, so every approval
    that came from talking to Jarvis had `task_id=None` and every "for this
    task" was discarded. A spoken request that needs three tools is a task in
    every sense the owner cares about.
    """
    from jarvis.llm.conversation import ConversationEngine

    engine = ConversationEngine(
        provider=_NullProvider(), invoker=invoker, registry=registry, session_id="s1"
    )
    first = engine.new_task_id()
    second = engine.new_task_id()

    assert first and second, "a conversation turn must be able to identify itself"
    assert first != second, (
        "every turn reused one id, so 'for this task' would silently become "
        "'forever' — the opposite failure, and a worse one"
    )


# =========================================================================
# Always-allow for browser automation (ADR-0032)
# =========================================================================
def test_browser_automation_may_be_granted_always(database, audit, events) -> None:
    """The owner's decision, 2026-08-05: one approval, not one per sentence.

    Deliberately *offered*, never defaulted. It appears in the dialog, it is
    written as an ordinary grant, it shows on the Permissions screen and it can
    be revoked there. What it is not is a policy that quietly stops asking —
    note that it still evaluates to ASK until the owner has actually chosen it.

    The engine is built here with the policy rather than taken from the bare
    fixture, because that is where the decision lives: `config/defaults.yaml`
    names the capability, and the code default names nothing.
    """
    permissions = PermissionEngine(
        database,
        audit,
        events,
        policy=DefaultPolicy(always_allowable_capabilities=(BROWSER,)),
    )
    assert permissions.evaluate(PermissionRequest(capability_id=BROWSER)).decision is Decision.ASK

    permissions.grant(BROWSER, Decision.ALLOW, GrantScope.ALWAYS, created_by="user")

    later = permissions.evaluate(
        PermissionRequest(capability_id=BROWSER, target="something else entirely")
    )
    assert later.decision is Decision.ALLOW, (
        "the standing grant did not apply to the next request, which is the "
        "whole thing it was granted for"
    )


def test_the_shipped_configuration_is_what_names_it() -> None:
    """The owner's decision, read back from the file that records it.

    Asserted against the loaded configuration rather than restated as a
    constant, so deleting the line from `defaults.yaml` fails this test instead
    of quietly reverting the behaviour it documents.
    """
    import yaml

    from jarvis.config.paths import find_defaults_config

    shipped = yaml.safe_load(find_defaults_config().read_text(encoding="utf-8"))
    assert BROWSER in shipped["permissions"]["always_allowable_capabilities"]


def test_the_dialog_offers_always_for_browser_automation() -> None:
    """A grant the owner can never reach is a grant they do not have."""
    scopes = offerable_scopes_for(RiskLevel.MEDIUM, always_allowable=True)
    assert GrantScope.ALWAYS in scopes
    assert GrantScope.ONCE in scopes, "single use must never stop being available"


def test_other_medium_capabilities_are_not_widened(permissions) -> None:
    """The blast radius, held to one capability.

    PRD 11.1 puts medium risk at "ask every time, per task, per app or per
    folder". ADR-0032 makes one named exception for one capability the owner
    uses constantly; it does not reopen the class.
    """
    assert GrantScope.ALWAYS not in offerable_scopes_for(RiskLevel.MEDIUM)

    with pytest.raises(PermissionError) as raised:
        permissions.grant(OTHER_MEDIUM, Decision.ALLOW, GrantScope.ALWAYS, created_by="user")
    assert "always" in str(raised.value).lower()


def test_high_risk_still_cannot_be_granted_always(permissions) -> None:
    """PRD 9.9 and 11.1, untouched. Not a UX preference, and not negotiable."""
    with pytest.raises(PermissionError):
        permissions.grant(
            "fs.delete_or_overwrite", Decision.ALLOW, GrantScope.ALWAYS, created_by="user"
        )


def test_the_exception_is_configuration_the_owner_can_withdraw(database, audit, events) -> None:
    """Whoever turned it on can turn it off, and the default stays conservative.

    The code default is an empty list: a fresh install has PRD 11.1's posture
    exactly. `config/defaults.yaml` records this machine's owner decision, which
    keeps the choice visible and revertible rather than compiled in.
    """
    strict = PermissionEngine(
        database, audit, events, policy=DefaultPolicy(always_allowable_capabilities=())
    )
    with pytest.raises(PermissionError):
        strict.grant(BROWSER, Decision.ALLOW, GrantScope.ALWAYS, created_by="user")


class _NullProvider:
    available = True

    def unavailable_reason(self):
        return None

    def complete(self, messages, tools=()):  # pragma: no cover - never reached
        raise AssertionError("this test never runs a turn")
