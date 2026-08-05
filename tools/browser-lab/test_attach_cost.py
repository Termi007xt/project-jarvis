"""How much does `connect_over_cdp` cost as the browser's tab count grows?

Phase 2, after the Option D switch. A research spike, outside the product
runtime and outside the security policy — the same status the other scripts in
this directory hold.

**Why this measurement exists.** On 2026-08-05 a `youtube.search` in the owner's
own Brave profile, with roughly ten YouTube tabs already open, took 96 seconds to
reach "attached" and blew through the tool's 90s timeout. Every attach recorded
against the *dedicated* profile — which held one blank tab — took 0.7s to 2.9s.
Two things changed at once that day, so the log alone cannot say whether the cost
is the profile or the tabs. This separates them.

It also asks the question the owner actually reported: their sleeping tabs all
became active when Jarvis attached. If attaching wakes discarded tabs, that is
not a cosmetic annoyance, it is the same fact as the 96 seconds.

Five runs, changing one variable at a time:

  A. 1 blank tab, settled              — the floor
  B. 10 blank tabs, settled            — cost of *count*
  C. 10 YouTube tabs, settled          — cost of *weight*
  E. 10 YouTube tabs, attach at once   — cost of attaching *during* a cold start
  F. 1 blank tab, attach at once       — E's control

**The measured answer, 2026-08-05: none of them.** A 0.01s, B 0.03s, C 0.09s,
E 0.89s, F 0.02s. Attaching is close to free under every arrangement, so neither
the tab count, the tab weight, nor the cold start accounts for the 96 seconds —
and the hypothesis that they did was wrong. `BraveCdpSession` now logs each
phase separately, because the total and the parts disagreed and no amount of
re-reading the old log could settle which phase was slow.

Keep this script: it is the evidence that three plausible explanations are ruled
out, which is worth more than the guesses it replaced.

**What this does to your machine:** launches Brave in a scratch profile under the
temp directory, loads real YouTube pages over the network, and closes it again.
Your own Brave profile is never opened and never touched.

Run:  .\.venv\Scripts\python.exe tools\browser-lab\test_attach_cost.py
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

#: Real pages, because the point is the weight of a live SPA, not of a URL.
YOUTUBE = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def wait_for_banner(port: int, timeout: float = 30.0) -> dict | None:
    url = f"http://127.0.0.1:{port}/json/version"
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2.0) as response:
                return json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, OSError, ValueError):
            time.sleep(0.25)
    return None


def targets(port: int) -> list[dict]:
    """The browser's own view of its tabs, read over plain HTTP.

    Deliberately *not* via Playwright: this has to be observable without the
    thing being measured taking part in the measurement.
    """
    with urllib.request.urlopen(f"http://127.0.0.1:{port}/json/list", timeout=5.0) as response:
        return json.loads(response.read().decode("utf-8"))


def run_case(label: str, urls: list[str], settle_seconds: float) -> None:
    from playwright.sync_api import sync_playwright

    profile = Path(tempfile.mkdtemp(prefix="jarvis-attach-lab-"))
    port = free_port()
    argv = (
        BRAVE,
        f"--user-data-dir={profile}",
        f"--remote-debugging-port={port}",
        "--no-first-run",
        "--no-default-browser-check",
        *urls,
    )

    print(f"\n=== {label} ===")
    launch_argv(argv)
    banner = wait_for_banner(port)
    if banner is None:
        print("  FAILED: no debugging port appeared")
        shutil.rmtree(profile, ignore_errors=True)
        return

    # Let the pages finish loading, so we are measuring attach cost and not
    # racing the network.
    time.sleep(settle_seconds)

    before = targets(port)
    pages_before = [t for t in before if t.get("type") == "page"]
    print(f"  tabs open before attach: {len(pages_before)}")

    started = time.monotonic()
    playwright = sync_playwright().start()
    started_connect = time.monotonic()
    browser = playwright.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
    connected = time.monotonic()

    contexts = browser.contexts
    page_count = sum(len(context.pages) for context in contexts)

    print(f"  sync_playwright().start() : {started_connect - started:6.2f}s")
    print(f"  connect_over_cdp()        : {connected - started_connect:6.2f}s   <-- the number")
    print(f"  contexts={len(contexts)}  pages Playwright attached to={page_count}")

    try:
        browser.close()
    except Exception:  # noqa: BLE001
        pass
    playwright.stop()
    shutil.rmtree(profile, ignore_errors=True)


def main() -> int:
    print("Measuring connect_over_cdp cost against tab count and tab weight.")
    print("A scratch profile is used; your own Brave profile is not opened.")

    run_case("A. 1 blank tab, settled", ["about:blank"], settle_seconds=2.0)
    run_case("B. 10 blank tabs, settled", ["about:blank"] * 10, settle_seconds=3.0)
    run_case("C. 10 YouTube tabs, settled", [YOUTUBE] * 10, settle_seconds=25.0)
    # The one the log actually shows. A-C all wait for the tabs to finish
    # loading before attaching, which is not what happened: Brave had just
    # cold-started and was still bringing its restored tabs up when Jarvis
    # attached. Same tabs, same count — only the timing differs.
    run_case("E. 10 YouTube tabs, attach immediately", [YOUTUBE] * 10, settle_seconds=0.0)
    run_case("F. 1 blank tab, attach immediately", ["about:blank"], settle_seconds=0.0)

    print("\nA-C attach after the pages settled. E attaches while they are still")
    print("loading, which is the state the 2026-08-05 log captured. F is E's")
    print("control: same timing, nothing heavy to load.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
