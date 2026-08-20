"""Every browser touch happens on the browser's own thread.

Playwright's synchronous API is bound to the thread that created it. Driving it
from another thread does not raise something legible — it raises
`greenlet.error: Cannot switch to a different thread` from an asyncio callback,
usually long after the call that caused it, and the page ends up closed.

That is what happened on 2026-08-05 at 13:55:59. `BrowserWorkspace` already
owned a single thread and already routed `_open()` through it — the browser was
launched and attached on `jarvis-browser_0`, exactly as designed. But the
`adapter` property *returned* the adapter to the caller, and the tools then
called `adapter.search(...)` on the invoker's own worker. So the session was
built on one thread and driven from another:

    Page.goto: Target page, context or browser has been closed
      - navigating to "youtube.com/results?search_query=best+gaming+monitors"

The visible result was a browser that opened a blank tab and never searched.

This is the Phase 1 defect class once more: the mechanism was correct, tested,
and documented, and nothing asserted that the callers actually went through it.
Unit tests of the workspace passed, unit tests of the tools passed, and the two
were connected by an assumption. So these tests assert the *seam* — which
thread the work really happens on — rather than the mechanism in isolation.
"""

from __future__ import annotations

import threading

import pytest

from jarvis.core.tools.contract import ToolContext
from jarvis.toolbox.browser import BrowserThreadViolation, PlaywrightPageDriver
from jarvis.toolbox.phase2_tools import (
    BrowserWorkspace,
    YouTubePlayInput,
    YouTubePlayTool,
    YouTubeSearchInput,
    YouTubeSearchTool,
)


class RecordingItem:
    def __init__(self, label: str) -> None:
        self.label = label


class RecordingResults:
    origin = "https://www.youtube.com/results?search_query=x"

    def __init__(self) -> None:
        self.items = [RecordingItem("first"), RecordingItem("second")]

    def __len__(self) -> int:
        return len(self.items)


class RecordingReport:
    position = 1
    title = "second"
    video_id = "vid2"
    expected_video_id = "vid2"
    clicked = True
    verified = True
    detail = "playing"


class RecordingAdapter:
    """An adapter that remembers which thread each call arrived on."""

    def __init__(self, threads: list[int]) -> None:
        self._threads = threads

    def search(self, _query: str) -> RecordingResults:
        self._threads.append(threading.get_ident())
        return RecordingResults()

    def play(self, _position: int) -> RecordingReport:
        self._threads.append(threading.get_ident())
        return RecordingReport()


def _workspace_with(threads: list[int]) -> BrowserWorkspace:
    """A workspace whose session opens instantly and records nothing."""
    adapter = RecordingAdapter(threads)

    class FakeSession:
        def __enter__(self):
            return self

        def __exit__(self, *_exc):
            return None

        def is_alive(self) -> bool:
            return True

        def page(self):
            return object()

    workspace = BrowserWorkspace(session_factory=FakeSession)
    workspace.set_adapter(adapter)
    return workspace


def test_the_search_tool_drives_the_browser_on_the_workspace_thread() -> None:
    """The seam. Acquiring the adapter on the right thread is not enough."""
    threads: list[int] = []
    workspace = _workspace_with(threads)
    tool = YouTubeSearchTool(workspace)

    tool.run(ToolContext(), YouTubeSearchInput(query="best gaming monitors"))

    assert threads, "the adapter was never called"
    assert threads[0] != threading.get_ident(), (
        "youtube.search drove the browser on the caller's thread. Playwright is "
        "bound to the thread that created the session, so this is the "
        "greenlet.error that left a blank tab on 2026-08-05"
    )
    assert threads[0] == workspace._browser_thread_id


def test_the_play_tool_drives_the_browser_on_the_workspace_thread() -> None:
    threads: list[int] = []
    workspace = _workspace_with(threads)
    tool = YouTubePlayTool(workspace)

    tool.run(ToolContext(), YouTubePlayInput(position=1))

    assert threads, "the adapter was never called"
    assert threads[0] != threading.get_ident()
    assert threads[0] == workspace._browser_thread_id


def test_search_then_play_share_one_thread() -> None:
    """Two utterances, one browser thread — "play the second video" included."""
    threads: list[int] = []
    workspace = _workspace_with(threads)

    YouTubeSearchTool(workspace).run(ToolContext(), YouTubeSearchInput(query="x"))
    YouTubePlayTool(workspace).run(ToolContext(), YouTubePlayInput(position=1))

    assert len(threads) == 2
    assert threads[0] == threads[1], (
        "the second utterance ran on a different thread from the first; "
        "Playwright objects created by the search cannot be used by the play"
    )


# =========================================================================
# The page driver defends its own binding
# =========================================================================
class FakePage:
    def goto(self, *_args, **_kwargs) -> None:
        return None

    def content(self) -> str:
        return "<html></html>"


def test_a_page_driver_refuses_to_be_driven_from_another_thread() -> None:
    """Legible failure instead of a greenlet error from an asyncio callback.

    Routing the callers correctly is the fix; this is what stops the next
    caller re-introducing it silently. The object that is thread-bound is the
    one that knows its binding, so it is the one that enforces it.
    """
    driver = PlaywrightPageDriver(FakePage())
    failures: list[BaseException] = []

    def drive_from_elsewhere() -> None:
        try:
            driver.content()
        except BaseException as exc:  # noqa: BLE001 - the point of the test
            failures.append(exc)

    other = threading.Thread(target=drive_from_elsewhere)
    other.start()
    other.join()

    assert failures, "a page driven from the wrong thread reported no problem"
    assert isinstance(failures[0], BrowserThreadViolation)
    assert "thread" in str(failures[0]).lower()


def test_a_page_driver_works_on_its_own_thread() -> None:
    """The control: the guard must not break the path that is correct."""
    driver = PlaywrightPageDriver(FakePage())
    assert driver.content() == "<html></html>"


def test_the_guard_survives_being_handed_to_the_workspace_thread() -> None:
    """A driver created *on* the browser thread is usable there, and only there."""
    workspace = BrowserWorkspace()
    driver = workspace.call(lambda: PlaywrightPageDriver(FakePage()))

    assert workspace.call(driver.content) == "<html></html>"

    with pytest.raises(BrowserThreadViolation):
        driver.content()  # the test's own thread, which is not the owner
