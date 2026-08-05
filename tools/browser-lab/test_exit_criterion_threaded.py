"""The exit criterion again — but reached the way production reaches it.

`test_exit_criterion.py` drives `BraveCdpSession -> PlaywrightPageDriver ->
YouTubeAdapter` straight from the main thread. It passed on 2026-08-05 while the
product was completely broken, because the *thread* was the broken part and the
lab never had more than one.

Production has several. `ToolInvoker` runs every tool on a four-worker pool, so
"open YouTube and search for best gaming monitors" and "play the second video"
routinely arrive on different threads. Playwright's synchronous API is bound to
the thread that created it, and driving it from another raises `greenlet.error:
Cannot switch to a different thread` from an asyncio callback — after which the
page is closed. What the owner saw was Brave opening a blank tab and never
searching.

So this asks the question the other lab cannot:

    Do two utterances still work when they arrive on two different threads?

The tools are called through `YouTubeSearchTool.run` / `YouTubePlayTool.run`,
from two separate executors, so the calling thread differs between them exactly
as it does in the product.

**What this does to your machine:** opens Brave on your own profile (ADR-0019
Option D), searches YouTube, and plays a video. Sound will come out. Close Brave
first — a browser that is already running cannot be given an automation port.

Run:  .\.venv\Scripts\python.exe tools\browser-lab\test_exit_criterion_threaded.py
"""

from __future__ import annotations

import os
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from jarvis.core.tools.contract import ToolContext  # noqa: E402
from jarvis.toolbox.browser import (  # noqa: E402
    DEDICATED_BROWSER_PROFILE,
    BraveCdpSession,
)
from jarvis.toolbox.launch import (  # noqa: E402
    ApplicationEntry,
    ArgumentKind,
    LaunchKind,
    process_running,
)
from jarvis.toolbox.phase2_tools import (  # noqa: E402
    BrowserWorkspace,
    YouTubePlayInput,
    YouTubePlayTool,
    YouTubeSearchInput,
    YouTubeSearchTool,
)

QUERY = "RTX 5070"
POSITION = 1  # "the second video"


def main() -> int:
    if os.name != "nt":
        print("This runs Brave on Windows. Nothing to do here.")
        return 0

    if process_running(("brave.exe",)):
        print(
            "Brave is already running, so no debugging port can be opened.\n"
            "Close Brave and re-run."
        )
        return 1

    program_files = os.environ.get("ProgramFiles", r"C:\Program Files")
    entry = ApplicationEntry(
        app_id="brave_default_profile",
        display_name="Brave",
        kind=LaunchKind.EXECUTABLE,
        target=rf"{program_files}\BraveSoftware\Brave-Browser\Application\brave.exe",
        fixed_arguments=(f"--profile-directory={DEDICATED_BROWSER_PROFILE}",),
        argument_kind=ArgumentKind.NONE,
        verify_process_names=("brave.exe",),
    )

    workspace = BrowserWorkspace(session_factory=lambda: BraveCdpSession(entry))
    search_tool = YouTubeSearchTool(workspace)
    play_tool = YouTubePlayTool(workspace)

    # Two separate executors, so the two utterances are guaranteed to arrive on
    # different threads. This is the condition the product hits and the reason
    # the single-threaded lab could pass against a broken build.
    first_caller = ThreadPoolExecutor(max_workers=1, thread_name_prefix="jarvis-tool-a")
    second_caller = ThreadPoolExecutor(max_workers=1, thread_name_prefix="jarvis-tool-b")

    print("=" * 70)
    print("Phase 2 exit criterion, reached across two calling threads")
    print("=" * 70)
    print(f"  main thread            : {threading.get_ident()}")

    try:
        print(f'\n1. "search {QUERY.lower()} on youtube"')
        search = first_caller.submit(
            search_tool.run, ToolContext(), YouTubeSearchInput(query=QUERY)
        ).result()
        print(f"   caller thread        : {_thread_of(first_caller)}")
        print(f"   browser thread       : {workspace._browser_thread_id}")
        print(f"   {search.output.result_count} result(s):\n")
        for index, title in enumerate(search.output.titles[:5]):
            marker = "  <-- 'the second video'" if index == POSITION else ""
            print(f"     [{index}] {title[:58]}{marker}")

        if search.output.result_count <= POSITION:
            print("\nFAILED: fewer results than expected; nothing to play.")
            return 1

        print(f'\n2. "play the second video"  ->  position {POSITION}')
        play = second_caller.submit(
            play_tool.run, ToolContext(), YouTubePlayInput(position=POSITION)
        ).result()
        print(f"   caller thread        : {_thread_of(second_caller)}")
        print(f"   browser thread       : {workspace._browser_thread_id}")

        print(f"\n   clicked  : {play.output.clicked}")
        print(f"   verified : {play.output.verified}")
        print(f"   playing  : {play.output.video_id!r}")
        print(f"   detail   : {play.output.detail}")

        print("\n" + "=" * 70)
        if play.output.verified:
            print("EXIT CRITERION MET across two calling threads, confirmed by")
            print("reading the player back and matching the video id.")
        else:
            print("NOT VERIFIED. The click landed but playback was not confirmed.")
            print("Reported honestly rather than as success (FR-048).")
        print("=" * 70)
        print("\nThe Brave window is left open. Close it when you are done.")
        return 0 if play.output.verified else 2
    finally:
        first_caller.shutdown(wait=False)
        second_caller.shutdown(wait=False)


def _thread_of(executor: ThreadPoolExecutor) -> int:
    return executor.submit(threading.get_ident).result()


if __name__ == "__main__":
    raise SystemExit(main())
