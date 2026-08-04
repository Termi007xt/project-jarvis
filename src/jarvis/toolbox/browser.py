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
import socket
import time
import urllib.error
import urllib.request
from typing import Any

from jarvis.toolbox.launch import (
    EPHEMERAL_PORT_RANGE,
    ApplicationEntry,
    launch_argv,
)

__all__ = [
    "BraveCdpSession",
    "BrowserUnavailable",
    "PlaywrightPageDriver",
    "free_ephemeral_port",
    "RESULT_SELECTOR",
]

_LOG = logging.getLogger(__name__)

#: YouTube's result rows, ordered in the DOM as they appear on screen — which is
#: what makes "the second video" a positional question. Measured in stage 0
#: against the real page (`tools/browser-lab/test_playwright_attach.py`).
RESULT_SELECTOR = "ytd-video-renderer"

#: The dedicated automation profile (FR-056, ADR-0019 Option A). Fixed by
#: `PROJECT_INPUTS.md` as `automation.dedicated_browser_profile: Jarvis`, and
#: kept as a constant here rather than a config field until something actually
#: needs it to vary — a setting nobody changes is a setting that drifts out of
#: agreement with the profile the user has signed into.
DEDICATED_BROWSER_PROFILE = "Jarvis"

#: How long to wait for the browser to open its debugging port before giving up.
CDP_READY_TIMEOUT_SECONDS = 20.0
_CDP_POLL_SECONDS = 0.25


class BrowserUnavailable(RuntimeError):
    """The browser could not be started or attached to."""


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
    ) -> None:
        self._entry = entry
        self._ready_timeout = ready_timeout_seconds
        self._port: int | None = None
        self._playwright: Any = None
        self._browser: Any = None
        self._page: "PlaywrightPageDriver | None" = None

    @property
    def attached(self) -> bool:
        return self._browser is not None

    def __enter__(self) -> "BraveCdpSession":
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            raise BrowserUnavailable(
                "Playwright is not installed, so Jarvis cannot drive the "
                'browser. Install the automation extra: pip install -e ".[automation]"'
            ) from exc

        self._port = free_ephemeral_port()
        argv = (
            self._entry.target,
            *self._entry.fixed_arguments,
            f"--remote-debugging-port={self._port}",
        )
        launch_argv(argv)  # the one authorised call site (ADR-0029)

        banner = _cdp_banner(self._port, self._ready_timeout)
        if banner is None:
            raise BrowserUnavailable(
                "the browser did not open its automation port within "
                f"{self._ready_timeout:.0f}s. If Brave was already running, its "
                "command line was handed to the existing instance and no port "
                "was opened — close Brave and try again."
            )

        self._playwright = sync_playwright().start()
        # connect_over_cdp, never launch: Playwright is a client here.
        self._browser = self._playwright.chromium.connect_over_cdp(
            f"http://127.0.0.1:{self._port}"
        )
        _LOG.info("attached to %s over CDP", banner.get("Browser"))
        return self

    def __exit__(self, *_exc: object) -> None:
        # Unconditional: a browser left listening on a debugging port after a
        # failed session is exactly the residual risk ADR-0031 bounds.
        for closer in (self._browser, self._playwright):
            if closer is None:
                continue
            try:
                closer.close() if closer is self._browser else closer.stop()
            except Exception:  # noqa: BLE001 - teardown must not mask the cause
                _LOG.warning("browser teardown did not complete cleanly", exc_info=True)
        self._browser = None
        self._playwright = None
        self._page = None
        self._port = None

    def page(self) -> "PlaywrightPageDriver":
        """The session's page. The *same* one every time.

        This opened a new tab on every call until a spike called it twice and
        got two. "Play the second video" would then have run against a fresh
        blank tab rather than the results the search had just read — the two
        utterances silently talking about different pages.
        """
        if self._browser is None:
            raise BrowserUnavailable("no browser is attached; use this as a context manager")
        if self._page is None:
            context = (
                self._browser.contexts[0]
                if self._browser.contexts
                else self._browser.new_context()
            )
            self._page = PlaywrightPageDriver(context.new_page())
        return self._page


class PlaywrightPageDriver:
    """`PageDriver` against a real page. Positional throughout.

    Note what is absent: nothing takes a title, a label or arbitrary text. The
    only way to identify a result is its ordinal.
    """

    def __init__(self, page: Any) -> None:
        self._page = page

    def goto(self, url: str, timeout_seconds: float) -> None:
        self._page.goto(url, timeout=timeout_seconds * 1000, wait_until="domcontentloaded")

    def results(self, timeout_seconds: float) -> list[dict[str, str]]:
        try:
            self._page.wait_for_selector(RESULT_SELECTOR, timeout=timeout_seconds * 1000)
        except Exception:  # noqa: BLE001
            # No results is a fact, not a failure. A consent interstitial or a
            # layout change also lands here, which is why the caller sees an
            # empty list rather than an exception it would have to guess about.
            _LOG.info("no %r appeared within %.0fs", RESULT_SELECTOR, timeout_seconds)
            return []

        found: list[dict[str, str]] = []
        for element in self._page.query_selector_all(RESULT_SELECTOR):
            link = element.query_selector("a#video-title")
            title = (link.get_attribute("title") if link else None) or ""
            href = (link.get_attribute("href") if link else None) or ""
            found.append({"title": title, "video_id": _video_id_from(href)})
        return found

    def click_result(self, position: int, timeout_seconds: float) -> None:
        elements = self._page.query_selector_all(RESULT_SELECTOR)
        if position >= len(elements):
            raise IndexError(f"position {position} is past the {len(elements)} results")
        link = elements[position].query_selector("a#video-title")
        if link is None:
            raise RuntimeError(f"result {position} has no playable link")
        link.click(timeout=timeout_seconds * 1000)

    def player_state(self, timeout_seconds: float) -> dict[str, Any] | None:
        """Read the player back. This is what turns a click into a success."""
        try:
            self._page.wait_for_selector("video", timeout=timeout_seconds * 1000)
            return self._page.evaluate(
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
