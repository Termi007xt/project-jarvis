"""The voice loop (PRD sections 10.2 to 10.4, ADR-0027, ADR-0028).

One place where capture, wake detection, voice activity, transcription and
speech meet, so the privacy and honesty rules are enforced once rather than at
each call site:

* Pre-wake audio lives only in the ring buffer, which cannot write to disk
  (FR-012, AT-002).
* Capture announces itself before it starts and stops announcing only after it
  stops (FR-013).
* The wake phrase is stripped from the command before it goes anywhere (FR-024).
* A low-confidence command that could cause an action is confirmed, not acted on
  (FR-023).
* Command audio is discarded once transcribed (FR-025).
* Capture continues while Jarvis speaks, and a detection during playback is
  judged against what Jarvis emitted rather than accepted blindly (ADR-0028).

The loop runs on its own thread. Nothing here touches Qt.
"""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass
from enum import Enum
from typing import Callable

from jarvis.audio.duplex import DuplexCoordinator
from jarvis.audio.ports import (
    AudioChunk,
    SpeechSegment,
    Transcript,
    WakeEvent,
)
from jarvis.audio.ring_buffer import RingBuffer
from jarvis.audio.stt import needs_confirmation, strip_wake_phrase
from jarvis.audio.vad import SpeechState, VoiceActivityDetector, rms_level
from jarvis.common import utc_now

__all__ = ["VoicePipeline", "ListeningState", "CommandHeard", "ActivationRoute"]

_LOG = logging.getLogger(__name__)


class ListeningState(str, Enum):
    OFF = "off"
    WAITING_FOR_WAKE = "waiting_for_wake"
    CAPTURING_COMMAND = "capturing_command"
    TRANSCRIBING = "transcribing"
    SPEAKING = "speaking"


class ActivationRoute(str, Enum):
    WAKE_WORD = "wake_word"
    PUSH_TO_TALK = "push_to_talk"


@dataclass(frozen=True)
class CommandHeard:
    """One complete spoken command, ready for the planner."""

    text: str
    transcript: Transcript
    route: ActivationRoute
    needs_confirmation: bool
    wake_event: WakeEvent | None = None

    @property
    def empty(self) -> bool:
        return not self.text.strip()


class VoicePipeline:
    """Capture in, commands out. Owns the listening state machine."""

    def __init__(
        self,
        *,
        wake_detector: object,
        stt: object,
        duplex: DuplexCoordinator | None = None,
        vad: VoiceActivityDetector | None = None,
        ring_buffer: RingBuffer | None = None,
        phrase: str = "Hey Jarvis",
        on_command: Callable[[CommandHeard], None] | None = None,
        on_state: Callable[[ListeningState], None] | None = None,
        on_level: Callable[[float], None] | None = None,
        always_listening: bool = False,
    ) -> None:
        self._wake = wake_detector
        self._stt = stt
        self._duplex = duplex or DuplexCoordinator()
        self._vad = vad or VoiceActivityDetector()
        self._buffer = ring_buffer or RingBuffer()
        self._phrase = phrase
        self._on_command = on_command
        self._on_state = on_state
        self._on_level = on_level
        self._always_listening = always_listening

        self._lock = threading.RLock()
        self._state = ListeningState.OFF
        self._command_frames: list[AudioChunk] = []
        self._route: ActivationRoute | None = None
        self._wake_event: WakeEvent | None = None
        self._commands_heard = 0

    # -- state -------------------------------------------------------------
    @property
    def state(self) -> ListeningState:
        with self._lock:
            return self._state

    @property
    def commands_heard(self) -> int:
        return self._commands_heard

    @property
    def duplex(self) -> DuplexCoordinator:
        return self._duplex

    @property
    def ring_buffer(self) -> RingBuffer:
        return self._buffer

    def _set_state(self, state: ListeningState) -> None:
        with self._lock:
            if self._state is state:
                return
            self._state = state
        if self._on_state is not None:
            try:
                self._on_state(state)
            except Exception:  # noqa: BLE001 - a listener must not stop the loop
                _LOG.exception("a listening-state listener raised")

    # -- control -----------------------------------------------------------
    def start_listening(self) -> None:
        """Begin waiting for the wake phrase, if enrolment allows it."""
        if not self._always_listening:
            _LOG.info("always-listening is off; push-to-talk only (ADR-0016)")
            return
        self._buffer.clear()
        self._vad.reset()
        self._set_state(ListeningState.WAITING_FOR_WAKE)

    def stop_listening(self) -> None:
        """Stop, and forget everything held. Nothing survives in memory."""
        self._buffer.clear()
        self._command_frames.clear()
        self._vad.reset()
        self._set_state(ListeningState.OFF)

    def begin_push_to_talk(self) -> None:
        """F9 pressed. Capture a command without a wake phrase (FR-018)."""
        if self._duplex.speaking:
            # Push-to-talk is the deterministic interruption path when acoustic
            # barge-in is unreliable (ADR-0028).
            self._duplex.request_barge_in("push-to-talk pressed")
        with self._lock:
            self._route = ActivationRoute.PUSH_TO_TALK
            self._wake_event = None
            self._command_frames = list(self._buffer.snapshot_frames())
        self._vad.reset()
        self._set_state(ListeningState.CAPTURING_COMMAND)

    def end_push_to_talk(self) -> CommandHeard | None:
        """F9 released. Transcribe what was captured."""
        if self.state is not ListeningState.CAPTURING_COMMAND:
            return None
        return self._finish_command("push-to-talk released")

    # -- the frame path ----------------------------------------------------
    def push_frame(self, chunk: AudioChunk) -> None:
        """One captured frame. Called from the audio thread."""
        if self._on_level is not None:
            try:
                self._on_level(rms_level(chunk))
            except Exception:  # noqa: BLE001
                _LOG.exception("a level listener raised")

        state = self.state
        if state is ListeningState.OFF:
            return

        if state is ListeningState.CAPTURING_COMMAND:
            self._command_frames.append(chunk)
            if self._vad.push(chunk) is SpeechState.ENDED:
                self._finish_command(self._vad.ended_because)
            return

        # Waiting for a wake phrase: audio stays in the ring buffer only.
        self._buffer.write(chunk)
        if not self._duplex.detection_enabled():
            return
        self._check_for_wake(chunk)

    def _check_for_wake(self, chunk: AudioChunk) -> None:
        detector = self._wake
        if not getattr(detector, "available", False):
            return
        try:
            score = detector.score(chunk)  # type: ignore[attr-defined]
        except Exception:  # noqa: BLE001 - a detector fault must not kill capture
            _LOG.exception("the wake detector raised")
            return

        threshold = getattr(detector, "threshold", 0.5)
        if score < threshold:
            return

        event = WakeEvent(
            phrase=self._phrase,
            score=score,
            detected_at=utc_now(),
            during_playback=self._duplex.speaking,
        )
        if not self._duplex.accept_detection(
            event, threshold, captured_level=rms_level(chunk)
        ):
            # Attributed to Jarvis's own output. Not a wake (ADR-0028).
            return

        if self._duplex.speaking:
            self._duplex.request_barge_in("the user spoke while Jarvis was speaking")

        # Reset before capturing. A detector keeps internal state across frames,
        # so without this the frames that produced the detection keep scoring
        # high and the same utterance wakes Jarvis several times over.
        try:
            detector.reset()  # type: ignore[attr-defined]
        except Exception:  # noqa: BLE001 - a reset fault must not lose the wake
            _LOG.exception("could not reset the wake detector")

        with self._lock:
            self._route = ActivationRoute.WAKE_WORD
            self._wake_event = event
            # The run-up to the phrase is what the ring buffer exists for: the
            # detector fires slightly after the user began speaking.
            self._command_frames = list(self._buffer.snapshot_frames())
        self._buffer.clear()
        self._vad.reset()
        self._set_state(ListeningState.CAPTURING_COMMAND)

    # -- completing a command ---------------------------------------------
    def _finish_command(self, reason: str) -> CommandHeard | None:
        with self._lock:
            frames, self._command_frames = self._command_frames, []
            route = self._route or ActivationRoute.PUSH_TO_TALK
            wake_event = self._wake_event
            self._wake_event = None

        if not frames:
            self._set_state(
                ListeningState.WAITING_FOR_WAKE if self._always_listening else ListeningState.OFF
            )
            return None

        self._set_state(ListeningState.TRANSCRIBING)
        audio = _join(frames)
        segment = SpeechSegment(
            audio=audio,
            started_at=frames[0].captured_at,
            ended_at=utc_now(),
            ended_because=reason,
        )

        try:
            transcript = self._stt.transcribe(segment.audio)  # type: ignore[attr-defined]
        except Exception as exc:  # noqa: BLE001 - reported, never guessed at
            _LOG.exception("transcription failed")
            transcript = Transcript(text="", model=str(exc))
        finally:
            # FR-025: the audio is gone as soon as it has been transcribed.
            frames.clear()

        text = strip_wake_phrase(transcript.text, self._phrase)
        command = CommandHeard(
            text=text,
            transcript=transcript,
            route=route,
            needs_confirmation=needs_confirmation(transcript),
            wake_event=wake_event,
        )

        self._set_state(
            ListeningState.WAITING_FOR_WAKE if self._always_listening else ListeningState.OFF
        )
        if not command.empty:
            self._commands_heard += 1
            if self._on_command is not None:
                try:
                    self._on_command(command)
                except Exception:  # noqa: BLE001
                    _LOG.exception("a command listener raised")
        return command

    # -- speaking ----------------------------------------------------------
    def speaking_started(self, text: str) -> None:
        self._duplex.playback_started(text)
        self._set_state(ListeningState.SPEAKING)

    def speaking_finished(self) -> None:
        self._duplex.playback_finished()
        self._set_state(
            ListeningState.WAITING_FOR_WAKE if self._always_listening else ListeningState.OFF
        )

    def set_always_listening(self, enabled: bool) -> None:
        """Only ever enabled after enrolment has been measured (ADR-0016)."""
        self._always_listening = enabled
        if not enabled and self.state is ListeningState.WAITING_FOR_WAKE:
            self.stop_listening()


def _join(frames: list[AudioChunk]) -> AudioChunk:
    first = frames[0]
    return AudioChunk(
        samples=b"".join(frame.samples for frame in frames),
        sample_rate=first.sample_rate,
        audio_format=first.audio_format,
        captured_at=first.captured_at,
    )
