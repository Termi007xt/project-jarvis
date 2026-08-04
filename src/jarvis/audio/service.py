"""The voice service: one object that owns the whole audio stack (L3).

Built even when nothing is installed, so the Voice screen can report each
component's real state instead of the feature simply being absent (ADR-0010).
Every provider it holds knows how to say why it is unavailable, and the service
never substitutes one for another silently.
"""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass
from pathlib import Path

from jarvis.audio.availability import describe_voice_stack
from jarvis.audio.capture import CaptureSession, capture_available, default_input_device
from jarvis.audio.duplex import DuplexCoordinator, DuplexMode
from jarvis.audio.model_hub import apply_network_policy
from jarvis.audio.pipeline import CommandHeard, ListeningState, VoicePipeline
from jarvis.audio.playback import PlaybackReport, play, playback_available
from jarvis.audio.ports import AudioChunk, AudioUnavailable
from jarvis.audio.ring_buffer import RingBuffer
from jarvis.audio.stt import build_stt_provider
from jarvis.audio.tts import build_tts_provider
from jarvis.audio.vad import NoiseCalibration, VoiceActivityDetector, calibrate
from jarvis.audio.wake import build_wake_detector, wake_model_path
from jarvis.core.audit.log import AuditLog
from jarvis.core.audit.models import AuditCategory

__all__ = ["VoiceService", "VoiceStatus", "SpokenResult", "configured_duplex_mode"]

_LOG = logging.getLogger(__name__)


def configured_duplex_mode(config: object) -> DuplexMode:
    """Read ``audio.duplex_mode``, degrading rather than over-claiming.

    Anything unreadable resolves to half duplex. The two failure directions are
    not symmetrical: claiming Jarvis can be interrupted when it cannot leaves
    the user talking at a machine that is not listening, while claiming it
    cannot when it can costs them one press of a key that also works.
    """
    audio = getattr(config, "audio", None)
    value = getattr(audio, "duplex_mode", None)
    if isinstance(value, str) and value.strip().lower() == DuplexMode.FULL.value:
        return DuplexMode.FULL
    return DuplexMode.HALF


@dataclass(frozen=True)
class SpokenResult:
    """What was synthesised, and what was actually played (PRD FR-048).

    Carries the same fields the synthesis result did, so callers that only want
    the audio are unaffected, plus the playback report that says whether any of
    it reached a speaker.
    """

    audio: AudioChunk
    voice_id: str
    text: str
    redacted: bool
    playback: PlaybackReport

    @property
    def spoken_aloud(self) -> bool:
        return self.playback.played


@dataclass(frozen=True)
class VoiceStatus:
    listening: ListeningState
    always_listening: bool
    enrolled: bool
    phrase: str
    duplex: str
    stack_summary: str


class VoiceService:
    """Owns the providers, the pipeline and the capture session."""

    def __init__(
        self,
        config: object,
        vault_root: Path,
        *,
        audit: AuditLog | None = None,
        on_command=None,
        on_state=None,
        on_level=None,
        indicator=None,
    ) -> None:
        self._config = config
        self._vault_root = vault_root
        self._audit = audit
        self._indicator = indicator
        self._lock = threading.RLock()
        self._capture: CaptureSession | None = None
        self._device_index: int | None = None
        self._output_device_index: int | None = None
        self._calibration: NoiseCalibration | None = None

        # AT-001: offline mode opens no socket, and the speech model hubs are
        # a component the user reasonably believes is already local.
        apply_network_policy(config)

        self.tts = build_tts_provider(config)
        self.stt = build_stt_provider(config)
        self.wake = build_wake_detector(config, vault_root)

        wake_settings = config.audio.wake_word  # type: ignore[attr-defined]
        self.pipeline = VoicePipeline(
            wake_detector=self.wake,
            stt=self.stt,
            duplex=DuplexCoordinator(mode=configured_duplex_mode(config)),
            vad=VoiceActivityDetector(),
            ring_buffer=RingBuffer(),
            phrase=wake_settings.phrase,
            on_command=on_command,
            on_state=on_state,
            on_level=on_level,
            # ADR-0016 criterion 2: never on until enrolment has been measured.
            always_listening=bool(wake_settings.always_listening and wake_settings.enrolled),
        )

    # -- status ------------------------------------------------------------
    def preload(self) -> dict[str, str]:
        """Load the speech models now, so the first command is not the slow one.

        Both providers load lazily, which is right for import time and wrong for
        the first thing the user says — the wait landed on them rather than on
        start-up. `FasterWhisperSttProvider.load` has said "call it from a
        worker at start-up" since Phase 1 and nothing ever did.

        Returns what happened per component, so a failure to warm is reported
        rather than swallowed. It never raises: a model that will not preload
        still loads on first use, more slowly, and that is a degradation rather
        than a failure (ADR-0010).
        """
        outcome: dict[str, str] = {}
        for name, provider in (("tts", self.tts), ("stt", self.stt)):
            load = getattr(provider, "load", None)
            if load is None:
                outcome[name] = "no preload needed"
                continue
            if not getattr(provider, "available", False):
                reason = getattr(provider, "unavailable_reason", lambda: None)()
                outcome[name] = f"unavailable: {reason or 'not installed'}"
                continue
            try:
                load()
                outcome[name] = "loaded"
            except Exception as exc:  # noqa: BLE001 - warming must not break start-up
                _LOG.warning("could not preload %s: %s", name, exc)
                outcome[name] = f"failed: {exc}"
        return outcome

    def status(self) -> VoiceStatus:
        wake_settings = self._config.audio.wake_word  # type: ignore[attr-defined]
        return VoiceStatus(
            listening=self.pipeline.state,
            always_listening=wake_settings.always_listening and wake_settings.enrolled,
            enrolled=wake_settings.enrolled,
            phrase=wake_settings.phrase,
            duplex=self.describe_interruption(),
            stack_summary=describe_voice_stack(
                self._config, wake_model_path(self._vault_root)
            ).summary(),
        )

    def describe_interruption(self) -> str:
        """What can interrupt Jarvis right now, given the microphone's state."""
        hotkey = getattr(
            getattr(self._config, "ui", None), "emergency_stop_hotkey", "the emergency-stop hotkey"
        )
        return self.pipeline.duplex.describe_interruption(
            listening=self.listening, hotkey=hotkey
        )

    @property
    def enrolment_passed(self) -> bool:
        """No enrolment has been run in this build, so nothing has passed."""
        return False

    def enrolment_summary(self) -> str:
        wake_settings = self._config.audio.wake_word  # type: ignore[attr-defined]
        reason = getattr(self.wake, "unavailable_reason", lambda: None)()
        if reason:
            return (
                f"{reason} Push-to-talk is the way to talk to Jarvis until that "
                "is resolved (ADR-0027)."
            )
        if not wake_settings.enrolled:
            return (
                "No wake-word enrolment has been recorded, so always-listening "
                "stays off and push-to-talk is used instead (ADR-0016)."
            )
        return "Enrolled, but no measurement is recorded for this enrolment."

    # -- capture -----------------------------------------------------------
    @property
    def capture_available(self) -> bool:
        return capture_available()

    @property
    def playback_available(self) -> bool:
        """Whether anything can actually be heard. Speaking depends on it."""
        return playback_available()

    def start_capture(self, device_index: int | None = None) -> bool:
        """Open the microphone. Returns False, honestly, if it cannot."""
        if not self.capture_available:
            return False
        with self._lock:
            if self._capture is not None:
                return True
            chosen = device_index if device_index is not None else self._device_index
            if chosen is None:
                default = default_input_device()
                chosen = default.index if default is not None else None
            try:
                self._capture = CaptureSession(
                    device_index=chosen,
                    on_frame=self.pipeline.push_frame,
                    indicator=self._indicator,
                ).start()
            except Exception as exc:  # noqa: BLE001 - reported, never hidden
                _LOG.exception("could not open the microphone")
                self._capture = None
                self._record(f"microphone could not be opened: {exc}")
                return False
            self._device_index = chosen
        self._record("microphone opened")
        return True

    def stop_capture(self) -> None:
        with self._lock:
            capture, self._capture = self._capture, None
        if capture is not None:
            capture.stop()
            self._record("microphone closed")
        self.pipeline.stop_listening()

    @property
    def capturing(self) -> bool:
        with self._lock:
            return self._capture is not None

    def calibrate_from(self, frames: list[AudioChunk]) -> NoiseCalibration:
        """Measure the room and apply the threshold (PRD FR-017)."""
        self._calibration = calibrate(frames)
        self.pipeline._vad.recalibrate(self._calibration)  # noqa: SLF001
        self._record(f"ambient noise calibrated: {self._calibration.describe()}")
        return self._calibration

    @property
    def calibration(self) -> NoiseCalibration | None:
        return self._calibration

    # -- speaking ----------------------------------------------------------
    def speak(self, text: str, *, voice_id: str | None = None) -> SpokenResult | None:
        """Synthesise **and play**, then report what actually came out.

        Synthesis alone used to be the whole of this method, and the caller
        reported "Spoken." on the strength of it. Nothing played the audio, so
        that was a verified success claim for a silent room (PRD FR-048). The
        returned report now says how much audio reached the device.
        """
        if not getattr(self.tts, "available", False):
            reason = getattr(self.tts, "unavailable_reason", lambda: None)()
            _LOG.info("cannot speak: %s", reason)
            return None
        self.pipeline.speaking_started(text)
        try:
            result = self.tts.synthesise(text, voice_id=voice_id)  # type: ignore[attr-defined]
        except (AudioUnavailable, ValueError) as exc:
            _LOG.warning("synthesis failed: %s", exc)
            self.pipeline.speaking_finished()
            return None

        if result.redacted:
            # FR-034: say that something was withheld rather than silently
            # speaking a different sentence.
            self._record("spoken output was redacted before it was spoken aloud")

        try:
            report = play(
                result.audio,
                device_index=self._output_device_index,
                # ADR-0028: barge-in cuts playback between blocks.
                should_stop=lambda: self.pipeline.duplex.stop_requested,
                on_block=self.pipeline.duplex.note_emitted_level,
            )
        finally:
            self.pipeline.speaking_finished()

        if report.error:
            _LOG.warning("nothing was spoken aloud: %s", report.error)
        if report.interrupted:
            self._record("speech was interrupted by the user (barge-in)")
        return SpokenResult(
            audio=result.audio,
            voice_id=result.voice_id,
            text=result.text,
            redacted=result.redacted,
            playback=report,
        )

    def set_input_device(self, device_index: int | None) -> bool:
        """Choose the microphone (PRD FR-016). Reopens an open stream."""
        was_capturing = self.capturing
        if was_capturing:
            self.stop_capture()
        with self._lock:
            self._device_index = device_index
        if was_capturing:
            return self.start_capture(device_index)
        return True

    @property
    def output_device_index(self) -> int | None:
        return self._output_device_index

    @property
    def cues_enabled(self) -> bool:
        return bool(getattr(self._config.audio, "cues_enabled", True))  # type: ignore[attr-defined]

    def set_output_device(self, device_index: int | None) -> None:
        self._output_device_index = device_index

    def apply_network_policy(self) -> bool:
        """Re-pin the model hubs after a network-mode change (AT-001)."""
        return apply_network_policy(self._config)

    def set_indicator(self, indicator) -> None:
        """Attach the recording indicator (PRD FR-013).

        Capture may not start without announcing itself, and only the shell can
        show it, so it is attached rather than passed in at construction.
        """
        self._indicator = indicator

    def stop_speaking(self, reason: str = "the user asked Jarvis to stop") -> bool:
        """Cut playback short. Speech only — never locks, never tasks.

        The deterministic half of ADR-0028. Acoustic barge-in depends on
        thresholds that have to be measured in a real room; pressing a key does
        not, so this is the route that has to work before any tuning does.
        """
        report = self.pipeline.duplex.request_barge_in(reason)
        if report.interrupted:
            self._record(f"speech was stopped: {reason}")
        return report.interrupted

    def finished_speaking(self) -> None:
        self.pipeline.speaking_finished()

    def set_duplex_mode(self, mode: DuplexMode) -> None:
        self.pipeline.duplex.set_duplex_mode(mode)
        self._record(f"audio duplex mode set to {mode.value}")

    # -- push to talk ------------------------------------------------------
    def begin_push_to_talk(self) -> bool:
        if not self.start_capture():
            return False
        self.pipeline.begin_push_to_talk()
        return True

    def end_push_to_talk(self) -> CommandHeard | None:
        return self.pipeline.end_push_to_talk()

    @property
    def capturing_command(self) -> bool:
        return self.pipeline.state is ListeningState.CAPTURING_COMMAND

    # -- always-listening (ADR-0016, amended) ------------------------------
    @property
    def listening(self) -> bool:
        return self.pipeline.state is not ListeningState.OFF and self.capturing

    def start_listening(self, device_index: int | None = None) -> tuple[bool, str]:
        """Listen for the wake phrase. Returns (started, why not).

        ADR-0016 originally gated this on a *personal* enrolment. The owner
        chose to run on the pretrained model instead, so the gate is now the
        model being installed and loadable rather than an enrolment that does
        not exist. What has and has not been measured is stated on the Voice
        screen; nothing here implies a false-accept rate we have not measured.
        """
        reason = getattr(self.wake, "unavailable_reason", lambda: None)()
        if reason:
            return False, reason
        if not self.capture_available:
            return False, "No microphone is available."
        if not self.start_capture(device_index):
            return False, "The microphone could not be opened."

        self.pipeline.set_always_listening(True)
        self.pipeline.start_listening()
        self._record("started listening for the wake phrase")
        return True, ""

    def stop_listening(self) -> None:
        """Close the microphone and forget everything buffered."""
        self.pipeline.set_always_listening(False)
        self.stop_capture()
        self._record("stopped listening")

    def set_command_listener(self, callback) -> None:
        """Where a finished spoken command goes. Nothing listened before."""
        self.pipeline.set_command_listener(callback)

    def set_state_listener(self, callback) -> None:
        self.pipeline.set_state_listener(callback)

    def set_level_listener(self, callback) -> None:
        self.pipeline.set_level_listener(callback)

    def shutdown(self) -> None:
        self.stop_capture()

    # -- internals ---------------------------------------------------------
    def _record(self, summary: str) -> None:
        if self._audit is None:
            return
        self._audit.record(AuditCategory.SECURITY, summary, actor="user")
