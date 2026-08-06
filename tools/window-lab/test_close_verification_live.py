"""Is "not in the window list" the same as "closed"? (P2-APP-01)

A research spike, outside the product runtime.

Reported 2026-08-06 by the owner: a music tab was playing in Microsoft Edge,
which asks for confirmation before it will close. Jarvis said *"Microsoft Edge
has been closed"* and Edge was still there — a **verified** success that was
false. Notepad, in the same session, closed correctly.

`WindowController.close` decides by asking whether the window is still in
`WindowDiscovery.list_windows(include_dialogs=True)`. That list is not a list of
windows that exist. It is the list of windows a *person* would call open, which
is a different thing on purpose: it drops the invisible, the untitled, the
DWM-cloaked, the tool windows and the zero-area ghosts, because that filter is
what turned a listing of eleven windows into the four the owner actually had.

An application that answers `WM_CLOSE` by hiding its window and then asking a
question is therefore indistinguishable, to that list, from one that closed.
Chromium does precisely this: `BrowserView::CanClose()` hides the frame while
the close is pending.

Two experiments.

**A** — deterministic, needs nothing open. Take a real window, and have the
close request *hide* it rather than destroy it. That is the Chromium behaviour
in isolation, with everything else real. Predicts: `closed`, `verified=True`,
about a window that is still there.

**B** — needs a Chromium window open. Post a real `WM_CLOSE` and watch every
attribute the filter tests, 4x a second, to see which one drops it and when.

**What this does to your machine:** experiment A opens Character Map and closes
it again. Experiment B asks the browser you name to close, exactly as clicking
its X does, and never forces it.

Run:  .\.venv\Scripts\python.exe tools\window-lab\test_close_verification_live.py
      .\.venv\Scripts\python.exe tools\window-lab\test_close_verification_live.py msedge
"""

from __future__ import annotations

import ctypes
import os
import sys
import time
from ctypes import wintypes
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from jarvis.toolbox.launch import launch_argv  # noqa: E402
from jarvis.toolbox.window_actions import (  # noqa: E402
    Win32ActionBackend,
    WindowController,
)
from jarvis.toolbox.windows import WindowDiscovery, _is_cloaked  # noqa: E402

_SW_HIDE = 0
_SW_SHOW = 5
_WM_CLOSE = 0x0010


def _user32():
    return ctypes.windll.user32  # type: ignore[attr-defined]


def _title(hwnd: int) -> str:
    length = _user32().GetWindowTextLengthW(hwnd)
    if length <= 0:
        return ""
    buffer = ctypes.create_unicode_buffer(length + 1)
    _user32().GetWindowTextW(hwnd, buffer, length + 1)
    return buffer.value


def _class_name(hwnd: int) -> str:
    buffer = ctypes.create_unicode_buffer(256)
    _user32().GetClassNameW(hwnd, buffer, 256)
    return buffer.value


def _attributes(hwnd: int) -> dict[str, object]:
    """Every property `is_user_facing` tests, plus why it would matter."""
    user32 = _user32()
    rect = wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(rect))
    return {
        "is_window": bool(user32.IsWindow(hwnd)),
        "visible": bool(user32.IsWindowVisible(hwnd)),
        "title_len": int(user32.GetWindowTextLengthW(hwnd)),
        "cloaked": _is_cloaked(hwnd),
        "tool_window": bool(user32.GetWindowLongW(hwnd, -20) & 0x00000080),
        "disabled": bool(user32.GetWindowLongW(hwnd, -16) & 0x08000000),
        "area": (rect.right - rect.left) * (rect.bottom - rect.top),
    }


def _why_dropped(attributes: dict[str, object]) -> str:
    if not attributes["is_window"]:
        return "the window is destroyed — genuinely gone"
    reasons = []
    if not attributes["visible"]:
        reasons.append("not visible")
    if not attributes["title_len"]:
        reasons.append("no title")
    if attributes["cloaked"]:
        reasons.append("DWM-cloaked")
    if attributes["tool_window"]:
        reasons.append("tool window")
    if not attributes["area"]:
        reasons.append("no area")
    return ", ".join(reasons) if reasons else "-"


class HidesInsteadOfClosing:
    """An application that answers WM_CLOSE by hiding and asking a question.

    Everything else in the run is real: real discovery, real Win32 enumeration,
    a real window. Only the application's *response* is substituted, because
    that response is the whole thing under test.
    """

    def __init__(self) -> None:
        self.hidden: list[int] = []

    def activate(self, handle: int) -> None: ...

    def set_state(self, handle: int, state: str) -> None: ...

    def move_resize(self, handle, x, y, width, height) -> None: ...

    def terminate(self, pid: int) -> None:
        raise AssertionError("a close must never terminate anything")

    def foreground_handle(self) -> int:
        return 0

    def request_close(self, handle: int) -> None:
        _user32().ShowWindow(handle, _SW_HIDE)
        self.hidden.append(handle)


def _find(discovery: WindowDiscovery, process_fragment: str, timeout: float = 10.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        for window in discovery.list_windows(include_dialogs=True):
            if process_fragment.casefold() in window.process_name.casefold():
                return window
        time.sleep(0.25)
    return None


# =========================================================================
# A — an application that hides rather than closes
# =========================================================================
def experiment_a() -> int:
    print("=" * 74)
    print("A. A window that was hidden, not closed. What does Jarvis report?")
    print("=" * 74)

    launch_argv([r"C:\Windows\System32\charmap.exe"])
    discovery = WindowDiscovery()
    window = _find(discovery, "charmap")
    if window is None:
        print("SKIP: Character Map did not open, so there is nothing to close.")
        return 0

    handle = window.handle
    print(f"\nopened {window.process_name}, hwnd={handle:#010x}, {window.title!r}")

    backend = HidesInsteadOfClosing()
    controller = WindowController(
        discovery=discovery, backend=backend, close_poll_seconds=0.5
    )

    try:
        report = controller.close(window.ref)
        after = _attributes(handle)

        print(f"\n  Jarvis reports : outcome={report.outcome.value} "
              f"verified={report.verified}")
        print(f"  and says       : {report.detail}")
        print(f"\n  the window     : exists={after['is_window']} "
              f"visible={after['visible']} title={_title(handle)!r}")
        print(f"  dropped from the list because: {_why_dropped(after)}")

        reproduced = (
            report.verified
            and report.outcome.value == "closed"
            and after["is_window"]
        )
        print()
        if reproduced:
            print("  REPRODUCED: reported closed, and verified, about a window")
            print("              that is still there. The check asks whether the")
            print("              window is still *presentable*, not whether it")
            print("              still *exists*.")
            return 1
        print("  NOT REPRODUCED: the hidden window was not reported as closed.")
        return 0
    finally:
        _user32().ShowWindow(handle, _SW_SHOW)
        _user32().PostMessageW(handle, _WM_CLOSE, 0, 0)
        time.sleep(0.5)
        print(f"\n  cleaned up: Character Map "
              f"{'closed' if not _user32().IsWindow(handle) else 'left open'}")


# =========================================================================
# B — a real browser, a real WM_CLOSE
# =========================================================================
def experiment_b(fragment: str) -> int:
    print()
    print("=" * 74)
    print(f"B. A real WM_CLOSE to {fragment}, watched attribute by attribute")
    print("=" * 74)

    discovery = WindowDiscovery()
    window = _find(discovery, fragment, timeout=1.0)
    if window is None:
        print(f"\nSKIP: no visible {fragment} window is open.")
        print("      Open it, put it in the state that asks before closing")
        print("      (a page that prompts, or several tabs), and run again.")
        return 0

    handle, pid = window.handle, window.pid
    print(f"\ntarget: hwnd={handle:#010x} pid={pid} class={_class_name(handle)}")
    print(f"        {window.title!r}")

    before = {
        entry.handle for entry in discovery.list_windows(include_dialogs=True)
    }
    Win32ActionBackend().request_close(handle)
    print("\nposted WM_CLOSE. Watching for 12 seconds:\n")
    print("   t     exists vis title cloak tool  in-list   dropped because")
    print("  " + "-" * 68)

    verdict_at_one_second = None
    for tick in range(48):
        time.sleep(0.25)
        elapsed = (tick + 1) * 0.25
        attributes = _attributes(handle)
        listed = discovery.list_windows(include_dialogs=True)
        in_list = any(entry.handle == handle for entry in listed)

        if abs(elapsed - 1.0) < 0.01:
            verdict_at_one_second = in_list

        if tick % 2 == 0 or not in_list:
            print(
                f"  {elapsed:5.2f}s  {str(attributes['is_window'])[0]:^6} "
                f"{str(attributes['visible'])[0]:^3} {attributes['title_len']:^5} "
                f"{str(attributes['cloaked'])[0]:^5} {str(attributes['tool_window'])[0]:^4} "
                f"{str(in_list):^9} {_why_dropped(attributes)}"
            )

        new_windows = [
            entry
            for entry in listed
            if entry.handle not in before and entry.pid == pid
        ]
        if new_windows:
            for entry in new_windows:
                print(
                    f"         NEW WINDOW hwnd={entry.handle:#010x} "
                    f"owned={entry.owned} class={_class_name(entry.handle)} "
                    f"{entry.title[:40]!r}"
                )
            before |= {entry.handle for entry in new_windows}

        if not attributes["is_window"]:
            print(f"\n  the window was destroyed at {elapsed:.2f}s — a real close.")
            break

    print()
    still_exists = bool(_user32().IsWindow(handle))
    print(f"  after 12s: the window {'still exists' if still_exists else 'is gone'}.")
    if verdict_at_one_second is not None:
        print(f"  at the 1s mark Jarvis would have said: "
              f"{'still open' if verdict_at_one_second else 'CLOSED'}")
    if still_exists and verdict_at_one_second is False:
        print("\n  REPRODUCED against the real browser.")
        return 1
    return 0


def main() -> int:
    if os.name != "nt":
        print("Windows only. Nothing to do here.")
        return 0

    reproduced = experiment_a()
    reproduced += experiment_b(sys.argv[1] if len(sys.argv) > 1 else "msedge")

    print()
    print("=" * 74)
    print(f"{'REPRODUCED' if reproduced else 'not reproduced'} "
          f"in {reproduced} of the experiments that ran")
    print("=" * 74)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
