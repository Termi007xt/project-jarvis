"""Voice activity detection and command bounds (PRD FR-014, FR-017).

Energy-based, deliberately. A neural VAD would be more accurate, but it is
another model to load, another optional dependency, and another thing that
behaves differently on a machine that does not have it. faster-whisper already
applies its own VAD filter during transcription (``vad_filter=True``, verified
in tools/voice-lab); this detector only has to answer a simpler question: *when
did the user stop talking?*

Thresholds are calibrated against the room rather than guessed (FR-017): the
caller measures ambient noise for a moment and the threshold is derived from it,
so a quiet study and a noisy office both work without the user tuning numbers.
"""

from __future__ import annotations

import array
import math
from dataclasses import dataclass
from enum import Enum

from jarvis.audio.ports import SAMPLE_RATE, AudioChunk, AudioFormat

__all__ = [
    "VoiceActivityDetector",
    "NoiseCalibration",
    "SpeechState",
    "rms_level",
    "calibrate",
]


class SpeechState(str, Enum):
    SILENT = "silent"
    SPEAKING = "speaking"
    ENDED = "ended"


def rms_level(chunk: AudioChunk) -> float:
    """Root-mean-square level of a chunk, normalised to roughly 0.0-1.0."""
    if not chunk.samples:
        return 0.0
    if chunk.audio_format is AudioFormat.FLOAT32:
        values = array.array("f")
        values.frombytes(chunk.samples[: len(chunk.samples) // 4 * 4])
        if not values:
            return 0.0
        return math.sqrt(sum(value * value for value in values) / len(values))
    values_i = array.array("h")
    values_i.frombytes(chunk.samples[: len(chunk.samples) // 2 * 2])
    if not values_i:
        return 0.0
    return math.sqrt(sum((v / 32768.0) ** 2 for v in values_i) / len(values_i))


@dataclass(frozen=True)
class NoiseCalibration:
    """What the room sounds like when nobody is talking (PRD FR-017)."""

    noise_floor: float
    speech_threshold: float
    sample_count: int

    def describe(self) -> str:
        return (
            f"noise floor {self.noise_floor:.4f}, speech above "
            f"{self.speech_threshold:.4f} ({self.sample_count} frames measured)"
        )


def calibrate(
    frames: list[AudioChunk], *, margin: float = 3.0, floor: float = 0.005
) -> NoiseCalibration:
    """Derive a speech threshold from ambient noise.

    ``margin`` is how far above the measured floor speech has to be. ``floor``
    stops a silent recording producing a threshold so low that every breath
    counts as speech.
    """
    if not frames:
        return NoiseCalibration(noise_floor=floor, speech_threshold=floor * margin, sample_count=0)
    levels = sorted(rms_level(frame) for frame in frames)
    # Median rather than mean: one door slam should not define the room.
    median = levels[len(levels) // 2]
    noise_floor = max(median, floor)
    return NoiseCalibration(
        noise_floor=noise_floor,
        speech_threshold=noise_floor * margin,
        sample_count=len(frames),
    )


class VoiceActivityDetector:
    """Tracks where one spoken command starts and stops.

    ``hangover`` is why this is a state machine rather than a threshold test:
    people pause mid-sentence, and cutting the command at the first quiet frame
    truncates half of what they said.
    """

    def __init__(
        self,
        calibration: NoiseCalibration | None = None,
        *,
        sample_rate: int = SAMPLE_RATE,
        start_frames: int = 2,
        hangover_seconds: float = 0.8,
        max_command_seconds: float = 30.0,
    ) -> None:
        self._calibration = calibration or NoiseCalibration(0.005, 0.015, 0)
        self._sample_rate = sample_rate
        self._start_frames = max(1, start_frames)
        self._hangover_seconds = hangover_seconds
        self._max_command_seconds = max_command_seconds
        self.reset()

    def reset(self) -> None:
        self._state = SpeechState.SILENT
        self._loud_run = 0
        self._quiet_seconds = 0.0
        self._speech_seconds = 0.0
        self._peak = 0.0

    # -- state -------------------------------------------------------------
    @property
    def state(self) -> SpeechState:
        return self._state

    @property
    def speech_seconds(self) -> float:
        return self._speech_seconds

    @property
    def peak_level(self) -> float:
        return self._peak

    @property
    def calibration(self) -> NoiseCalibration:
        return self._calibration

    def recalibrate(self, calibration: NoiseCalibration) -> None:
        self._calibration = calibration

    # -- the detector ------------------------------------------------------
    def push(self, chunk: AudioChunk) -> SpeechState:
        """Feed one frame. Returns the state after it."""
        level = rms_level(chunk)
        self._peak = max(self._peak, level)
        duration = chunk.duration_seconds
        loud = level >= self._calibration.speech_threshold

        if self._state is SpeechState.SILENT:
            self._loud_run = self._loud_run + 1 if loud else 0
            if self._loud_run >= self._start_frames:
                self._state = SpeechState.SPEAKING
                self._speech_seconds = duration * self._loud_run
                self._quiet_seconds = 0.0
            return self._state

        if self._state is SpeechState.SPEAKING:
            self._speech_seconds += duration
            if loud:
                self._quiet_seconds = 0.0
            else:
                self._quiet_seconds += duration
                if self._quiet_seconds >= self._hangover_seconds:
                    self._state = SpeechState.ENDED
                    return self._state
            if self._speech_seconds >= self._max_command_seconds:
                # Bounded, like every other wait in the product (NFR-013).
                self._state = SpeechState.ENDED
        return self._state

    @property
    def ended_because(self) -> str:
        if self._speech_seconds >= self._max_command_seconds:
            return f"reached the {self._max_command_seconds:.0f}s limit for one command"
        return "silence"
