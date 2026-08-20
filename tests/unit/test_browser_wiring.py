"""The browser tools are connected to something, or say why they are not.

Phase 1's six acceptance rounds all found the same class of defect: components
that worked perfectly while connected to nothing.
`tests/ui/test_conversation_screen.py` passed in full against a screen that was
entirely non-functional, because every test exercised the unit and nothing
exercised the seam.

`youtube.search` is the Phase 2 shape of that risk. It can be registered,
enabled, and offered to the planner while its workspace has no way to ever open
a browser — answering "there is no browser session" forever. That reads as a
working feature to every unit test and as a dead end to the user.

So this asserts the wiring, not the behaviour: the registered tool reaches a
workspace that can open a session, and where it genuinely cannot, the reason it
gives is a *reason* rather than a permanent state.
"""

from __future__ import annotations

import pytest

from jarvis.core.tools.contract import ToolContext, ToolFailure
from jarvis.toolbox.phase2_tools import (
    BrowserWorkspace,
    YouTubeSearchInput,
    YouTubeSearchTool,
)


def test_the_core_registers_the_browser_tools(core) -> None:
    """Registered at all — the first thing that was wrong in Phase 1."""
    assert {"youtube.search", "youtube.play"} <= set(core.registry.tool_ids())


def test_the_core_gives_the_workspace_a_way_to_open_a_browser(core) -> None:
    """The seam itself.

    Without a session factory the tools are permanently inert, and no unit test
    of either tool would notice — both would pass against a workspace that can
    never do anything.
    """
    assert core.browser_workspace._session_factory is not None, (
        "youtube.search is registered but its workspace can never open a "
        "browser, so the tool is offered and can never work"
    )


def test_a_workspace_with_no_factory_says_so_rather_than_pretending() -> None:
    """The honest end of the same seam (ADR-0010)."""
    tool = YouTubeSearchTool(BrowserWorkspace())

    with pytest.raises(ToolFailure) as raised:
        tool.run(ToolContext(), YouTubeSearchInput(query="anything"))

    assert raised.value.code == "no_browser_session"
    assert raised.value.code in YouTubeSearchTool.spec.failure_codes


def test_a_browser_that_will_not_open_is_a_declared_failure() -> None:
    """Not a crash, and not a silent empty result list."""

    def refuses():
        raise OSError("Brave is not installed")

    tool = YouTubeSearchTool(BrowserWorkspace(session_factory=refuses))

    with pytest.raises(ToolFailure) as raised:
        tool.run(ToolContext(), YouTubeSearchInput(query="anything"))

    assert raised.value.code == "browser_unavailable"
    assert "Brave is not installed" in str(raised.value), (
        "pass the underlying cause through rather than replacing it"
    )


def test_closing_the_workspace_closes_the_session() -> None:
    """A browser left attached is one left listening on a debugging port."""
    closed: list[bool] = []

    class FakeSession:
        def __enter__(self):
            return self

        def __exit__(self, *_exc):
            closed.append(True)

        def page(self):
            return object()

    workspace = BrowserWorkspace(session_factory=FakeSession)
    workspace.adapter  # opens it
    assert workspace.is_open

    workspace.close()
    assert closed == [True]
    assert not workspace.is_open


def test_closing_twice_is_safe() -> None:
    """Shutdown paths run more than once; this must not raise on the second."""
    workspace = BrowserWorkspace()
    workspace.close()
    workspace.close()


# -- recovering from a browser the user closed ----------------------------
class DyingSession:
    """A session whose page dies, as Playwright's does when Brave is closed."""

    opened = 0

    def __init__(self) -> None:
        type(self).opened += 1
        self.generation = type(self).opened
        self.alive = True

    def __enter__(self):
        return self

    def __exit__(self, *_exc):
        self.alive = False

    def is_alive(self) -> bool:
        return self.alive

    def page(self):
        return self

    # The page driver surface the workspace hands to the adapter.
    def content(self) -> str:
        self._check()
        return "<div>ok</div>"

    def goto(self, url, timeout_seconds):
        self._check()

    def results(self, timeout_seconds):
        self._check()
        return [{"title": "a video", "video_id": "vid1"}]

    def click_result(self, position, timeout_seconds):
        self._check()

    def player_state(self, timeout_seconds):
        self._check()
        return {"playing": True, "video_id": "vid1"}

    def _check(self) -> None:
        if not self.alive:
            raise RuntimeError("Target page, context or browser has been closed")


def test_a_browser_the_user_closed_is_reopened_rather_than_failing_forever() -> None:
    """The defect from real use, reported 2026-08-04.

    Closing Brave left the workspace holding a dead page, and *every* later
    request failed with "Target page, context or browser has been closed" until
    Jarvis itself was restarted. The user closing their browser is completely
    ordinary, so a session that cannot survive it is not usable.
    """
    DyingSession.opened = 0
    workspace = BrowserWorkspace(session_factory=DyingSession)

    first = workspace.adapter
    first.search("anything")
    assert DyingSession.opened == 1

    # The user closes Brave.
    workspace._session.alive = False  # type: ignore[union-attr]

    second = workspace.adapter
    second.search("anything again")
    assert DyingSession.opened == 2, "a dead session must be replaced, not reused"


def test_a_dead_session_is_detected_before_it_is_handed_out() -> None:
    DyingSession.opened = 0
    workspace = BrowserWorkspace(session_factory=DyingSession)
    workspace.adapter
    workspace._session.alive = False  # type: ignore[union-attr]

    assert workspace.is_open is False, (
        "a session whose browser has gone must not still report as open"
    )


def test_shutting_down_the_core_closes_the_browser(core) -> None:
    """The shutdown path must actually reach the workspace."""
    closed: list[bool] = []

    class FakeSession:
        def __enter__(self):
            return self

        def __exit__(self, *_exc):
            closed.append(True)

        def page(self):
            return object()

    core.browser_workspace._session_factory = FakeSession
    core.browser_workspace.adapter  # open one
    core.shutdown("test")

    assert closed == [True], "shutdown left the browser attached"
