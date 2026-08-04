"""Can Playwright drive a Brave that *we* launched, and is "the second video" addressable by index?

Phase 2 stage 0, part B. A research spike, outside the product runtime and
outside the security policy — the same status `tools/voice-lab/` holds.

Part A (`test_cdp_attach.py`) established that Brave opens a CDP port. This asks
the two questions that actually gate stage 3:

1. **Does `connect_over_cdp` attach to a browser we started ourselves?** If it
   does, Playwright is a client and ADR-0029's single process-creation call site
   is untouched. If it does not, the attach mechanism needs re-planning — and the
   answer is *not* to let Playwright launch Brave.

2. **Is a YouTube result list addressable as a structured list, selected by
   index?** This is the exit criterion's core, and it is also the phase's central
   security control. "Play the second video" must mean *the element at position
   two*, never *the element whose title says something*. If titles were the only
   handle, a page that can rename itself could redirect the action — which is
   exactly what `tests/security/test_prompt_injection.py` will assert against.
   This spike checks the handle exists before stage 1 is designed around it.

Titles are printed here only as evidence for a human reading the output. Nothing
selects on them, and the product must not either.

**What this does to your machine:** launches Brave, loads a real YouTube search
over the network, leaves the window open.

Run:  .\.venv\Scripts\python.exe tools\browser-lab\test_playwright_attach.py
"""

from __future__ import annotations

import json
import os
import socket
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from jarvis.toolbox.launch import (  # noqa: E402
    ApplicationEntry,
    ArgumentKind,
    LaunchKind,
    build_argv,
    launch_argv,
    process_running,
)

SEARCH_URL = "https://www.youtube.com/results?search_query=RTX+5070"
CDP_TIMEOUT_SECONDS = 15.0
PAGE_TIMEOUT_MS = 30_000
RESULTS_TIMEOUT_MS = 20_000

#: YouTube's result rows. Ordered in the DOM as they are ordered on screen, which
#: is what makes "the second video" a positional question rather than a textual one.
RESULT_SELECTOR = "ytd-video-renderer"


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def wait_for_cdp(port: int, timeout_seconds: float) -> dict[str, str] | None:
    url = f"http://127.0.0.1:{port}/json/version"
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2.0) as response:
                return json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, OSError, ValueError):
            time.sleep(0.25)
    return None


def main() -> int:
    if os.name != "nt":
        print("This spike measures Brave on Windows. Nothing to do here.")
        return 0

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print('playwright is not installed. Run: pip install -e ".[automation]"')
        return 1

    if process_running(("brave.exe",)):
        print(
            "Brave is already running. A second brave.exe hands its command line\n"
            "to the existing instance and exits, so no port will open and the\n"
            "result would be ambiguous. Close Brave and re-run."
        )
        return 1

    program_files = os.environ.get("ProgramFiles", r"C:\Program Files")
    port = free_port()
    entry = ApplicationEntry(
        app_id="brave_spike",
        display_name="Brave (Jarvis profile)",
        kind=LaunchKind.EXECUTABLE,
        target=rf"{program_files}\BraveSoftware\Brave-Browser\Application\brave.exe",
        fixed_arguments=("--profile-directory=Jarvis", f"--remote-debugging-port={port}"),
        argument_kind=ArgumentKind.NONE,
        verify_process_names=("brave.exe",),
    )

    argv = build_argv(entry)
    print("=" * 70)
    print("Stage 0 part B: Playwright attaches to a browser it did not launch")
    print("=" * 70)
    print(f"\nargv: {list(argv)}")
    print("(note: this vector comes from jarvis.toolbox.launch.build_argv —")
    print(" the product's own launcher, not a parallel one)")

    launch_argv(argv)
    banner = wait_for_cdp(port, CDP_TIMEOUT_SECONDS)
    if banner is None:
        print(f"\nFAILED: no CDP endpoint on 127.0.0.1:{port}")
        return 1
    print(f"\nCDP open: {banner.get('Browser')}")

    with sync_playwright() as playwright:
        try:
            browser = playwright.chromium.connect_over_cdp(f"http://127.0.0.1:{port}")
        except Exception as exc:  # noqa: BLE001 - a spike reports, it does not handle
            print(f"\nFAILED to attach: {type(exc).__name__}: {exc}")
            return 1

        print(f"ATTACHED. contexts={len(browser.contexts)}")
        context = browser.contexts[0] if browser.contexts else browser.new_context()
        page = context.new_page()

        print(f"\nLoading {SEARCH_URL}")
        page.goto(SEARCH_URL, timeout=PAGE_TIMEOUT_MS, wait_until="domcontentloaded")

        try:
            page.wait_for_selector(RESULT_SELECTOR, timeout=RESULTS_TIMEOUT_MS)
        except Exception as exc:  # noqa: BLE001
            print(f"FAILED: '{RESULT_SELECTOR}' never appeared: {type(exc).__name__}")
            print("        A consent interstitial or a layout change would do this.")
            print(f"        page title: {page.title()!r}")
            return 1

        results = page.query_selector_all(RESULT_SELECTOR)
        print(f"\nSTRUCTURED RESULT LIST: {len(results)} x '{RESULT_SELECTOR}'")
        print("Index-addressable, so 'the second video' is results[1] — a position,")
        print("never a title match. Titles below are evidence for you, not a handle:\n")

        for index, result in enumerate(results[:5]):
            title_element = result.query_selector("a#video-title")
            title = (title_element.get_attribute("title") if title_element else None) or "?"
            href = (title_element.get_attribute("href") if title_element else None) or "?"
            marker = "  <-- 'the second video'" if index == 1 else ""
            print(f"  [{index}] {title[:64]}{marker}")
            print(f"      {href[:64]}")

        print("\n" + "=" * 70)
        print("RESULT")
        print("=" * 70)
        print("  connect_over_cdp to our own launch : WORKS")
        print(f"  ADR-0029 process-creation sites    : still 1 (launch_argv)")
        print(f"  index-addressable result list      : {'YES' if len(results) >= 2 else 'NO'}")
        print("\nThe Brave window is left open. Close it when you are done.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
