"""Does an application with unsaved work actually stop the close?

Phase 2 stage 4, P2-APP-01 / AT-004. A research spike, outside the product
runtime and outside the security policy.

`tests/unit/test_close_before_force.py` proves the *logic* against an injected
backend: a new owned window from the same process means the application is
asking something, so stop. It proves nothing about whether Notepad's save prompt
is actually an owned window, and that assumption is the whole control. If real
prompts are top-level rather than owned, the unit tests stay green while the
product force-closes past somebody's unsaved work — which is the exact shape of
failure this project keeps producing.

So this makes a real document dirty and asks Notepad to close.

**It does not currently get that far, and the reason is worth reading.** Windows
only lets the process that already owns the foreground give it away, so a script
run from a terminal cannot bring Notepad forward, and a keystroke sent with
`SendInput` lands in the terminal instead. The document never becomes unsaved,
so the run ends `INCONCLUSIVE` (exit 3) rather than claiming a result. AT-004
therefore still needs a human: type into Notepad, then ask Jarvis to close it.

That dead end was worth hitting anyway. It is how `activate` was found reporting
`verified` for a window that never took the foreground — it checked only that
the window was no longer minimised, which it usually was not. Now it asks
Windows which window actually has the foreground. Same vacuous-verification
shape as `app.open` reporting success from a browser that was already running,
and it would not have surfaced from a test using an injected backend, because
the injected one always obeys.

**What this does to your machine:** opens Notepad, types one character into it,
asks it to close, and dismisses the resulting "save changes?" prompt by choosing
**Don't Save** — on a document that only ever contained that one character. It
refuses to run if Notepad is already open, so it can never touch a document of
yours. Nothing is force-closed.

Run:  .\.venv\Scripts\python.exe tools\window-lab\test_close_before_force_live.py
"""

from __future__ import annotations

import ctypes
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from jarvis.toolbox.launch import launch_argv  # noqa: E402
from jarvis.toolbox.window_actions import (  # noqa: E402
    CloseOutcome,
    Win32ActionBackend,
    WindowController,
)
from jarvis.toolbox.windows import WindowDiscovery  # noqa: E402

NOTEPAD = r"C:\Windows\System32\notepad.exe"


def _type_a_character(user32) -> None:
    """Press and release one key, through the real input queue.

    `SendInput` rather than posting a message to a child control: the Windows 11
    Notepad has no "Edit" window to post to, and a keystroke that lands nowhere
    is indistinguishable from one that landed and did nothing.
    """
    import ctypes
    from ctypes import wintypes

    class KEYBDINPUT(ctypes.Structure):
        _fields_ = [
            ("wVk", wintypes.WORD),
            ("wScan", wintypes.WORD),
            ("dwFlags", wintypes.DWORD),
            ("time", wintypes.DWORD),
            ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
        ]

    class INPUT(ctypes.Structure):
        class _U(ctypes.Union):
            _fields_ = [("ki", KEYBDINPUT)]

        _anonymous_ = ("u",)
        _fields_ = [("type", wintypes.DWORD), ("u", _U)]

    def event(flags: int) -> INPUT:
        item = INPUT()
        item.type = 1  # INPUT_KEYBOARD
        item.ki = KEYBDINPUT(0x58, 0, flags, 0, None)  # 'X'
        return item

    events = (INPUT * 2)(event(0), event(0x0002))  # down, KEYEVENTF_KEYUP
    user32.SendInput(2, ctypes.byref(events), ctypes.sizeof(INPUT))


def _title_of(user32, handle: int) -> str:
    """The window's own title.

    Read only to confirm the *lab's* precondition — that typing actually
    reached the document. The product never decides anything from a title.
    Compared for change rather than searched for a particular marker, because
    which marker Notepad uses for a modified document is a detail of the
    Notepad build and not something worth encoding a guess about.
    """
    import ctypes

    length = user32.GetWindowTextLengthW(handle)
    buffer = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(handle, buffer, length + 1)
    return buffer.value


def _shut_notepad(user32, handle: int, discovery: WindowDiscovery) -> None:
    """Close the window this script opened, answering any prompt with Don't Save."""
    user32.PostMessageW(handle, 0x0010, 0, 0)  # WM_CLOSE
    for _ in range(4):
        time.sleep(0.6)
        dialog = user32.GetLastActivePopup(handle)
        if dialog and dialog != handle:
            user32.PostMessageW(dialog, 0x0111, 7, 0)  # WM_COMMAND, IDNO
    time.sleep(0.5)
    if notepad_ref(discovery) is not None:
        print("\nNote: Notepad is still open. Close it by hand — this script")
        print("deliberately has no way to force it.")
    else:
        print("\nCleaned up: the document this created was discarded unsaved.")


def notepad_ref(discovery: WindowDiscovery) -> str | None:
    for window in discovery.list_windows():
        if window.process_name.casefold() == "notepad.exe":
            return window.ref
    return None


def main() -> int:
    if os.name != "nt":
        print("This drives real Windows windows. Nothing to do here.")
        return 0

    discovery = WindowDiscovery()
    controller = WindowController(
        discovery=discovery, backend=Win32ActionBackend(), close_poll_seconds=1.5
    )
    user32 = ctypes.windll.user32

    if notepad_ref(discovery) is not None:
        print("Notepad is already open. Close it and re-run, so this can only")
        print("ever act on a document it created itself.")
        return 1

    print("=" * 68)
    print("Close-before-force against a real unsaved document (AT-004)")
    print("=" * 68)

    launch_argv((NOTEPAD,))
    ref = None
    deadline = time.monotonic() + 15.0
    while time.monotonic() < deadline:
        ref = notepad_ref(discovery)
        if ref is not None:
            break
        time.sleep(0.25)
    if ref is None:
        print("\nFAILED: Notepad did not appear.")
        return 1

    window = next(w for w in discovery.list_windows() if w.ref == ref)
    print(f"\nopened Notepad, reference {ref}")

    # Make it dirty, then *check that it worked*. The first version of this
    # posted WM_CHAR to a child window of class "Edit" — which is how Notepad
    # was built for thirty years and is not how the Windows 11 one is. The
    # keystroke went nowhere, Notepad closed cleanly because it had nothing to
    # save, and the script reported that as the product failing to notice a
    # prompt. A lab that cannot establish its own precondition must say so
    # rather than blame what it was pointed at.
    controller.activate(ref)
    time.sleep(0.8)
    before_title = _title_of(user32, window.handle)
    _type_a_character(user32)
    time.sleep(1.5)
    after_title = _title_of(user32, window.handle)
    print(f"  title before typing : {before_title!r}")
    print(f"  title after typing  : {after_title!r}")

    if after_title == before_title:
        print("\n  INCONCLUSIVE: could not make the document unsaved.")
        print("  Notepad's title shows no modified marker, so closing it would")
        print("  prove nothing about the save-prompt pause. This is a limit of")
        print("  the lab, not a result about the product.")
        _shut_notepad(user32, window.handle, discovery)
        return 3
    print("  typed one character; the title now shows unsaved changes")

    failures = 0
    try:
        print("\n1. Asking it to close, the way clicking the X does:\n")
        report = controller.close(ref)
        print(f"   outcome  : {report.outcome.value}")
        print(f"   verified : {report.verified}")
        print(f"   detail   : {report.detail}")

        if report.outcome is CloseOutcome.WAITING_ON_USER:
            print("\n   PASS: the prompt was noticed and the close stopped there.")
        else:
            failures += 1
            print(
                "\n   FAIL: expected the save prompt to pause the close. If the"
                "\n   outcome was 'closed', Notepad discarded the document without"
                "\n   asking — or the prompt is not an owned window, and the"
                "\n   detection needs to change."
            )

        print("\n2. Confirming nothing escalated:\n")
        still_there = notepad_ref(discovery) is not None
        print(f"   Notepad still running: {still_there}")
        if not still_there:
            failures += 1
            print("   FAIL: the process is gone. Nothing here may force-close.")
        else:
            print("   PASS: still there. A refused close stays refused.")

        print("\n" + "=" * 68)
        print("PASS" if failures == 0 else f"{failures} check(s) failed")
        print("=" * 68)
        return 0 if failures == 0 else 2
    finally:
        # Answer the prompt the way a person would: Don't Save, on a document
        # that only ever contained one character.
        _shut_notepad(user32, window.handle, discovery)


if __name__ == "__main__":
    raise SystemExit(main())
