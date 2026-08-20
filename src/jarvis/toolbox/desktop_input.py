"""Noticing that the user has taken the desktop back (FR-078, AT-008).

Phase 2 stage 2. Written before any tool can move the pointer, because a pause
added afterwards has to be threaded back through every tool that was built
without one.

**The distinction the whole class exists for.** Windows reports *the last input*
through `GetLastInputInfo`, and automation's own synthetic clicks and keystrokes
are input. A watcher that does not separate ours from the user's fails in one of
two ways, and both look identical from outside — it either pauses the task on its
own first click, or never fires at all because our own activity keeps refreshing
the timestamp. So callers tell this watcher when *they* acted, and anything newer
than that is the user.

**Honesty where it cannot observe.** On a platform without the Win32 call, this
does not quietly answer "the user did nothing". Automation that *cannot* be
interrupted is a different product from automation that *was not* interrupted,
and the caller has to be able to tell the difference (ADR-0010, FR-078). So the
watcher reports itself unavailable and refuses to answer, rather than returning a
comfortable `False` that would let un-interruptible automation run believing it
was safe.

Nothing here moves anything. This module only observes.
"""

from __future__ import annotations

import os
from typing import Callable

__all__ = ["UserInputWatcher", "monotonic_tick_ms", "last_user_input_tick_ms"]

#: Deliberately absent: a time window for deciding whose input is whose.
#:
#: The first version of this class compared the last-input time against *our*
#: clock and treated anything within 250ms of our own action as ours. A test
#: killed it immediately, and it deserved to die: a user grabbing the mouse
#: 50ms after an automated click is the single most important case to catch,
#: and a grace window swallows exactly that. Timestamps cannot separate two
#: events that happen close together.
#:
#: What works instead is not a heuristic at all. After injecting input we ask
#: the system what it now reports as the last-input time, and anything strictly
#: later than that value is, by definition, not ours. No tolerance, no tuning.


def monotonic_tick_ms() -> int:
    """A millisecond tick from the same family as Win32's `GetTickCount`."""
    import time

    return int(time.monotonic() * 1000)


def last_user_input_tick_ms() -> int | None:
    """When Windows last saw any input, or ``None`` where it cannot be asked.

    Uses `GetLastInputInfo` through `ctypes`. Deliberately not a process
    invocation — that would be a second process-creation site, which ADR-0029
    forbids.
    """
    if os.name != "nt":
        return None

    import ctypes
    from ctypes import wintypes

    class LASTINPUTINFO(ctypes.Structure):
        _fields_ = [("cbSize", wintypes.UINT), ("dwTime", wintypes.DWORD)]

    info = LASTINPUTINFO()
    info.cbSize = ctypes.sizeof(LASTINPUTINFO)
    if not ctypes.windll.user32.GetLastInputInfo(ctypes.byref(info)):  # type: ignore[attr-defined]
        return None
    return int(info.dwTime)


class UserInputWatcher:
    """Watches for input the user made, ignoring input we made ourselves.

    Not thread-safe by design: one automation task owns `foreground_desktop` at
    a time (PRD §7.1), so one task owns its watcher.
    """

    def __init__(
        self,
        tick: Callable[[], int] | None = None,
        last_input_tick: Callable[[], int | None] | None = None,
    ) -> None:
        self._tick = tick or monotonic_tick_ms
        self._last_input_tick = last_input_tick or last_user_input_tick_ms
        self._armed_at: int | None = None
        #: The last-input value the *system* reported straight after our own
        #: injection. Anything later than this is not ours.
        self._baseline: int | None = None
        self._available = self._last_input_tick() is not None

    # -- what it can and cannot do -------------------------------------
    @property
    def available(self) -> bool:
        return self._available

    def unavailable_reason(self) -> str | None:
        if self._available:
            return None
        return (
            "This system does not report when the user last used the mouse or "
            "keyboard, so automation could not be paused when you touched them. "
            "Jarvis will not drive the desktop without that."
        )

    # -- lifecycle -----------------------------------------------------
    def arm(self) -> None:
        """Start watching from now. Forgets anything observed before."""
        self._armed_at = self._tick()
        self._baseline = None

    def note_synthetic_input(self) -> None:
        """Record that *we* just sent input, so it is not read as the user's.

        Call this **after** the injection, not before: it works by asking the
        system what it now considers the last input, which becomes the line
        above which input is somebody else's.

        Every code path that injects a keystroke or pointer event must call
        this. A path that forgets will pause its own task on its own action, and
        the symptom — automation stopping immediately, for no visible reason — is
        a long way from the cause.
        """
        # The one real-hardware risk left in this design, recorded rather than
        # guessed at: if Windows has not yet registered our injection when this
        # runs, the baseline is stale by one event and our own input reads as
        # the user's — automation pausing itself. It needs measuring against a
        # real SendInput, not reasoning about, and until then the failure is at
        # least the safe direction: it stops, rather than ignoring the user.
        observed = self._last_input_tick()
        if observed is not None:
            self._baseline = observed

    # -- the question --------------------------------------------------
    def user_intervened(self) -> bool:
        """Whether the user has touched the desktop since `arm()`.

        Raises rather than guessing: an unarmed or unobservable watcher returning
        ``False`` would be indistinguishable from a quiet desktop.
        """
        if self._armed_at is None:
            raise RuntimeError(
                "the watcher was asked about user input before it was armed; "
                "call arm() when the automation task takes the desktop"
            )
        if not self._available:
            raise RuntimeError(
                "user input cannot be observed on this system, so whether the "
                "user intervened is unknown. Automation must not treat that as "
                "'they did not'."
            )

        last_input = self._last_input_tick()
        if last_input is None:
            # It answered once and stopped. Downgrade honestly rather than
            # carrying on with a stale answer.
            self._available = False
            raise RuntimeError(
                "the system stopped reporting user input part-way through, so "
                "automation can no longer be interrupted reliably"
            )

        # The line above which input belongs to somebody else: whatever the
        # system reported after our own last injection, or the moment we armed
        # if we have not acted yet.
        baseline = self._baseline if self._baseline is not None else self._armed_at
        return last_input > baseline
