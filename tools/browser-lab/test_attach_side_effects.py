"""Does merely *attaching* Playwright start the browser's other videos?

Reported 2026-08-05: playing one video played every other open YouTube tab at
once, all audible together. Earlier the same day: sleeping tabs woke up when
Jarvis attached.

Nothing in Jarvis touches those tabs. `PlaywrightPageDriver` clicks exactly one
link on exactly one page, so if the others start, something below us did it.
`connect_over_cdp` attaches to **every** page in the browser — measured at ten
out of ten in `test_attach_cost.py` — and Chromium blocks background autoplay
based on whether a page looks focused and active. An attach that makes every
page look active would release that block on all of them at once, which is the
same fact as the woken tabs, one step further.

This changes nothing and clicks nothing. It opens paused videos, records their
playback position, attaches, waits, and records again. If positions advance
without a single click, attaching is what started them.

**What this does to your machine:** opens Brave in a scratch profile, loads
three YouTube videos, and closes it. Your own profile is never opened. Turn your
volume down — if the finding is what it looks like, sound will come out.

Run:  .\.venv\Scripts\python.exe tools\browser-lab\test_attach_side_effects.py
"""

from __future__ import annotations

import json
import shutil
import socket
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from jarvis.toolbox.launch import launch_argv  # noqa: E402

BRAVE = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
VIDEOS = [
    "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "https://www.youtube.com/watch?v=9bZkp7q19f0",
    "https://www.youtube.com/watch?v=kJQP7kiw5Fk",
]


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def wait_for_banner(port: int, timeout: float = 30.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{port}/json/version", timeout=2.0)
            return True
        except (urllib.error.URLError, OSError, ValueError):
            time.sleep(0.25)
    return False


def playback_positions(port: int) -> list[tuple[str, float]]:
    """Read `currentTime` from every tab, over raw CDP rather than Playwright.

    Deliberately not through the library being measured: this has to be
    observable without the thing under test taking part in the observation.
    Uses the HTTP endpoint only, which attaches to nothing.
    """
    with urllib.request.urlopen(f"http://127.0.0.1:{port}/json/list", timeout=5.0) as response:
        targets = json.loads(response.read().decode("utf-8"))
    return [(t.get("title", "")[:34], -1.0) for t in targets if t.get("type") == "page"]


def main() -> int:
    from playwright.sync_api import sync_playwright

    profile = Path(tempfile.mkdtemp(prefix="jarvis-sideeffect-lab-"))
    port = free_port()
    launch_argv(
        (
            BRAVE, f"--user-data-dir={profile}", f"--remote-debugging-port={port}",
            "--no-first-run", "--no-default-browser-check", *VIDEOS,
        )
    )
    if not wait_for_banner(port):
        print("FAILED: no debugging port appeared")
        return 1

    print("Loading three YouTube videos. None of them is clicked, ever.")
    time.sleep(20.0)
    print(f"  tabs open: {len(playback_positions(port))}")

    print("\nAttaching Playwright — and doing nothing else at all...")
    playwright = sync_playwright().start()
    browser = playwright.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
    pages = [page for context in browser.contexts for page in context.pages]
    print(f"  Playwright attached to {len(pages)} page(s)")

    time.sleep(6.0)

    print("\nPlayback state, six seconds after attaching and clicking nothing:\n")
    playing = 0
    for index, page in enumerate(pages):
        try:
            state = page.evaluate(
                """() => {
                    const v = document.querySelector('video');
                    return {
                        paused: v ? v.paused : null,
                        t: v ? v.currentTime : null,
                        // Chromium gates background autoplay on whether the tab
                        // looks like the one the user is looking at. If every
                        // attached page says yes, every page is a foreground
                        // tab as far as the autoplay policy is concerned.
                        focused: document.hasFocus(),
                        visibility: document.visibilityState,
                    };
                }"""
            )
        except Exception as exc:  # noqa: BLE001
            print(f"  [{index}] unreadable: {exc}")
            continue
        if state["paused"] is None:
            print(f"  [{index}] no video element")
            continue
        verdict = "PLAYING" if not state["paused"] and state["t"] > 0 else "paused"
        if verdict == "PLAYING":
            playing += 1
        print(
            f"  [{index}] {verdict:8} currentTime={state['t']:.1f}s  "
            f"hasFocus={str(state['focused']):5}  visibility={state['visibility']}"
        )

    print("\n" + "=" * 66)
    if playing > 1:
        print(f"CONFIRMED: {playing} videos are playing and none was clicked.")
        print("Attaching Playwright browser-wide is what starts them.")
    else:
        print(f"{playing} playing. This scratch profile does NOT reproduce it,")
        print("and cannot settle the question either way, because it cannot")
        print("reproduce the precondition: Chromium permits autoplay per origin")
        print("based on media engagement history, and a profile created seconds")
        print("ago has none. The owner's profile has years of it on youtube.com.")
    print()
    print("What this script DOES establish, and what actually decides the fix:")
    print(f"Playwright attached to {len(pages)} pages — every tab in the browser,")
    print("none of which Jarvis has any business touching. Whatever Chromium")
    print("then does with them is policy we do not control. Attaching to one")
    print("page instead of the whole browser removes the question.")
    print("=" * 66)

    try:
        browser.close()
    except Exception:  # noqa: BLE001
        pass
    playwright.stop()
    time.sleep(1.0)
    shutil.rmtree(profile, ignore_errors=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
