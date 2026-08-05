"""Naming a window so that the name still means it when the action runs.

Three defects from real use on 2026-08-05, all one root cause plus noise.

    Sir: move my code editor anti-gravity to the left half of the screen
    Jarvis: Got it — your Antigravity IDE window is now snapped to the left half.
    [confirmed by a tool]

It moved the Jarvis window.

**Why.** `window.arrange` took a *position in the last listing*. The model reads
that listing, maps "my IDE" to position 4, and calls the tool — but a position is
an index into a list that reorders every time anything moves, so by the time the
call arrives position 4 is a different window. The tool then verified against the
window it actually moved and reported success, truthfully, about the wrong thing.

Positional addressing is right for *"play the second video"*: the **user** names
the position, and the control it buys is that a page cannot rename itself into
being the second video. It is wrong for *"move my IDE"*, where the user names the
window and the number is only the model's guess at a moving target. The guess is
what breaks.

**The fix is a reference, not an index.** A listing mints an opaque token per
window, bound to its handle. The token means the same window however the desktop
reorders, and it cannot be forged: a model that has not listed a window has no
token for it, and a window cannot mint one for itself by changing its title. The
security property positions were protecting — the model may not name a window by
supplying raw text or a raw handle — is kept exactly, and the staleness goes.

It also removes the instruction that produced the *second* defect. Telling the
model "call window.list again before each arrange" made it announce a re-check
instead of doing one:

    Sir: Put my notepad on the left half of the screen.
    Jarvis: Let me take another look at your current windows...
    [from the local model — no tool ran]

With stable references there is nothing to re-check, so there is nothing to
narrate.
"""

from __future__ import annotations

import pytest

from jarvis.toolbox.sensitive import SensitiveTargets
from jarvis.toolbox.window_actions import WindowController
from jarvis.toolbox.windows import WindowDiscovery, WindowState


class FakeBackend:
    def __init__(self, windows):
        self.windows = windows

    def is_available(self):
        return True

    def unavailable_reason(self):
        return None

    def list_windows(self):
        return [dict(window) for window in self.windows]


class FakeActions:
    def __init__(self):
        self.calls = []

    def activate(self, handle):
        self.calls.append(("activate", handle))

    def set_state(self, handle, state):
        self.calls.append(("set_state", handle, state))

    def move_resize(self, handle, x, y, width, height):
        self.calls.append(("move_resize", handle, x, y, width, height))


def _window(**overrides):
    base = {
        "handle": 1001,
        "title": "YouTube — Brave",
        "process_name": "brave.exe",
        "pid": 1,
        "bounds": (0, 0, 800, 600),
        "state": "normal",
        "monitor": 0,
    }
    base.update(overrides)
    return base


# =========================================================================
# A reference survives the desktop reordering underneath it
# =========================================================================
def test_a_reference_still_means_the_same_window_after_everything_moves() -> None:
    """The defect, stated exactly.

    Between the listing and the action, the desktop reorders — which is not an
    edge case, it is what happens every time anything is clicked or moved.
    """
    ide = _window(handle=7, process_name="ide.exe", title="project-jarvis - IDE")
    backend = FakeBackend([_window(handle=1), ide, _window(handle=3)])
    discovery = WindowDiscovery(backend=backend)

    listed = discovery.list_windows()
    ide_ref = next(w.ref for w in listed if w.process_name == "ide.exe")
    assert listed[1].index == 1  # the IDE is at position 1 right now

    # The user clicks something; z-order changes completely.
    backend.windows = [_window(handle=3), _window(handle=1), ide]

    actions = FakeActions()
    controller = WindowController(
        discovery=discovery, backend=actions, secure_desktop=lambda: False
    )
    controller.activate(ide_ref)

    assert actions.calls == [("activate", 7)], (
        "the reference resolved to a different window after the desktop "
        "reordered — this is the bug that moved the Jarvis window instead of "
        "the IDE"
    )


def test_the_same_window_keeps_the_same_reference_across_listings() -> None:
    """Otherwise the model is handed a new name for the same thing each time."""
    discovery = WindowDiscovery(backend=FakeBackend([_window(handle=42)]))

    first = discovery.list_windows()[0].ref
    second = discovery.list_windows()[0].ref

    assert first == second


def test_different_windows_never_share_a_reference() -> None:
    discovery = WindowDiscovery(
        backend=FakeBackend([_window(handle=1), _window(handle=2)])
    )
    refs = [window.ref for window in discovery.list_windows()]
    assert len(set(refs)) == 2


def test_a_reference_that_was_never_listed_is_refused() -> None:
    """Unforgeable. A window cannot mint a token for itself by any means, and a
    model that has not listed a window has no way to name one."""
    discovery = WindowDiscovery(backend=FakeBackend([_window(handle=1)]))
    discovery.list_windows()
    actions = FakeActions()
    controller = WindowController(
        discovery=discovery, backend=actions, secure_desktop=lambda: False
    )

    with pytest.raises(KeyError) as raised:
        controller.activate("win-not-a-real-reference")

    assert not actions.calls
    assert "window.list" in str(raised.value), "say how to get a valid one"


def test_a_reference_to_a_closed_window_is_refused_clearly() -> None:
    """Closed between listing and acting. Common, and must not hit something else."""
    backend = FakeBackend([_window(handle=1), _window(handle=2)])
    discovery = WindowDiscovery(backend=backend)
    gone = discovery.list_windows()[0].ref

    backend.windows = [_window(handle=2)]  # the first window was closed

    actions = FakeActions()
    controller = WindowController(
        discovery=discovery, backend=actions, secure_desktop=lambda: False
    )
    with pytest.raises(KeyError) as raised:
        controller.activate(gone)

    assert not actions.calls, "acted on whatever had taken its place"
    assert "closed" in str(raised.value).casefold()


def test_the_reference_is_not_the_raw_handle() -> None:
    """The model never receives an OS handle, and never supplies one.

    A handle is a number it could plausibly guess or increment into another
    window. A token exists only because Jarvis listed the window.
    """
    discovery = WindowDiscovery(backend=FakeBackend([_window(handle=1001)]))
    ref = discovery.list_windows()[0].ref
    assert "1001" not in ref


def test_a_sensitive_window_is_still_refused_by_reference() -> None:
    """The guard cannot be walked around by using the new addressing."""
    from jarvis.toolbox.window_actions import SensitiveWindowRefused

    discovery = WindowDiscovery(
        backend=FakeBackend([_window(process_name="1Password.exe")]),
        sensitive=SensitiveTargets(),
    )
    ref = discovery.list_windows()[0].ref
    actions = FakeActions()
    controller = WindowController(
        discovery=discovery, backend=actions, secure_desktop=lambda: False
    )

    with pytest.raises(SensitiveWindowRefused):
        controller.set_state(ref, WindowState.MINIMISED)
    assert not actions.calls


# =========================================================================
# The listing is windows a person would recognise
# =========================================================================
def test_the_listing_is_filtered_to_windows_a_person_would_recognise() -> None:
    """Reported 2026-08-05: eleven windows listed, four of them real.

    "Windows Input Experience", "Program Manager" and an off-screen
    ApplicationFrameHost ghost are not things the owner thinks of as open
    windows, and listing them makes the model choose between eleven candidates
    when there were four. The filter runs in the backend, against Win32
    attributes rather than against titles — a title-based skip list would be
    both wrong and defeatable.
    """
    from jarvis.toolbox.windows import is_user_facing

    assert is_user_facing(title="project-jarvis - IDE", cloaked=False, tool_window=False,
                          owned=False, bounds=(0, 0, 1920, 1080))
    # No title at all
    assert not is_user_facing(title="", cloaked=False, tool_window=False,
                              owned=False, bounds=(0, 0, 800, 600))
    # DWM-cloaked: the UWP ghost windows ApplicationFrameHost leaves behind
    assert not is_user_facing(title="Settings", cloaked=True, tool_window=False,
                              owned=False, bounds=(0, 0, 800, 600))
    # A tool window is chrome, not a window in its own right
    assert not is_user_facing(title="Toolbar", cloaked=False, tool_window=True,
                              owned=False, bounds=(0, 0, 800, 600))
    # Zero-sized, like the USBLCD window at (-80, -80, 0, 0)
    assert not is_user_facing(title="XProg", cloaked=False, tool_window=False,
                              owned=False, bounds=(-80, -80, 0, 0))


def test_the_shell_desktop_is_not_a_window() -> None:
    """explorer.exe's "Program Manager" is the desktop itself."""
    from jarvis.toolbox.windows import is_shell_window

    assert is_shell_window("Program Manager", "explorer.exe")
    assert is_shell_window("Windows Input Experience", "TextInputHost.exe")
    assert not is_shell_window("Downloads", "explorer.exe"), (
        "an ordinary File Explorer window is a real window"
    )
