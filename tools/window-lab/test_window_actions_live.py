"""Do the window actions actually move a real window?

Phase 2 stage 4, P2-WIN-09. A research spike, outside the product runtime and
outside the security policy — the same status `tools/browser-lab/` holds.

Everything under `tests/` runs against an injected backend, deliberately
(ARCHITECTURE §11), which proves the guards, the positional addressing and the
verification logic and proves nothing about `SetForegroundWindow`. That gap is
not hypothetical: the browser labs passed for a day while the product was
broken, because the lab exercised a path the product did not take.

So this drives `Win32ActionBackend` against a window that really exists, and
checks each result the way `WindowController` does — by reading the window back.

**What this does to your machine:** opens Notepad, minimises, maximises,
restores and moves *that* window, then closes it. Your own windows are read but
never touched: the only handle acted on is the one Notepad reports.

Run:  .\.venv\Scripts\python.exe tools\window-lab\test_window_actions_live.py
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from jarvis.toolbox.launch import launch_argv  # noqa: E402
from jarvis.toolbox.window_actions import (  # noqa: E402
    Win32ActionBackend,
    WindowController,
    screen_work_area,
)
from jarvis.toolbox.windows import WindowDiscovery, WindowState  # noqa: E402

NOTEPAD = r"C:\Windows\System32\notepad.exe"


def find_notepad(discovery: WindowDiscovery) -> int | None:
    """Its *position*, found by process identity — never by title."""
    for window in discovery.list_windows():
        if window.process_name.casefold() == "notepad.exe":
            return window.index
    return None


def main() -> int:
    if os.name != "nt":
        print("This drives real Windows windows. Nothing to do here.")
        return 0

    discovery = WindowDiscovery()
    controller = WindowController(discovery=discovery, backend=Win32ActionBackend())

    print("=" * 68)
    print("Window actions against a real window")
    print("=" * 68)

    if find_notepad(discovery) is not None:
        print("\nNotepad is already open. Close it and re-run, so this only ever")
        print("acts on a window it opened itself.")
        return 1

    launch_argv((NOTEPAD,))
    position = None
    deadline = time.monotonic() + 15.0
    while time.monotonic() < deadline:
        position = find_notepad(discovery)
        if position is not None:
            break
        time.sleep(0.25)

    if position is None:
        print("\nFAILED: Notepad did not appear within 15s.")
        return 1

    before = discovery.list_windows()[position]
    print(f"\nopened Notepad at position {position}, handle {before.handle}")
    print(f"  starting state  : {before.state.value}  {before.bounds}")

    failures = 0

    def check(make_report, expectation: str) -> None:
        """Re-find the window, then act.

        Positions go stale the moment anything moves: `EnumWindows` returns
        z-order, so acting on a window changes where it sits in the list. That
        is not a lab artefact — it is the product's contract too, and the reason
        the tool loop re-reads before each step rather than reusing a position
        it was given three actions ago.
        """
        nonlocal failures
        current = find_notepad(discovery)
        if current is None:
            print(f"  [FAIL] {expectation:28} -> the window disappeared")
            failures += 1
            return
        report = make_report(current)
        mark = "OK  " if report.verified else "FAIL"
        if not report.verified:
            failures += 1
        print(f"  [{mark}] {expectation:28} -> {report.detail}")

    try:
        print("\nActions, each verified by reading the window back:\n")
        time.sleep(0.4)
        check(lambda p: controller.set_state(p, WindowState.MINIMISED), "minimise")
        time.sleep(0.4)
        check(lambda p: controller.set_state(p, WindowState.MAXIMISED), "maximise")
        time.sleep(0.4)
        check(lambda p: controller.set_state(p, WindowState.NORMAL), "restore")
        time.sleep(0.4)
        check(controller.activate, "activate")

        # Snap to the left half of the work area, which is the shape "put this
        # on the left" will use once the tool exists.
        left, top, width, height = screen_work_area()
        time.sleep(0.4)
        check(
            lambda p: controller.move_resize(p, left, top, width // 2, height),
            "move to the left half",
        )

        print("\n" + "=" * 68)
        if failures == 0:
            print("PASS: every action took effect and was confirmed by re-reading")
            print("the window. The verification is not vacuous.")
        else:
            print(f"{failures} action(s) reported unverified. That is the honest")
            print("outcome, not a crash — but check whether the request is one")
            print("Windows actually honours before shipping the tool.")
        print("=" * 68)
        return 0 if failures == 0 else 2
    finally:
        # Close the window we opened. WM_CLOSE, so Notepad decides — the same
        # request clicking its X makes.
        import ctypes

        current = find_notepad(discovery)
        if current is not None:
            handle = discovery.list_windows()[current].handle
            ctypes.windll.user32.PostMessageW(handle, 0x0010, 0, 0)  # WM_CLOSE
            print("\nClosed the Notepad window this opened.")


if __name__ == "__main__":
    raise SystemExit(main())
