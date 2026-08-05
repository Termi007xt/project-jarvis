"""Driving the dedicated Brave profile over CDP (FR-056, FR-072, ADR-0031).

Phase 2 stage 3. Brave is started through the **one** authorised
process-creation call site — `jarvis.toolbox.launch.launch_argv` — with an
ephemeral debugging port, and Playwright *attaches* to it. Playwright never
launches anything, and `tests/security/test_browser_attach.py` fails the build if
that ever changes.

Why it is worth the extra machinery: `playwright.chromium.launch_persistent_context()`
would create a browser process from library code inside `site-packages`, which
`tests/security/test_no_shell.py` cannot see, because that scanner AST-scans
`src/`. The `ALLOW_LIST` would stay empty and the security suite would stay
green while ADR-0029's single-call-site invariant was quietly false — a green
suite compatible with a broken product, aimed at the control everything else
rests on.

**The CDP port is a real cost, not a free trick.** It is an unauthenticated local
control channel on a browser that may hold live logins. The mitigations ADR-0031
requires are implemented here rather than described: an ephemeral port chosen per
session, bound to loopback, opened when a session starts and closed with it, and
never recorded in audit parameters or shown to the model.

Selector policy: everything here addresses results **by position**. There is no
method that resolves an element from page text, because that is the one thing
that would let a page choose what an action lands on by renaming itself
(`jarvis.core.observations`, `tests/security/test_prompt_injection.py`).
"""

from __future__ import annotations

import json
import logging
import os
import socket
import threading
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from pathlib import Path
from typing import Any

from jarvis.toolbox.launch import (
    EPHEMERAL_PORT_RANGE,
    ApplicationEntry,
    launch_argv,
    process_running,
)

__all__ = [
    "BraveCdpSession",
    "BrowserUnavailable",
    "BrowserNeedsRestart",
    "PlaywrightPageDriver",
    "brave_user_data_dir",
    "browser_windows",
    "close_window",
    "existing_debug_port",
    "free_ephemeral_port",
    "quit_browser",
    "RESULT_SELECTOR",
]

_LOG = logging.getLogger(__name__)

#: YouTube's result rows, ordered in the DOM as they appear on screen — which is
#: what makes "the second video" a positional question. Measured in stage 0
#: against the real page (`tools/browser-lab/test_playwright_attach.py`).
RESULT_SELECTOR = "ytd-video-renderer"

#: Which Brave profile automation drives.
#:
#: `"Default"` since 2026-08-04, by owner decision: automation runs in their own
#: profile so there is one browser window and one set of logins. This is a
#: recorded departure from FR-056's dedicated profile — the reasoning, the risk
#: and the controls it makes load-bearing are in ADR-0019, which should be read
#: before this is changed back or forward.
DEDICATED_BROWSER_PROFILE = "Default"

#: How long to wait for the browser to open its debugging port before giving up.
CDP_READY_TIMEOUT_SECONDS = 20.0
_CDP_POLL_SECONDS = 0.25

#: A port recalled from `DevToolsActivePort` belongs to a browser that is
#: already running, so it either answers at once or the file is stale. There is
#: nothing to wait for, and waiting is the failure this whole path exists to
#: remove.
_RECALLED_PORT_TIMEOUT_SECONDS = 2.0


class BrowserUnavailable(RuntimeError):
    """The browser could not be started or attached to."""


class BrowserThreadViolation(RuntimeError):
    """A page was driven from a thread other than the one that created it.

    Playwright's synchronous API is bound to its creating thread, and the
    failure it produces otherwise is neither legible nor local: an asyncio
    callback raises `greenlet.error: Cannot switch to a different thread`, the
    page ends up closed, and the traceback points at Playwright internals rather
    than at the call that was wrong. On 2026-08-05 that surfaced to the owner as
    a browser that opened a blank tab and never searched.

    Raised eagerly and by name so the *next* caller to get this wrong is told
    what they did, at the moment they do it.
    """


class BrowserNeedsRestart(BrowserUnavailable):
    """Brave is running without an automation port, and only a restart fixes it.

    Its own type because it is the one browser failure with a known, automatable
    remedy. Collapsed into `BrowserUnavailable` it was indistinguishable from a
    missing Playwright or a browser that will not start, and on 2026-08-05 the
    model responded to it by inventing instructions for a human — *"I need you
    to manually quit Brave once from your taskbar"* — about a browser Jarvis had
    opened itself fifty-six seconds earlier.
    """


#: How long to wait for a browser to shut down after its windows are asked to
#: close. Generous, because Chromium writes out session state on the way out and
#: that is precisely what makes the tabs come back.
QUIT_TIMEOUT_SECONDS = 15.0
_QUIT_POLL_SECONDS = 0.25


def browser_windows(process_names: tuple[str, ...]) -> list[int]:
    """Top-level window handles belonging to any of the named processes.

    Read-only: enumerating windows changes nothing. Windows-only, and empty
    everywhere else, which keeps the Linux import CI enforces working.
    """
    if not process_names or os.name != "nt":
        return []
    import ctypes
    from ctypes import wintypes

    wanted_pids = _pids_for(process_names)
    if not wanted_pids:
        return []

    user32 = ctypes.windll.user32  # type: ignore[attr-defined]
    handles: list[int] = []

    callback_type = ctypes.WINFUNCTYPE(
        wintypes.BOOL, wintypes.HWND, wintypes.LPARAM
    )

    def visit(hwnd: int, _param: int) -> bool:
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        # Only visible top-level windows: Chromium keeps a swarm of hidden
        # message-only windows, and asking those to close does nothing while
        # making the count meaningless.
        if pid.value in wanted_pids and user32.IsWindowVisible(hwnd):
            handles.append(int(hwnd))
        return True

    user32.EnumWindows(callback_type(visit), 0)
    return handles


def _pids_for(process_names: tuple[str, ...]) -> set[int]:
    """Process ids for the named executables, via the tool-help snapshot."""
    if os.name != "nt":
        return set()
    import ctypes
    from ctypes import wintypes

    wanted = {name.casefold() for name in process_names}

    class PROCESSENTRY32W(ctypes.Structure):
        _fields_ = [
            ("dwSize", wintypes.DWORD),
            ("cntUsage", wintypes.DWORD),
            ("th32ProcessID", wintypes.DWORD),
            ("th32DefaultHeapID", ctypes.POINTER(ctypes.c_ulong)),
            ("th32ModuleID", wintypes.DWORD),
            ("cntThreads", wintypes.DWORD),
            ("th32ParentProcessID", wintypes.DWORD),
            ("pcPriClassBase", ctypes.c_long),
            ("dwFlags", wintypes.DWORD),
            ("szExeFile", wintypes.WCHAR * 260),
        ]

    kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
    snapshot = kernel32.CreateToolhelp32Snapshot(0x00000002, 0)
    if snapshot == ctypes.c_void_p(-1).value:
        return set()
    found: set[int] = set()
    try:
        entry = PROCESSENTRY32W()
        entry.dwSize = ctypes.sizeof(PROCESSENTRY32W)
        if not kernel32.Process32FirstW(snapshot, ctypes.byref(entry)):
            return found
        while True:
            if entry.szExeFile.casefold() in wanted:
                found.add(int(entry.th32ProcessID))
            if not kernel32.Process32NextW(snapshot, ctypes.byref(entry)):
                return found
    finally:
        kernel32.CloseHandle(snapshot)


def close_window(handle: int) -> None:
    """Ask a window to close, the way clicking its X does.

    `WM_CLOSE` is a *request*: the application decides what to do with it, which
    is the entire point. Chromium takes it as "quit", writes its session out and
    restores those tabs next time. Terminating the process would skip all of
    that and greet the user with "Brave didn't shut down correctly" — while
    Jarvis had just promised their tabs would come back.
    """
    if os.name != "nt":  # pragma: no cover - Windows-only path
        return
    import ctypes

    WM_CLOSE = 0x0010
    ctypes.windll.user32.PostMessageW(handle, WM_CLOSE, 0, 0)  # type: ignore[attr-defined]


#: Bound before `quit_browser` shadows the name with its parameter, so the
#: default stays the real function rather than a `globals()` lookup.
_CLOSE_WINDOW = close_window


def quit_browser(
    process_names: tuple[str, ...],
    *,
    timeout_seconds: float = QUIT_TIMEOUT_SECONDS,
    windows_for: "Callable[[tuple[str, ...]], list[int]] | None" = None,
    close_window: "Callable[[int], None] | None" = None,
    still_running: "Callable[[tuple[str, ...]], bool] | None" = None,
    sleep: "Callable[[float], None] | None" = None,
) -> bool:
    """Close the browser gracefully and confirm it actually exited.

    Returns whether it is gone. Never forces the issue: a page holding an
    "unsaved changes" prompt is the owner's to answer, and discarding their work
    to satisfy a search would be a far worse outcome than saying so.

    The seams are injected for the same reason `BraveCdpSession` injects its
    launcher — the whole path is then testable without a real browser, and CI
    stays able to run it on Linux.
    """
    find_windows = windows_for or browser_windows
    close = close_window or _CLOSE_WINDOW
    running = still_running or process_running
    pause = sleep or time.sleep

    if not running(process_names):
        return True  # already closed; the owner may have got there first

    handles = find_windows(process_names)
    for handle in handles:
        close(handle)
    _LOG.info("asked %d browser window(s) to close", len(handles))

    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if not running(process_names):
            return True
        pause(_QUIT_POLL_SECONDS)

    return not running(process_names)


def free_ephemeral_port() -> int:
    """An unused port, chosen per session (ADR-0031 constraint 1).

    A fixed, well-known port would leave a predictable control channel open on
    the user's browser for anything local to find.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        port = int(sock.getsockname()[1])
    low, high = EPHEMERAL_PORT_RANGE
    if not low <= port <= high:  # pragma: no cover - the OS does not do this
        raise BrowserUnavailable(f"the OS offered an unusable port: {port}")
    return port


def brave_user_data_dir(entry: ApplicationEntry) -> Path | None:
    """Where the profile this entry drives keeps its state.

    Taken from the entry's own `--user-data-dir` when it sets one, and otherwise
    Chromium's default location for Brave. Only ever used to *read* the port
    file below.
    """
    for argument in entry.fixed_arguments:
        if argument.startswith("--user-data-dir="):
            return Path(argument.split("=", 1)[1])
    local_app_data = os.environ.get("LOCALAPPDATA")
    if not local_app_data:
        return None
    return Path(local_app_data) / "BraveSoftware" / "Brave-Browser" / "User Data"


def existing_debug_port(user_data_dir: Path | None) -> int | None:
    """The port a *running* Brave already has open, if it has one.

    Chromium writes the live debugging port to `DevToolsActivePort` in the user
    data directory when it starts with one, and removes the file when it exits
    cleanly. That makes a browser Jarvis started earlier re-attachable after
    Jarvis itself restarts — the difference between "restarting Jarvis fixed it"
    and "restarting Jarvis left the browser unusable until I closed Brave too".

    The file is a hint and nothing more. A stale one survives a crash, so the
    caller must confirm the port actually answers before trusting it. Reading it
    does not widen ADR-0031 constraint 1 either: the port is still ephemeral and
    still chosen per browser start, it is simply being *recalled* rather than
    chosen again.
    """
    if user_data_dir is None:
        return None
    try:
        first_line = (user_data_dir / "DevToolsActivePort").read_text(
            encoding="utf-8"
        ).splitlines()[0]
        port = int(first_line.strip())
    except (OSError, ValueError, IndexError):
        return None
    low, high = EPHEMERAL_PORT_RANGE
    return port if low <= port <= high else None


def _cdp_banner(port: int, timeout_seconds: float) -> dict[str, Any] | None:
    """Wait for the debugging endpoint, bounded. Loopback only."""
    url = f"http://127.0.0.1:{port}/json/version"
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2.0) as response:
                return json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, OSError, ValueError):
            time.sleep(_CDP_POLL_SECONDS)
    return None


class BraveCdpSession:
    """A Brave we started, attached to over CDP, and close when done.

    Used as a context manager so the browser is not left listening on a
    debugging port after a failure. That teardown is a security control, not
    tidiness — see ADR-0031.
    """

    def __init__(
        self,
        entry: ApplicationEntry,
        *,
        ready_timeout_seconds: float = CDP_READY_TIMEOUT_SECONDS,
        already_running: "Callable[[], bool] | None" = None,
        launcher: "Callable[[tuple[str, ...]], Any] | None" = None,
    ) -> None:
        self._entry = entry
        self._ready_timeout = ready_timeout_seconds
        self._already_running = already_running or self._brave_is_running
        self._launch = launcher or launch_argv
        self._port: int | None = None
        self._playwright: Any = None
        self._browser: Any = None
        self._page: "PlaywrightPageDriver | None" = None
        #: Whether *this* session started the browser. Decides whether teardown
        #: may close it — see `__exit__`.
        self._started_the_browser = False

    def _brave_is_running(self) -> bool:
        names = self._entry.verify_process_names or ("brave.exe",)
        return process_running(names)

    @property
    def attached(self) -> bool:
        return self._browser is not None

    def is_alive(self) -> bool:
        """Whether the browser we attached to is still running.

        Attached is not alive: the user closing Brave leaves this object holding
        a browser handle whose every call raises "Target page, context or
        browser has been closed". Asking Playwright directly is the only honest
        answer, and it is what lets the workspace reopen instead of failing for
        the rest of the session.
        """
        if self._browser is None:
            return False
        try:
            return bool(self._browser.is_connected())
        except Exception:  # noqa: BLE001 - a handle that cannot answer is gone
            return False

    def __enter__(self) -> "BraveCdpSession":
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            raise BrowserUnavailable(
                "Playwright is not installed, so Jarvis cannot drive the "
                'browser. Install the automation extra: pip install -e ".[automation]"'
            ) from exc

        # Asked *before* launching, because the answer decides whether launching
        # can possibly help. `--remote-debugging-port` is a startup flag: a
        # second `brave.exe` handed to a running instance forwards its command
        # line and exits, and no port is ever opened. Waiting the full timeout to
        # learn that costs the user 20 seconds of silence to reach a conclusion
        # available in microseconds — and, worse, the pointless launch pulls
        # their browser window to the foreground first.
        if self._already_running():
            recalled = existing_debug_port(brave_user_data_dir(self._entry))
            # Confirmed, never assumed: the file outlives a crash, and a stale
            # port would otherwise be attached to as though it were live.
            banner = (
                _cdp_banner(recalled, _RECALLED_PORT_TIMEOUT_SECONDS)
                if recalled is not None
                else None
            )
            if banner is None:
                raise BrowserNeedsRestart(
                    "Brave is already open, and a browser that is already "
                    "running cannot be given an automation port — that setting "
                    "only applies when it starts. Call the 'browser.restart' "
                    "tool to close Brave and reopen it with the tabs restored, "
                    "then try again. Do not ask the user to close it by hand."
                )
            # A browser we did not start. Attach to it, but never close it.
            self._port = recalled
            self._started_the_browser = False
            self._attach(banner, launched_at=time.monotonic())
            return self

        self._started_the_browser = True
        self._port = free_ephemeral_port()
        argv = (
            self._entry.target,
            *self._entry.fixed_arguments,
            f"--remote-debugging-port={self._port}",
        )
        launched_at = time.monotonic()
        self._launch(argv)  # the one authorised call site (ADR-0029)

        banner = _cdp_banner(self._port, self._ready_timeout)
        if banner is None:
            raise BrowserUnavailable(
                "the browser did not open its automation port within "
                f"{self._ready_timeout:.0f}s, so there is nothing to attach to. "
                "Nothing was searched."
            )

        self._attach(banner, launched_at=launched_at, port_open_at=time.monotonic())
        return self

    def _attach(
        self,
        banner: dict[str, Any],
        *,
        launched_at: float,
        port_open_at: float | None = None,
    ) -> None:
        """Connect Playwright to a port that has already been confirmed open."""
        from playwright.sync_api import sync_playwright

        port_open_at = launched_at if port_open_at is None else port_open_at
        self._playwright = sync_playwright().start()
        driver_at = time.monotonic()
        # connect_over_cdp, never launch: Playwright is a client here.
        self._browser = self._playwright.chromium.connect_over_cdp(
            f"http://127.0.0.1:{self._port}"
        )
        attached_at = time.monotonic()

        # Per phase, not just a total. On 2026-08-05 this path took 96s against
        # a 90s tool timeout, and the log recorded only "attached" — which said
        # that it was slow and nothing about *where*. Every phase was
        # individually measured as fast afterwards, so the total and the parts
        # disagreed and the log could not settle it. Timing each boundary is what
        # makes the next occurrence name its own cause (`tools/browser-lab/
        # test_attach_cost.py` holds the measurements).
        _LOG.info(
            "attached to %s over CDP in %.1fs "
            "(port wait %.1fs, driver start %.1fs, attach %.1fs); "
            "browser started by Jarvis: %s",
            banner.get("Browser"),
            attached_at - launched_at,
            port_open_at - launched_at,
            driver_at - port_open_at,
            attached_at - driver_at,
            self._started_the_browser,
        )

    def __exit__(self, *_exc: object) -> None:
        # Detaching is unconditional: a session left connected to a debugging
        # port after a failure is exactly the residual risk ADR-0031 bounds.
        #
        # *Closing the browser* is not. Jarvis closes what Jarvis started; a
        # browser that was already running when we attached is the user's, and
        # ending a Jarvis session is not a reason to take their tabs with it.
        # Dropping the Playwright connection without closing leaves them exactly
        # as they were.
        if self._browser is not None and self._started_the_browser:
            try:
                self._browser.close()
            except Exception:  # noqa: BLE001 - teardown must not mask the cause
                _LOG.warning("browser teardown did not complete cleanly", exc_info=True)
        if self._playwright is not None:
            try:
                self._playwright.stop()
            except Exception:  # noqa: BLE001
                _LOG.warning("the automation driver did not stop cleanly", exc_info=True)
        self._browser = None
        self._playwright = None
        self._page = None
        self._port = None

    def page(self) -> "PlaywrightPageDriver":
        """The session's page. The *same* one every time — while it exists.

        This opened a new tab on every call until a spike called it twice and
        got two. "Play the second video" would then have run against a fresh
        blank tab rather than the results the search had just read — the two
        utterances silently talking about different pages.

        Sticky is not the same as immortal, though. The driver is handed the
        means to open a replacement tab, because the owner closing one is the
        most ordinary thing anybody does in a browser and it must not cost them
        the rest of the session (see `PlaywrightPageDriver._live`).
        """
        if self._browser is None:
            raise BrowserUnavailable("no browser is attached; use this as a context manager")
        if self._page is None:
            context = (
                self._browser.contexts[0]
                if self._browser.contexts
                else self._browser.new_context()
            )
            self._page = PlaywrightPageDriver(
                context.new_page(), new_page=context.new_page
            )
        return self._page


class PlaywrightPageDriver:
    """`PageDriver` against a real page. Positional throughout.

    Note what is absent: nothing takes a title, a label or arbitrary text. The
    only way to identify a result is its ordinal.
    """

    def __init__(self, page: Any, *, new_page: "Callable[[], Any] | None" = None) -> None:
        self._page = page
        self._new_page = new_page
        #: The thread Playwright bound itself to. Every later call must arrive
        #: on it — see `_check_thread`.
        self._owner_thread = threading.get_ident()
        self._prepare(page)

    def _check_thread(self) -> None:
        """Refuse, legibly, rather than fail illegibly somewhere else later.

        `BrowserWorkspace` owns a thread and routes work to it, and on
        2026-08-05 it did that correctly for opening the session and then handed
        the adapter back so the tools drove it from the invoker's worker
        instead. Nothing objected at the call site. What objected was an asyncio
        callback minutes later, with `greenlet.error: Cannot switch to a
        different thread` and a closed page, and the visible result was a
        browser that opened a blank tab and never searched.

        The routing is the fix. This is what stops it being undone silently: the
        object that is thread-bound is the one that knows, so it is the one that
        checks.
        """
        current = threading.get_ident()
        if current != self._owner_thread:
            raise BrowserThreadViolation(
                f"the browser was driven from thread {current}, but Playwright "
                f"bound this page to thread {self._owner_thread}. Route the call "
                "through BrowserWorkspace.with_adapter() so it runs on the "
                "browser's own thread."
            )

    @staticmethod
    def _prepare(page: Any) -> None:
        """Undo Playwright's own emulation, so this looks like the owner's tab.

        Playwright forces `prefers-color-scheme: light` on pages it creates. On
        2026-08-05 that produced one light-mode YouTube tab among a window of
        dark ones — small, and exactly the kind of tell that makes automation
        feel like a foreign process rather than the owner's own session, which
        is the opposite of what ADR-0019 chose their real profile for.
        """
        try:
            page.emulate_media(color_scheme="null")
        except Exception:  # noqa: BLE001 - cosmetic; never worth failing a search
            _LOG.debug("could not clear the emulated colour scheme", exc_info=True)

    def _live(self) -> Any:
        """The page, replaced if the owner closed it.

        Reported 2026-08-05 as *"the YouTube search failed because the browser
        tab was unexpectedly closed"*, and recorded in the audit log as
        `Page.goto: Target page, context or browser has been closed`. The
        *browser* was fine — `is_alive()` said so correctly — and the single
        cached tab was what had died, which nothing looked at.
        """
        self._check_thread()
        if self._new_page is None:
            return self._page
        try:
            closed = bool(self._page.is_closed())
        except Exception:  # noqa: BLE001 - a page that cannot answer is gone
            closed = True
        if closed:
            _LOG.info("the tab was closed; opening a fresh one")
            self._page = self._new_page()
            self._prepare(self._page)
        return self._page

    def goto(self, url: str, timeout_seconds: float) -> None:
        self._live().goto(url, timeout=timeout_seconds * 1000, wait_until="domcontentloaded")

    def content(self) -> str:
        """The page's markup, for anti-bot detection only (FR-058).

        Untrusted, like everything else read from a page. It is used solely to
        decide whether to *stop*, never to decide whether to proceed — see
        `jarvis.toolbox.captcha` for why that direction matters.
        """
        # Resolved outside the `try`, so a thread violation is raised rather
        # than swallowed into "the page was unreadable" — which is how a
        # misrouted call would otherwise disappear into an empty string and
        # surface much later as something unrelated.
        page = self._live()
        try:
            return page.content()
        except Exception:  # noqa: BLE001
            # An unreadable page is not a challenge; let the normal result path
            # report honestly rather than inventing a CAPTCHA.
            _LOG.debug("page content could not be read", exc_info=True)
            return ""

    def results(self, timeout_seconds: float) -> list[dict[str, str]]:
        page = self._live()
        try:
            page.wait_for_selector(RESULT_SELECTOR, timeout=timeout_seconds * 1000)
        except Exception:  # noqa: BLE001
            # No results is a fact, not a failure. A consent interstitial or a
            # layout change also lands here, which is why the caller sees an
            # empty list rather than an exception it would have to guess about.
            _LOG.info("no %r appeared within %.0fs", RESULT_SELECTOR, timeout_seconds)
            return []

        found: list[dict[str, str]] = []
        for element in page.query_selector_all(RESULT_SELECTOR):
            link = element.query_selector("a#video-title")
            title = (link.get_attribute("title") if link else None) or ""
            href = (link.get_attribute("href") if link else None) or ""
            found.append({"title": title, "video_id": _video_id_from(href)})
        return found

    def click_result(self, position: int, timeout_seconds: float) -> None:
        elements = self._live().query_selector_all(RESULT_SELECTOR)
        if position >= len(elements):
            raise IndexError(f"position {position} is past the {len(elements)} results")
        link = elements[position].query_selector("a#video-title")
        if link is None:
            raise RuntimeError(f"result {position} has no playable link")
        link.click(timeout=timeout_seconds * 1000)

    def player_state(self, timeout_seconds: float) -> dict[str, Any] | None:
        """Read the player back. This is what turns a click into a success."""
        page = self._live()
        try:
            page.wait_for_selector("video", timeout=timeout_seconds * 1000)
            return page.evaluate(
                """() => {
                    const video = document.querySelector('video');
                    if (!video) return null;
                    const url = new URL(window.location.href);
                    return {
                        playing: !video.paused && !video.ended && video.currentTime > 0,
                        video_id: url.searchParams.get('v') || ''
                    };
                }"""
            )
        except Exception:  # noqa: BLE001
            # Unreadable, which is *unverified* — deliberately not reported as
            # "not playing", because those are different facts.
            _LOG.info("the player could not be read", exc_info=True)
            return None


def _video_id_from(href: str) -> str:
    """Pull the id out of a `/watch?v=...` link. Never trusts it as a selector."""
    if "v=" not in href:
        return ""
    return href.split("v=", 1)[1].split("&", 1)[0]
