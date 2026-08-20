"""AT-003 — "Jarvis, open Sea of Thieves" launches it and verifies it.

> When the user says "Jarvis, open Sea of Thieves," the configured game
> launches and Jarvis verifies its process or window.

Run against a fake process probe, so no real game is needed. The two halves
that matter are asserted separately: that the *right vector* is built, and that
a launch which cannot be confirmed is reported as **unverified** rather than as
success (PRD FR-048, AT-018).
"""

from __future__ import annotations

import pytest

from jarvis.core.permissions.models import Decision, GrantScope
from jarvis.core.tools.contract import ToolOutcome, Verification
from jarvis.core.tools.invoker import ToolCall, ToolInvoker
from jarvis.core.tools.ports import AutoApprovalPort
from jarvis.toolbox import launch as launch_module
from jarvis.toolbox.launch import default_catalogue
from jarvis.toolbox.phase1_tools import OpenApplicationTool, OpenUrlTool


@pytest.fixture
def catalogue():
    return default_catalogue()


@pytest.fixture
def launching_invoker(registry, permissions, audit, locks, events, database):
    for capability in ("app.open_approved", "web.open_approved_url"):
        permissions.grant(capability, Decision.ALLOW, GrantScope.ALWAYS, created_by="test")
    invoker = ToolInvoker(
        registry, permissions, audit, locks=locks, approvals=AutoApprovalPort(),
        event_bus=events, database=database,
    )
    yield invoker
    invoker.shutdown(wait=False)


@pytest.fixture
def recorded_launches(monkeypatch):
    """Capture argv instead of starting anything, and control verification."""
    calls: list[tuple[str, ...]] = []
    state = {"running": True}
    launched = {"yet": False}

    def fake_launch_argv(argv):
        calls.append(tuple(argv))
        launched["yet"] = True
        return 4242

    def fake_process_running(_names):
        # Nothing is running *before* the launch. That is what makes the
        # observation afterwards evidence rather than coincidence.
        #
        # This fixture previously reported the process as running from the
        # start, which modelled a machine where the application was already
        # open — and under that model a launch "verified" itself by observing
        # something it had not caused. That is the defect behind "Open YouTube
        # Music opens a tab" still recording succeeded/verified.
        if not launched["yet"]:
            return False
        return state["running"]

    monkeypatch.setattr(launch_module, "launch_argv", fake_launch_argv)
    monkeypatch.setattr(launch_module, "process_running", fake_process_running)
    return calls, state


# -- AT-003 proper ---------------------------------------------------------
def test_asking_for_sea_of_thieves_launches_and_verifies_it(
    registry, launching_invoker, catalogue, recorded_launches
) -> None:
    calls, _state = recorded_launches
    registry.register(OpenApplicationTool(catalogue))

    result = launching_invoker.invoke(
        ToolCall(
            tool_id="app.open",
            parameters={"application": "Sea of Thieves"},
            initiating_utterance="Jarvis, open Sea of Thieves",
        )
    )

    assert result.outcome is ToolOutcome.SUCCEEDED
    assert result.verification is Verification.VERIFIED
    assert result.output["verified"] is True

    # The vector: the fixed broker plus the catalogue's AUMID, nothing else.
    assert len(calls) == 1
    assert calls[0][0] == "explorer.exe"
    assert "Microsoft.SeaofThieves" in calls[0][1]


def test_a_launch_that_cannot_be_confirmed_is_not_reported_as_success(
    registry, launching_invoker, catalogue, recorded_launches
) -> None:
    """AT-018: unverified is a distinct outcome, not a quiet success."""
    _calls, state = recorded_launches
    state["running"] = False
    registry.register(OpenApplicationTool(catalogue))

    result = launching_invoker.invoke(
        ToolCall(tool_id="app.open", parameters={"application": "Sea of Thieves"})
    )

    assert result.verification is Verification.UNVERIFIED
    assert result.output["started"] is True
    assert result.output["verified"] is False
    assert "unverified" in result.message.lower()


def test_an_application_outside_the_catalogue_is_refused(
    registry, launching_invoker, catalogue, recorded_launches
) -> None:
    calls, _state = recorded_launches
    registry.register(OpenApplicationTool(catalogue))

    result = launching_invoker.invoke(
        ToolCall(tool_id="app.open", parameters={"application": "cmd.exe"})
    )

    assert result.outcome is ToolOutcome.FAILED
    assert result.failure_code == "unknown_application"
    assert calls == [], "nothing may be launched for an unapproved application"


# -- the rest of PRD section 21's exit criterion ---------------------------
@pytest.mark.parametrize(
    "spoken, expect_in_argv",
    [
        ("Brave", "brave.exe"),
        ("YouTube", "youtube.com"),
        # Deliberately the installed web app rather than a tab: the user
        # installed and pinned it, and "open YouTube Music" means that window.
        ("YouTube Music", "--app-id="),
        ("Xbox", "Microsoft.GamingApp"),
        ("Sea of Thieves", "Microsoft.SeaofThieves"),
    ],
)
def test_each_named_application_builds_the_right_vector(
    registry, launching_invoker, catalogue, recorded_launches, spoken, expect_in_argv
) -> None:
    calls, _state = recorded_launches
    registry.register(OpenApplicationTool(catalogue))

    result = launching_invoker.invoke(
        ToolCall(tool_id="app.open", parameters={"application": spoken})
    )

    assert result.outcome is ToolOutcome.SUCCEEDED, result.message
    assert any(expect_in_argv in part for part in calls[-1])


def test_opening_a_url_uses_the_approved_browser(
    registry, launching_invoker, catalogue, recorded_launches
) -> None:
    calls, _state = recorded_launches
    registry.register(OpenUrlTool(catalogue))

    result = launching_invoker.invoke(
        ToolCall(
            tool_id="web.open_url",
            parameters={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
        )
    )

    assert result.outcome is ToolOutcome.SUCCEEDED
    assert calls[-1][0].endswith("brave.exe")
    assert calls[-1][-1] == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    assert result.output["host"] == "www.youtube.com"


@pytest.mark.parametrize(
    "url", ["file:///C:/Windows/win.ini", "javascript:alert(1)", "steam://run/1"]
)
def test_a_dangerous_url_never_reaches_the_browser(
    registry, launching_invoker, catalogue, recorded_launches, url
) -> None:
    calls, _state = recorded_launches
    registry.register(OpenUrlTool(catalogue))

    result = launching_invoker.invoke(
        ToolCall(tool_id="web.open_url", parameters={"url": url})
    )

    assert result.outcome is ToolOutcome.FAILED
    assert result.failure_code == "refused_url"
    assert calls == []


# -- the pipeline is not bypassed -----------------------------------------
def test_launching_requires_permission_like_anything_else(
    registry, permissions, audit, locks, events, database, catalogue, recorded_launches
) -> None:
    """ADR-0029 constraint 8: no direct path from a plan to Popen."""
    from jarvis.core.tools.ports import DenyingApprovalPort

    calls, _state = recorded_launches
    invoker = ToolInvoker(
        registry, permissions, audit, locks=locks, approvals=DenyingApprovalPort(),
        event_bus=events, database=database,
    )
    registry.register(OpenApplicationTool(catalogue))

    result = invoker.invoke(
        ToolCall(tool_id="app.open", parameters={"application": "Brave"})
    )

    assert result.outcome is ToolOutcome.DENIED
    assert calls == [], "a denied launch must never reach the call site"
    invoker.shutdown(wait=False)


def test_the_launch_is_audited_with_its_argument_vector(
    registry, launching_invoker, catalogue, recorded_launches, audit
) -> None:
    registry.register(OpenApplicationTool(catalogue))
    launching_invoker.invoke(
        ToolCall(tool_id="app.open", parameters={"application": "Brave"})
    )
    summaries = [str(record.get("summary", "")) for record in audit.query(limit=50)]
    assert any("app.open" in summary for summary in summaries)
