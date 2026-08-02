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
from jarvis.audio.pipeline import CommandHeard, ListeningState, VoicePipeline
from jarvis.audio.ports import AudioChunk, AudioUnavailable, SynthesisResult
from jarvis.audio.ring_buffer import RingBuffer
from jarvis.audio.stt import build_stt_provider
from jarvis.audio.tts import build_tts_provider
from jarvis.audio.vad import NoiseCalibration, VoiceActivityDetector, calibrate
from jarvis.audio.wake import build_wake_detector, wake_model_path
from jarvis.core.audit.log import AuditLog
from jarvis.core.audit.models import AuditCategory

__all__ = ["VoiceService", "VoiceStatus"]

_LOG = logging.getLogger(__name__)


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
        self._calibration: NoiseCalibration | None = None

        self.tts = build_tts_provider(config)
        self.stt = build_stt_provider(config)
        self.wake = build_wake_detector(config, vault_root)

        wake_settings = config.audio.wake_word  # type: ignore[attr-defined]
        self.pipeline = VoicePipeline(
            wake_detector=self.wake,
            stt=self.stt,
            duplex=DuplexCoordinator(),
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
    def status(self) -> VoiceStatus:
        wake_settings = self._config.audio.wake_word  # type: ignore[attr-defined]
        return VoiceStatus(
            listening=self.pipeline.state,
            always_listening=wake_settings.always_listening and wake_settings.enrolled,
            enrolled=wake_settings.enrolled,
            phrase=wake_settings.phrase,
            duplex=self.pipeline.duplex.describe_mode(),
            stack_summary=describe_voice_stack(
                self._config, wake_model_path(self._vault_root)
            ).summary(),
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
    def speak(self, text: str, *, voice_id: str | None = None) -> SynthesisResult | None:
        """Synthesise and hand back audio. Playback is the shell's job."""
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
        return result

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

    def shutdown(self) -> None:
        self.stop_capture()

    # -- internals ---------------------------------------------------------
    def _record(self, summary: str) -> None:
        if self._audit is None:
            return
        self._audit.record(AuditCategory.SECURITY, summary, actor="user")
