"""FR-078 / AT-008: the user touching the mouse or keyboard pauses automation.

Phase 2 stage 2, and built before any tool can move the pointer, because a
pause that is added afterwards has to be threaded back through every tool that
was written without it.

The whole difficulty is in one distinction. Windows reports *the last input*,
and automation's own synthetic clicks and keystrokes are input. A watcher that
does not separate the two either never fires — because our own typing keeps
refreshing the timestamp — or fires constantly, pausing the automation on its
own actions. Both failures look like "the pause does not work".

The other half is honesty. On a machine where this cannot be observed at all,
the watcher must say so rather than report a confident "the user did nothing",
because "no interruption detected" and "interruption cannot be detected" are
very different facts to run automation on (ADR-0010).
"""

from __future__ import annotations

import pytest

from jarvis.toolbox.desktop_input import UserInputWatcher


class FakeDesktop:
    """A controllable stand-in for the Win32 last-input tick and the clock."""

    def __init__(self) -> None:
        self.now_ms = 100_000
        self.last_input_ms = 100_000
        self.available = True

    # -- what the watcher consumes -------------------------------------
    def tick(self) -> int:
        return self.now_ms

    def last_input(self) -> int | None:
        return self.last_input_ms if self.available else None

    # -- what a test does ----------------------------------------------
    def advance(self, ms: int) -> None:
        self.now_ms += ms

    def user_touches_something(self) -> None:
        self.advance(50)
        self.last_input_ms = self.now_ms


@pytest.fixture
def desktop() -> FakeDesktop:
    return FakeDesktop()


@pytest.fixture
def watcher(desktop: FakeDesktop) -> UserInputWatcher:
    return UserInputWatcher(tick=desktop.tick, last_input_tick=desktop.last_input)


def test_a_quiet_desktop_is_not_an_interruption(watcher, desktop) -> None:
    watcher.arm()
    desktop.advance(5_000)
    assert watcher.user_intervened() is False


def test_the_user_touching_the_mouse_is_an_interruption(watcher, desktop) -> None:
    watcher.arm()
    desktop.user_touches_something()
    assert watcher.user_intervened() is True


def test_our_own_synthetic_input_is_not_an_interruption(watcher, desktop) -> None:
    """The defect this class exists to avoid.

    Automation clicks. Windows records a new last-input time. A naive watcher
    reads that as the user intervening and pauses the task on its own action —
    so automation stops the instant it starts, and the cause is invisible.
    """
    watcher.arm()

    # We act, and tell the watcher we did.
    desktop.advance(50)
    desktop.last_input_ms = desktop.now_ms
    watcher.note_synthetic_input()

    assert watcher.user_intervened() is False


def test_the_user_interrupting_after_our_own_input_still_counts(watcher, desktop) -> None:
    """The dangerous inverse: suppressing our own input must not deafen us."""
    watcher.arm()

    desktop.advance(50)
    desktop.last_input_ms = desktop.now_ms
    watcher.note_synthetic_input()

    desktop.user_touches_something()
    assert watcher.user_intervened() is True


def test_rearming_forgets_an_earlier_interruption(watcher, desktop) -> None:
    """A resumed task starts from the moment it resumed, not from the past."""
    watcher.arm()
    desktop.user_touches_something()
    assert watcher.user_intervened() is True

    watcher.arm()
    assert watcher.user_intervened() is False


def test_asking_before_arming_is_an_error(watcher) -> None:
    """An unarmed watcher returning False would read as "the user did nothing"."""
    with pytest.raises(RuntimeError):
        watcher.user_intervened()


# -- honesty when it cannot be observed ------------------------------------
def test_a_watcher_that_cannot_observe_input_says_so(desktop) -> None:
    desktop.available = False
    watcher = UserInputWatcher(tick=desktop.tick, last_input_tick=desktop.last_input)

    assert watcher.available is False
    assert watcher.unavailable_reason()


def test_an_unobservable_desktop_never_reports_a_quiet_one(desktop) -> None:
    """ADR-0010: "not detected" must not be dressed up as "did not happen".

    Automation that cannot be interrupted is a different product from automation
    that was not interrupted. The caller has to be able to tell, so this raises
    rather than returning a comfortable False.
    """
    desktop.available = False
    watcher = UserInputWatcher(tick=desktop.tick, last_input_tick=desktop.last_input)
    watcher.arm()

    with pytest.raises(RuntimeError) as raised:
        watcher.user_intervened()
    assert "cannot" in str(raised.value).lower()


def test_the_real_watcher_reports_its_own_availability_truthfully() -> None:
    """The default construction must not claim a capability it lacks.

    On Windows this reads the real Win32 last-input tick; everywhere else it is
    unavailable, and CI runs on Linux, so this asserts the honest branch exists
    rather than asserting a platform.
    """
    import os

    watcher = UserInputWatcher()
    if os.name == "nt":
        assert watcher.available is True
        assert watcher.unavailable_reason() is None
    else:
        assert watcher.available is False
        assert watcher.unavailable_reason()
