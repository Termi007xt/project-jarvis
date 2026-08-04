"""The Phase 2 exit criterion, against the real YouTube.

    "search rtx 5070 on youtube"     -> youtube.search
    "play the second video"          -> youtube.play(1)

Everything under `tests/` runs headless against fakes, deliberately
(ARCHITECTURE §11), which means the suite proves the *logic* and proves nothing
about the real page. This runs the real thing, through the real production code
path: `BraveCdpSession` -> `PlaywrightPageDriver` -> `YouTubeAdapter`.

**What this does to your machine:** opens Brave on the dedicated Jarvis profile,
searches YouTube, and plays a video. Sound will come out. Close Brave first, or
the launch is handed to the running instance and no debugging port opens.

Run:  .\.venv\Scripts\python.exe tools\browser-lab\test_exit_criterion.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

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
from jarvis.toolbox.youtube import YouTubeAdapter  # noqa: E402

QUERY = "RTX 5070"
POSITION = 1  # "the second video"


def main() -> int:
    if os.name != "nt":
        print("This runs Brave on Windows. Nothing to do here.")
        return 0

    if process_running(("brave.exe",)):
        print(
            "Brave is already running. A second brave.exe hands its command\n"
            "line to the existing instance and exits, so no debugging port\n"
            "opens. Close Brave and re-run."
        )
        return 1

    program_files = os.environ.get("ProgramFiles", r"C:\Program Files")
    entry = ApplicationEntry(
        app_id="brave_jarvis_profile",
        display_name="Brave (Jarvis profile)",
        kind=LaunchKind.EXECUTABLE,
        target=rf"{program_files}\BraveSoftware\Brave-Browser\Application\brave.exe",
        fixed_arguments=(f"--profile-directory={DEDICATED_BROWSER_PROFILE}",),
        argument_kind=ArgumentKind.NONE,
        verify_process_names=("brave.exe",),
    )

    print("=" * 70)
    print("Phase 2 exit criterion, against the real YouTube")
    print("=" * 70)

    with BraveCdpSession(entry) as session:
        adapter = YouTubeAdapter(page=session.page())

        print(f'\n1. "search {QUERY.lower()} on youtube"')
        results = adapter.search(QUERY)
        print(f"   {len(results)} result(s). Titles are data, positions are handles:\n")
        for item in results.items[:5]:
            marker = "  <-- 'the second video'" if item.index == POSITION else ""
            print(f"     [{item.index}] {item.label[:58]}{marker}")

        if len(results) <= POSITION:
            print("\nFAILED: fewer results than expected; nothing to play.")
            return 1

        print(f'\n2. "play the second video"  ->  select({POSITION})')
        # The adapter polls the player itself, bounded, so a video that takes a
        # moment to start is not reported as unverified.
        report = adapter.play(POSITION)

        print(f"\n   clicked  : {report.clicked}")
        print(f"   verified : {report.verified}")
        print(f"   expected : {report.expected_video_id!r}")
        print(f"   playing  : {report.video_id!r}")
        print(f"   detail   : {report.detail}")

        print("\n" + "=" * 70)
        if report.verified:
            print("EXIT CRITERION MET: the second video is playing, confirmed by")
            print("reading the player back and matching the video id.")
        else:
            print("NOT VERIFIED. The click landed but playback was not confirmed.")
            print("This is reported honestly rather than as success (FR-048).")
        print("=" * 70)
        print("\nThe Brave window is left open. Close it when you are done.")

        return 0 if report.verified else 2


if __name__ == "__main__":
    raise SystemExit(main())
