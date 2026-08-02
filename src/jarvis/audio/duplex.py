"""Full-duplex audio and barge-in (ADR-0028, PRD FR-015, section 11.3).

ADR-0028 chose to implement barge-in in Phase 1 rather than take the half-duplex
shortcut FR-015 permits, and named the consequence plainly: **the microphone
stays open while Kokoro is speaking**, so Jarvis hears itself. Without handling,
its own voice triggers the wake word, it interrupts itself, and it loops.

The ADR set the order of defences, and this module implements the first and
third; the second (platform acoustic echo cancellation) is a capture-device
setting requested in :mod:`jarvis.audio.capture`.

1. **Playback-aware gating (required).** The coordinator knows when it is
   speaking and for how long. A detection during playback is evaluated against
   that knowledge instead of being accepted blindly.
2. **Acoustic echo cancellation (preferred).** Requested from Windows at the
   capture device, because using the platform's is strongly preferred to writing
   one.
3. **Energy and similarity thresholds (fallback).** During playback the wake
   threshold is raised, and a detection whose level tracks what was just emitted
   is rejected as self-echo.

If the measured self-trigger rate is unacceptable, the honest fallback is
half-duplex — pause detection while speaking — **and say so in the GUI**
(NFR-014). That path is implemented here as :meth:`set_duplex_mode`, not
assumed unnecessary.

Barge-in is not emergency stop. It interrupts *speech*. It does not release
resource locks or cancel tasks — that is emergency stop's job, and conflating
them would make "stop talking" quietly destructive.
"""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

from jarvis.audio.ports import AudioChunk, WakeEvent
from jarvis.audio.vad import rms_level
from jarvis.common import utc_now

__all__ = ["DuplexCoordinator", "DuplexMode", "PlaybackWindow", "BargeInReport"]

_LOG = logging.getLogger(__name__)

#: How much higher a detection must score while Jarvis is speaking. Tuning is
#: hardware-specific; this is a starting point, not a measured constant.
PLAYBACK_SCORE_MULTIPLIER = 1.6

#: Detections within this long of playback starting or stopping are treated as
#: overlapping it, covering the delay between emitting a sample and hearing it.
ECHO_TAIL_SECONDS = 0.35


class DuplexMode(str, Enum):
    """Full duplex is the goal; half duplex is the honest fallback."""

    FULL = "full"
    HALF = "half"


@dataclass
class PlaybackWindow:
    """One stretch of Jarvis speaking, and what it emitted."""

    started_at: datetime
    text: str = ""
    ended_at: datetime | None = None
    peak_level: float = 0.0

    def covers(self, moment: datetime) -> bool:
        if moment < self.started_at - timedelta(seconds=ECHO_TAIL_SECONDS):
            return False
        if self.ended_at is None:
            return True
        return moment <= self.ended_at + timedelta(seconds=ECHO_TAIL_SECONDS)


@dataclass(frozen=True)
class BargeInReport:
    """What a barge-in actually stopped. Never more than speech."""

    interrupted: bool
    spoken_text: str = ""
    reason: str = ""
    #: Stated explicitly because the distinction from emergency stop matters.
    released_locks: tuple[str, ...] = field(default_factory=tuple)
    cancelled_tasks: tuple[str, ...] = field(default_factory=tuple)


class DuplexCoordinator:
    """Knows when Jarvis is speaking, and judges detections accordingly."""

    def __init__(
        self,
        *,
        mode: DuplexMode = DuplexMode.FULL,
        score_multiplier: float = PLAYBACK_SCORE_MULTIPLIER,
    ) -> None:
        self._mode = mode
        self._score_multiplier = score_multiplier
        self._lock = threading.RLock()
        self._current: PlaybackWindow | None = None
        self._recent: list[PlaybackWindow] = []
        self._stop_playback: threading.Event = threading.Event()
        self._self_triggers = 0
        self._accepted_during_playback = 0

    # -- mode --------------------------------------------------------------
    @property
    def mode(self) -> DuplexMode:
        with self._lock:
            return self._mode

    def set_duplex_mode(self, mode: DuplexMode) -> None:
        """Degrade to half duplex when full duplex cannot be made reliable."""
        with self._lock:
            self._mode = mode
        _LOG.info("audio duplex mode set to %s", mode.value)

    def describe_mode(self) -> str:
        if self.mode is DuplexMode.FULL:
            return (
                "Full duplex: you can interrupt Jarvis while it is speaking."
            )
        return (
            "Half duplex: wake detection pauses while Jarvis is speaking, so you "
            "cannot interrupt by voice. Use push-to-talk or the emergency-stop "
            "hotkey instead."
        )

    # -- playback ----------------------------------------------------------
    @property
    def speaking(self) -> bool:
        with self._lock:
            return self._current is not None

    def playback_started(self, text: str = "") -> PlaybackWindow:
        with self._lock:
            self._stop_playback.clear()
            self._current = PlaybackWindow(started_at=utc_now(), text=text)
            return self._current

    def playback_finished(self) -> None:
        with self._lock:
            if self._current is None:
                return
            self._current.ended_at = utc_now()
            self._recent.append(self._current)
            # Only the last few windows matter for echo attribution.
            self._recent = self._recent[-8:]
            self._current = None
            self._stop_playback.clear()

    def note_emitted_level(self, chunk: AudioChunk) -> None:
        """Record how loud Jarvis's own output was, for the echo comparison."""
        with self._lock:
            if self._current is not None:
                self._current.peak_level = max(self._current.peak_level, rms_level(chunk))

    # -- capture gating (ADR-0028 rule: playback never stops capture) ------
    def capture_should_run(self) -> bool:
        """Capture continues during playback. That is the point of full duplex."""
        return True

    def detection_enabled(self) -> bool:
        """Whether wake detection is live right now."""
        if self.mode is DuplexMode.FULL:
            return True
        # Half duplex: detection pauses while speaking, and the GUI says so.
        return not self.speaking

    # -- judging a detection ----------------------------------------------
    def accept_detection(
        self, event: WakeEvent, base_threshold: float, *, captured_level: float | None = None
    ) -> bool:
        """Decide whether a detection is the user or Jarvis hearing itself."""
        with self._lock:
            speaking = self._current is not None
            window = self._current or next(
                (w for w in reversed(self._recent) if w.covers(event.detected_at)), None
            )
            overlaps = speaking or (window is not None and window.covers(event.detected_at))

            if not overlaps:
                return True

            if self.mode is DuplexMode.HALF:
                self._self_triggers += 1
                return False

            # Defence 3: raise the bar while our own voice is in the room.
            if event.score < base_threshold * self._score_multiplier:
                self._self_triggers += 1
                _LOG.debug(
                    "rejected a detection during playback: score %.3f below raised "
                    "threshold %.3f", event.score, base_threshold * self._score_multiplier
                )
                return False

            # ...and reject one whose level merely tracks what we just emitted.
            if (
                captured_level is not None
                and window is not None
                and window.peak_level > 0.0
                and captured_level <= window.peak_level * 1.1
            ):
                self._self_triggers += 1
                _LOG.debug("rejected a detection during playback: level matches our own output")
                return False

            self._accepted_during_playback += 1
            return True

    # -- barge-in ----------------------------------------------------------
    def request_barge_in(self, reason: str = "the user spoke") -> BargeInReport:
        """Stop speaking. Do nothing else — this is not emergency stop."""
        with self._lock:
            window = self._current
            if window is None:
                return BargeInReport(interrupted=False, reason="Jarvis was not speaking")
            self._stop_playback.set()
            spoken = window.text
        return BargeInReport(interrupted=True, spoken_text=spoken, reason=reason)

    @property
    def stop_requested(self) -> bool:
        """Polled by the playback loop between buffers."""
        return self._stop_playback.is_set()

    def clear_stop(self) -> None:
        self._stop_playback.clear()

    # -- measurement (ADR-0028 gates enabling barge-in on this) ------------
    @property
    def self_trigger_count(self) -> int:
        with self._lock:
            return self._self_triggers

    @property
    def accepted_during_playback_count(self) -> int:
        with self._lock:
            return self._accepted_during_playback

    def measurement_summary(self) -> str:
        with self._lock:
            rejected, accepted = self._self_triggers, self._accepted_during_playback
        total = rejected + accepted
        if total == 0:
            return "No detections have occurred during playback yet."
        return (
            f"{rejected} of {total} detection(s) during playback were attributed to "
            f"Jarvis's own output and rejected."
        )
