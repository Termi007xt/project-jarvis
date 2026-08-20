"""Reopening the browser, reopening the tab, and staying on one thread.

Every test here is named after something that happened on 2026-08-05 and is
recorded in `logs/audit.jsonl`. The session is worth reading as one story,
because the defects are not independent — the first one *caused* the second:

* 12:35:28 — `app.open(youtube)` launched `brave.exe` with **no** debugging
  port, and reported verified success.
* 12:36:24 — `youtube.search("best monitors")` was approved and then failed with
  *"Brave is already open, and a browser that is already running cannot be given
  an automation port"*. Jarvis told the owner to close a browser **it had opened
  itself fifty-six seconds earlier**, and had no way to close it.
* 12:38:30 — after the owner quit Brave by hand, the identical request worked
  and read back 20 results.
* 12:42:51 — `youtube.search("latest anime")` failed with
  `Page.goto: Target page, context or browser has been closed`. The browser was
  alive; the *tab* was not, and nothing looked at the tab.

The owner's summary of what this should have been is the specification these
tests encode: *"if browser close, open and perform task, in new tab. same tab
task perform. or if its open, just open a new tab."*
"""

from __future__ import annotations

import threading

import pytest

from jarvis.core.tools.contract import ToolFailure
from jarvis.toolbox.browser import (
    BraveCdpSession,
    BrowserNeedsRestart,
    BrowserUnavailable,
    quit_browser,
)
from jarvis.toolbox.launch import ApplicationEntry, LaunchKind
from jarvis.toolbox.phase2_tools import BrowserWorkspace

BRAVE_ENTRY = ApplicationEntry(
    app_id="brave",
    display_name="Brave",
    kind=LaunchKind.EXECUTABLE,
    target=r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
    verify_process_names=("brave.exe",),
)


# =========================================================================
# "Brave is already running" must be a *recoverable* state, not a dead end
# =========================================================================
def test_a_running_brave_without_a_port_asks_for_a_restart_by_name() -> None:
    """The dead end, given a way out.

    The refusal itself is correct and stays: `--remote-debugging-port` is a
    startup flag and no amount of retrying will make a running Brave grow one.
    What was wrong is that the only exit was the owner alt-tabbing to Brave and
    quitting it by hand, three times in four minutes, on a browser Jarvis had
    opened itself.

    So the failure gets its own type, distinguishable from every other reason a
    browser might be unavailable, because the whole point is that this one has a
    known and automatable remedy and the others do not.
    """
    session = BraveCdpSession(
        BRAVE_ENTRY, already_running=lambda: True, launcher=lambda _argv: None
    )

    with pytest.raises(BrowserNeedsRestart) as raised:
        session.__enter__()

    assert isinstance(raised.value, BrowserUnavailable), (
        "callers that only know the general failure must keep working"
    )
    message = str(raised.value)
    assert "browser.restart" in message, (
        "the message must name the tool that fixes it. A planner cannot act on "
        f"advice addressed to a human, and this one is: {message}"
    )


def test_the_search_tool_reports_a_restart_as_its_own_failure_code() -> None:
    """`browser_unavailable` and `browser_restart_required` are different facts.

    Collapsing them is what produced *"I need you to manually quit Brave once
    from your taskbar"* — the model had a failure it could not distinguish from
    a broken install, so it improvised instructions for a human.
    """
    workspace = BrowserWorkspace(
        session_factory=_raising(BrowserNeedsRestart("close and reopen: browser.restart"))
    )

    with pytest.raises(ToolFailure) as raised:
        workspace.adapter

    assert raised.value.code == "browser_restart_required", (
        f"got '{raised.value.code}', which is indistinguishable from a browser "
        "that cannot work at all"
    )


def test_any_other_browser_failure_is_still_browser_unavailable() -> None:
    """The control: only the restartable case gets the restartable code."""
    workspace = BrowserWorkspace(
        session_factory=_raising(BrowserUnavailable("Playwright is not installed"))
    )

    with pytest.raises(ToolFailure) as raised:
        workspace.adapter

    assert raised.value.code == "browser_unavailable"


# =========================================================================
# Quitting Brave gracefully, so the tabs come back
# =========================================================================
def test_quitting_asks_the_windows_to_close_and_waits_for_the_process() -> None:
    """Graceful, never forced.

    Jarvis promised the owner *"it will reopen with your tabs restored"* four
    times. Terminating the process would break that promise precisely when it
    was made: Chromium restores a session it was asked to close, and shows
    "Brave didn't shut down correctly" for one that was killed.
    """
    closed: list[int] = []
    alive = [True, True, False]

    quit = quit_browser(
        ("brave.exe",),
        windows_for=lambda _names: [101, 102],
        close_window=closed.append,
        still_running=lambda _names: alive.pop(0),
        sleep=lambda _seconds: None,
        timeout_seconds=5.0,
    )

    assert quit is True
    assert closed == [101, 102], "every window must be asked to close, not just the first"


def test_a_browser_that_will_not_quit_is_reported_rather_than_forced() -> None:
    """A page holding an "unsaved changes" prompt is the owner's to answer.

    Escalating to a forced kill here would discard their work to satisfy a
    search. Reporting the truth costs one sentence.
    """
    quit = quit_browser(
        ("brave.exe",),
        windows_for=lambda _names: [101],
        close_window=lambda _hwnd: None,
        still_running=lambda _names: True,
        sleep=lambda _seconds: None,
        timeout_seconds=0.5,
    )

    assert quit is False, "reported a clean quit for a browser that is still running"


def test_quitting_a_browser_that_is_not_running_succeeds_immediately() -> None:
    """Idempotent: the owner may already have closed it, as they did at 12:38."""
    assert (
        quit_browser(
            ("brave.exe",),
            windows_for=lambda _names: [],
            close_window=lambda _hwnd: None,
            still_running=lambda _names: False,
            sleep=lambda _seconds: None,
        )
        is True
    )


# =========================================================================
# The tab the owner closed
# =========================================================================
class FakePage:
    """A Playwright page that can be closed out from under us, as tabs are."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.closed = False
        self.visited: list[str] = []
        self.emulated: list[object] = []

    def is_closed(self) -> bool:
        return self.closed

    def goto(self, url: str, **_kwargs) -> None:
        if self.closed:
            raise RuntimeError("Target page, context or browser has been closed")
        self.visited.append(url)

    def emulate_media(self, **kwargs) -> None:
        self.emulated.append(kwargs)


def test_a_closed_tab_is_replaced_instead_of_being_driven() -> None:
    """12:42:51, in the words the audit log recorded it.

    `is_alive()` asked whether the *browser* was connected, and it was — Brave
    was running perfectly well. The dead thing was the single tab the driver had
    cached at open time, and nothing ever looked at it, so every later request
    navigated a page that no longer existed.

    Closing a tab is the most ordinary thing a person does in a browser. It must
    cost a new tab, not the rest of the session.
    """
    from jarvis.toolbox.browser import PlaywrightPageDriver

    pages = [FakePage("first"), FakePage("second")]
    live = pages[0]
    driver = PlaywrightPageDriver(live, new_page=lambda: pages[1])

    pages[0].closed = True  # the owner closes the tab
    driver.goto("https://www.youtube.com/results?search_query=latest+anime", 5.0)

    assert pages[1].visited == [
        "https://www.youtube.com/results?search_query=latest+anime"
    ], "the search was run against the tab the owner had already closed"


def test_a_live_tab_is_reused_rather_than_piling_up_new_ones() -> None:
    """The other half, and the reason `page()` was made sticky in the first place.

    "Play the second video" has to land on the page the search just read. A
    driver that healed by always opening a tab would reintroduce exactly the
    defect the stickiness fixed.
    """
    from jarvis.toolbox.browser import PlaywrightPageDriver

    first, spare = FakePage("first"), FakePage("spare")
    driver = PlaywrightPageDriver(first, new_page=lambda: spare)

    driver.goto("https://www.youtube.com/results?search_query=a", 5.0)
    driver.goto("https://www.youtube.com/results?search_query=b", 5.0)

    assert len(first.visited) == 2
    assert spare.visited == [], "opened a second tab while the first was perfectly alive"


def test_a_new_tab_does_not_get_playwrights_light_theme() -> None:
    """The searched tab came back light while every other tab was dark.

    Playwright emulates `prefers-color-scheme: light` on pages it creates, so
    the one tab Jarvis opened looked like someone else's browser. Small, and
    exactly the kind of detail that makes automation feel like a foreign process
    rather than the owner's own session (ADR-0019 chose their real profile so
    that it would not).
    """
    from jarvis.toolbox.browser import PlaywrightPageDriver

    page = FakePage("first")
    PlaywrightPageDriver(page)

    assert page.emulated, "the page kept Playwright's emulated colour scheme"
    assert page.emulated[0].get("color_scheme") == "null", (
        "colour-scheme emulation must be switched off, not set to a fixed theme"
    )


# =========================================================================
# One thread, because Playwright's sync API is bound to the one that made it
# =========================================================================
def test_every_browser_call_runs_on_the_same_owned_thread() -> None:
    """`greenlet.error: Cannot switch to a different thread`, before it bites.

    `ToolInvoker` runs tools on a four-worker pool and abandons the *future*, not
    the thread, when a tool times out. The 12:05 timeout left worker 0 busy, so
    the next call had to start worker 1 — and Playwright's sync API raises the
    moment it is touched from a thread other than the one that created it. Every
    shutdown in `app.log` already logs that error from `MainThread`.

    So the workspace owns a single thread and every browser touch goes through
    it, whichever pool worker happens to be asking.
    """
    workspace = BrowserWorkspace(session_factory=lambda: _FakeSession())
    seen: list[int] = []

    def ask() -> None:
        seen.append(workspace.call(threading.get_ident))

    callers = [threading.Thread(target=ask) for _ in range(3)]
    for caller in callers:
        caller.start()
    for caller in callers:
        caller.join()

    assert len(set(seen)) == 1, (
        f"browser work ran on {len(set(seen))} different threads; Playwright's "
        "sync API raises greenlet.error the first time that happens"
    )
    assert seen[0] != threading.get_ident(), "the browser thread must be its own"


def test_opening_and_closing_also_run_on_the_browser_thread() -> None:
    """Teardown is where this actually broke, every single run.

    `app.log` ends every session with `greenlet.error` from `MainThread`,
    because the session was created on a tool worker and closed from the GUI
    thread. The port was left open on a browser holding live logins — the exact
    residual risk ADR-0031 bounds by making teardown a control.
    """
    threads: list[int] = []
    workspace = BrowserWorkspace(
        session_factory=lambda: _FakeSession(on_enter=lambda: threads.append(threading.get_ident()))
    )

    workspace.adapter
    workspace.close()

    assert len(threads) == 1
    assert threads[0] != threading.get_ident(), "the session was opened on the caller's thread"


# =========================================================================
# The tool that keeps the promise Jarvis kept making
# =========================================================================
def test_restarting_closes_the_browser_and_brings_it_back() -> None:
    """*"Closing Brave briefly then reopening will restore your tabs"* — 12:36:24.

    Jarvis said that, or a variant of it, four times on 2026-08-05 and could do
    none of it. The order matters and is asserted: our own connection is dropped
    *before* the browser is closed, because closing Brave underneath a live
    Playwright connection leaves the workspace holding a session whose every
    call raises — which is the exact state this tool exists to leave behind.
    """
    from jarvis.toolbox.phase2_tools import BrowserRestartTool

    order: list[str] = []

    class Session(_FakeSession):
        def __exit__(self, *_exc):
            order.append("detached")
            return super().__exit__()

    workspace = BrowserWorkspace(session_factory=Session)
    workspace.adapter  # a browser is open before the restart

    tool = BrowserRestartTool(
        workspace, quit_fn=lambda _names: order.append("quit") or True
    )
    execution = tool.run(_context(), tool.spec.input_model(reason="search YouTube"))

    assert order == ["detached", "quit"], (
        f"the browser was closed while still attached, or not at all: {order}"
    )
    assert execution.output.closed and execution.output.reopened
    assert execution.verification.value == "verified"
    assert workspace.is_open, "the browser did not come back"


def test_a_browser_that_refuses_to_close_is_a_failure_not_a_kill() -> None:
    """An "unsaved changes" prompt belongs to the owner, not to a search."""
    from jarvis.toolbox.phase2_tools import BrowserRestartTool

    tool = BrowserRestartTool(
        BrowserWorkspace(session_factory=_FakeSession), quit_fn=lambda _names: False
    )

    with pytest.raises(ToolFailure) as raised:
        tool.run(_context(), tool.spec.input_model(reason="search YouTube"))

    assert raised.value.code == "close_refused"
    assert raised.value.code in tool.spec.failure_codes, (
        "an undeclared failure code is rejected by the invoker before the "
        "message ever reaches the user"
    )


def test_the_restart_tool_says_not_to_ask_the_user_to_close_the_browser() -> None:
    """The description is the fix for what the model actually did.

    Given only "the browser is unavailable", it wrote *"I need you to manually
    quit Brave once from your taskbar or system tray (right-click -> Quit)"*.
    The tool's description is the one place that instruction can be pre-empted,
    because it is what the planner reads when it is choosing.
    """
    from jarvis.toolbox.phase2_tools import BrowserRestartTool

    description = BrowserRestartTool.spec.description.lower()
    assert "browser_restart_required" in description, (
        "the description must name the failure code it answers"
    )
    assert "never tell the user to close the browser" in description


# =========================================================================
# helpers
# =========================================================================
def _context():
    from jarvis.core.tools.contract import ToolContext

    return ToolContext(invocation_id="test-invocation")



def _raising(exc: Exception):
    def factory():
        raise exc

    return factory


class _FakeSession:
    def __init__(self, on_enter=None) -> None:
        self._on_enter = on_enter
        self.entered = False
        self.exited = False

    def __enter__(self):
        if self._on_enter is not None:
            self._on_enter()
        self.entered = True
        return self

    def __exit__(self, *_exc):
        self.exited = True

    def is_alive(self) -> bool:
        return self.entered and not self.exited

    def page(self):
        return object()
