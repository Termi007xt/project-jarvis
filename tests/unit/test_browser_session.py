"""Opening the browser session: fail fast, say why, and never leak a port.

All three cases here come from one real run — 2026-08-05, recorded in
`logs/app.log` and `logs/audit.jsonl` — in which "open YouTube and search best
microphones" opened YouTube, never searched, and had to be fixed by restarting
Jarvis.

The audit log timed it precisely: `youtube.search` was invoked at 06:33:47.593Z,
`launch_argv` ran 67ms later, the invoker abandoned the call at 06:35:17.595Z
after exactly 90.0s, and the browser reported itself attached at 06:35:23.712Z —
six seconds *after* Jarvis had already shut down and released its locks.

Two separate defects sit in that sequence, and each is asserted below.
"""

from __future__ import annotations

import time

import pytest

from jarvis.toolbox.browser import (
    BraveCdpSession,
    BrowserUnavailable,
    brave_user_data_dir,
    existing_debug_port,
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
# Defect 1: a browser that is already running can never open a debug port
# =========================================================================
def test_an_already_running_brave_fails_immediately_and_says_what_to_do() -> None:
    """`--remote-debugging-port` is a *startup* flag, and this is now the norm.

    When Brave is already running, a second `brave.exe --remote-debugging-port=N`
    does not open a port. Chromium's singleton hands the command line to the
    running instance and the new process exits, so the port never appears and
    the wait can only ever end in a timeout.

    Before ADR-0019 Option D this was the rare case: automation drove a
    dedicated profile that was almost never already open, so the launch
    cold-started Brave and the port appeared in well under a second. Pointing
    automation at the owner's own profile inverted that — their browser is
    essentially always running — which is why searching "worked before" and then
    stopped.

    Waiting 20s to discover something knowable in microseconds is the part that
    is wrong. The answer is the same either way; the user should not buy it with
    20 seconds of silence, and the message has to name the fix (ADR-0010).
    """
    started: list[tuple[str, ...]] = []
    session = BraveCdpSession(
        BRAVE_ENTRY,
        already_running=lambda: True,
        launcher=lambda argv: started.append(tuple(argv)),
    )

    began = time.monotonic()
    with pytest.raises(BrowserUnavailable) as raised:
        session.__enter__()
    elapsed = time.monotonic() - began

    assert elapsed < 1.0, (
        f"took {elapsed:.1f}s to report something knowable before launching; "
        "the port wait cannot succeed when Brave is already running"
    )
    assert not started, (
        "launched Brave anyway; the launch cannot help and steals window focus"
    )
    message = str(raised.value)
    assert "already" in message.lower() and "close" in message.lower(), (
        f"the message must name the one thing that fixes it, got: {message}"
    )


def test_a_browser_that_is_not_running_is_launched_normally() -> None:
    """The control: the pre-check must not block the case that works."""
    started: list[tuple[str, ...]] = []
    session = BraveCdpSession(
        BRAVE_ENTRY,
        already_running=lambda: False,
        launcher=lambda argv: started.append(tuple(argv)),
        ready_timeout_seconds=0.01,
    )

    with pytest.raises(BrowserUnavailable):
        session.__enter__()  # no real browser, so the port never appears

    assert len(started) == 1, "a browser that was not running must still be launched"
    assert any("--remote-debugging-port=" in part for part in started[0])


def test_the_debugging_port_never_reaches_the_failure_message() -> None:
    """ADR-0031: the port is a control channel, not diagnostic detail."""
    session = BraveCdpSession(
        BRAVE_ENTRY,
        already_running=lambda: False,
        launcher=lambda _argv: None,
        ready_timeout_seconds=0.01,
    )
    with pytest.raises(BrowserUnavailable) as raised:
        session.__enter__()

    assert session._port is not None
    assert str(session._port) not in str(raised.value)


# =========================================================================
# Re-attaching to a browser Jarvis started earlier
# =========================================================================
def test_a_stale_port_file_is_not_trusted(tmp_path) -> None:
    """`DevToolsActivePort` survives a crash, so it is a hint, not a fact."""
    (tmp_path / "DevToolsActivePort").write_text("54321\nws/path\n", encoding="utf-8")
    assert existing_debug_port(tmp_path) == 54321

    entry = ApplicationEntry(
        app_id="brave",
        display_name="Brave",
        kind=LaunchKind.EXECUTABLE,
        target=BRAVE_ENTRY.target,
        fixed_arguments=(f"--user-data-dir={tmp_path}",),
        verify_process_names=("brave.exe",),
    )
    session = BraveCdpSession(
        entry, already_running=lambda: True, launcher=lambda _argv: None
    )

    # Nothing is listening on the recalled port, so this must refuse rather
    # than hand back a session wired to a browser that is not there.
    with pytest.raises(BrowserUnavailable) as raised:
        session.__enter__()
    assert "already open" in str(raised.value)


def test_the_port_file_is_read_from_the_profile_the_entry_names(tmp_path) -> None:
    entry = ApplicationEntry(
        app_id="brave",
        display_name="Brave",
        kind=LaunchKind.EXECUTABLE,
        target=BRAVE_ENTRY.target,
        fixed_arguments=(f"--user-data-dir={tmp_path}",),
    )
    assert brave_user_data_dir(entry) == tmp_path


def test_a_browser_jarvis_did_not_start_is_never_closed() -> None:
    """Ending a Jarvis session must not take the user's tabs with it.

    Re-attaching only helps if detaching is safe. Playwright's `browser.close()`
    terminates a CDP-connected browser, so running it against a browser the user
    had already open would close their windows when Jarvis exited — a far worse
    outcome than the failure this path exists to remove.
    """
    closed: list[str] = []

    class FakeBrowser:
        def close(self) -> None:
            closed.append("browser")

    class FakeDriver:
        def stop(self) -> None:
            closed.append("driver")

    session = BraveCdpSession(BRAVE_ENTRY)
    session._browser = FakeBrowser()
    session._playwright = FakeDriver()
    session._started_the_browser = False

    session.__exit__(None, None, None)

    assert closed == ["driver"], (
        "Jarvis closed a browser it did not start; detaching is required, "
        "closing someone else's windows is not"
    )


def test_a_browser_jarvis_started_is_closed() -> None:
    """The other half: what Jarvis started, Jarvis closes (ADR-0031)."""
    closed: list[str] = []

    class FakeBrowser:
        def close(self) -> None:
            closed.append("browser")

    class FakeDriver:
        def stop(self) -> None:
            closed.append("driver")

    session = BraveCdpSession(BRAVE_ENTRY)
    session._browser = FakeBrowser()
    session._playwright = FakeDriver()
    session._started_the_browser = True

    session.__exit__(None, None, None)

    assert closed == ["browser", "driver"], (
        "a browser Jarvis started was left listening on a debugging port"
    )


# =========================================================================
# Defect 2: work abandoned by the tool timeout must not outlive the workspace
# =========================================================================
class SlowSession:
    """A session whose open finishes after the caller has given up on it.

    `during_open` runs inside `__enter__`, which is where the real shutdown
    landed: Jarvis stopped while the attach was still in flight, not before it
    started. A test that closed the workspace first and opened afterwards would
    pass against the broken code, because the ordering is the entire defect.
    """

    def __init__(self, during_open=None) -> None:
        self.entered = False
        self.exited = False
        self._during_open = during_open

    def __enter__(self):
        if self._during_open is not None:
            self._during_open()
        self.entered = True
        return self

    def __exit__(self, *_exc):
        self.exited = True

    def is_alive(self) -> bool:
        return self.entered and not self.exited

    def page(self):
        return object()


def test_a_session_that_opens_after_shutdown_is_closed_immediately() -> None:
    """The port leak the 2026-08-05 log caught, six seconds after shutdown.

    `ToolInvoker._run_with_timeout` abandons the *future*, not the thread. When
    `youtube.search` exceeded 90s the invoker reported `timed_out` and moved on,
    but the worker kept going and completed the attach at 06:35:23.712Z — after
    Jarvis had shut down at 06:34:45.079Z.

    `BrowserWorkspace.close()` had already run and found `self._session` still
    `None`, because the open had not finished assigning it. So nothing closed
    that browser: it was left running with an unauthenticated debugging port
    open on loopback, and Jarvis was no longer there to close it. ADR-0031
    treats that teardown as a security control, which makes this a leak of the
    control itself rather than an untidy exit.
    """
    workspace = BrowserWorkspace()
    # Jarvis shuts down while the attach is still in flight, and the attach
    # completes afterwards — the ordering the log recorded to the second.
    session = SlowSession(during_open=workspace.close)
    workspace._session_factory = lambda: session

    workspace._open()

    assert session.exited, (
        "a session that finished opening after shutdown was left attached, "
        "which leaves a debugging port open on a browser holding live logins"
    )
    assert not workspace.is_open


def test_a_normal_open_after_a_close_still_works() -> None:
    """The control: closing must not permanently disable the workspace.

    `close()` runs on ordinary paths too — a browser the user shut, a session
    being replaced. If it latched, the first close of the day would end browser
    automation until restart, which is the defect this phase already fixed once.
    """
    workspace = BrowserWorkspace(session_factory=SlowSession)
    workspace.adapter
    assert workspace.is_open

    workspace.close()
    assert not workspace.is_open

    workspace.adapter  # a fresh request, well after the close
    assert workspace.is_open, "the workspace refused to reopen after a normal close"
