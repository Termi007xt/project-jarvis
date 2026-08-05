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


def find_notepad(discovery: WindowDiscovery) -> str | None:
    """Its *reference*, found by process identity — never by title."""
    for window in discovery.list_windows():
        if window.process_name.casefold() == "notepad.exe":
            return window.ref
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
    ref = None
    deadline = time.monotonic() + 15.0
    while time.monotonic() < deadline:
        ref = find_notepad(discovery)
        if ref is not None:
            break
        time.sleep(0.25)

    if ref is None:
        print("\nFAILED: Notepad did not appear within 15s.")
        return 1

    before = next(w for w in discovery.list_windows() if w.ref == ref)
    print(f"\nopened Notepad, reference {ref}")
    print(f"  starting state  : {before.state.value}  {before.bounds}")

    failures = 0

    def check(make_report, expectation: str) -> None:
        """Act using the reference taken once, before any of this ran.

        This is the point of references. An earlier version of this lab re-found
        the window before every step, because positions went stale the moment
        anything moved — and the *product* could not do that, which is how
        "move my code editor to the left" moved the Jarvis window instead. The
        same reference is reused throughout here precisely to prove it survives
        the reordering each action causes.
        """
        nonlocal failures
        report = make_report(ref)
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
            handle = next(w for w in discovery.list_windows() if w.ref == current).handle
            ctypes.windll.user32.PostMessageW(handle, 0x0010, 0, 0)  # WM_CLOSE
            print("\nClosed the Notepad window this opened.")


if __name__ == "__main__":
    raise SystemExit(main())
