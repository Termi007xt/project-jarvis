"""Audio provider boundaries (ARCHITECTURE.md section 8, PRD sections 10.2-10.4).

The three extension points Phase 1 fills — ``WakeDetector``, ``SttProvider``,
``TtsProvider`` — plus the typed values that cross them.

Nothing here imports an audio library. These are the shapes the engine reasons
about, so the whole pipeline can be tested against recorded fixtures with no
microphone, no GPU and no optional dependency installed (ARCHITECTURE section 11).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Iterator, Protocol, Sequence, runtime_checkable

from jarvis.common import utc_now

__all__ = [
    "SAMPLE_RATE",
    "FRAME_MILLISECONDS",
    "AudioFormat",
    "AudioChunk",
    "AudioDevice",
    "Transcript",
    "TranscriptSegment",
    "WakeEvent",
    "SpeechSegment",
    "SynthesisResult",
    "VoiceDescription",
    "WakeDetector",
    "SttProvider",
    "TtsProvider",
    "AudioUnavailable",
]

#: 16 kHz mono is what both openWakeWord and faster-whisper expect. Resampling
#: happens once, at capture, rather than in three places downstream.
SAMPLE_RATE = 16_000

#: Wake detection works on 80 ms frames. Everything upstream uses the same size
#: so a frame never has to be re-cut between components.
FRAME_MILLISECONDS = 80


class AudioUnavailable(RuntimeError):
    """An audio component cannot run, and says which and why."""


class AudioFormat(str, Enum):
    PCM16 = "pcm_s16le"
    FLOAT32 = "float32"


@dataclass(frozen=True)
class AudioChunk:
    """A block of mono audio. ``samples`` is raw bytes, never a file path."""

    samples: bytes
    sample_rate: int = SAMPLE_RATE
    audio_format: AudioFormat = AudioFormat.FLOAT32
    captured_at: datetime = field(default_factory=utc_now)

    @property
    def frame_count(self) -> int:
        width = 2 if self.audio_format is AudioFormat.PCM16 else 4
        return len(self.samples) // width

    @property
    def duration_seconds(self) -> float:
        return self.frame_count / self.sample_rate if self.sample_rate else 0.0


@dataclass(frozen=True)
class AudioDevice:
    """An input or output device the user can choose (PRD FR-016)."""

    index: int
    name: str
    channels: int
    default_sample_rate: float
    is_input: bool
    is_default: bool = False

    def describe(self) -> str:
        suffix = " (default)" if self.is_default else ""
        return f"{self.name}{suffix}"


@dataclass(frozen=True)
class TranscriptSegment:
    text: str
    start_seconds: float
    end_seconds: float
    confidence: float | None = None


@dataclass(frozen=True)
class Transcript:
    """What was said. ``confidence`` gates confirmation (PRD FR-023)."""

    text: str
    language: str = "en"
    confidence: float | None = None
    segments: tuple[TranscriptSegment, ...] = ()
    duration_seconds: float = 0.0
    model: str = ""

    @property
    def empty(self) -> bool:
        return not self.text.strip()


@dataclass(frozen=True)
class WakeEvent:
    """The wake phrase was detected."""

    phrase: str
    score: float
    detected_at: datetime = field(default_factory=utc_now)
    #: True when detection happened while Jarvis was speaking and survived the
    #: self-echo checks (ADR-0028).
    during_playback: bool = False


@dataclass(frozen=True)
class SpeechSegment:
    """Voice activity bounds for one command (PRD FR-014)."""

    audio: AudioChunk
    started_at: datetime
    ended_at: datetime
    ended_because: str = "silence"


@dataclass(frozen=True)
class VoiceDescription:
    """A selectable voice, with the licence metadata FR-032 requires."""

    voice_id: str
    name: str
    provider: str
    language: str
    licence: str = "unknown"
    licence_url: str | None = None
    redistributable: bool = False
    sample_rate_hz: int = 24_000

    def describe(self) -> str:
        return f"{self.name} ({self.provider}, {self.language}, licence {self.licence})"


@dataclass(frozen=True)
class SynthesisResult:
    audio: AudioChunk
    voice_id: str
    text: str
    #: Set when the text was altered before speaking — for example because it
    #: contained something that must not be spoken aloud (PRD FR-034).
    redacted: bool = False


@runtime_checkable
class WakeDetector(Protocol):
    """Streams frames in, yields a wake event when the phrase is heard."""

    @property
    def available(self) -> bool:
        ...

    def unavailable_reason(self) -> str | None:
        ...

    def stream(self, frames: Iterator[AudioChunk]) -> Iterator[WakeEvent]:
        ...

    def reset(self) -> None:
        ...


@runtime_checkable
class SttProvider(Protocol):
    """Audio in, transcript out. Local by default (PRD FR-020)."""

    @property
    def available(self) -> bool:
        ...

    def unavailable_reason(self) -> str | None:
        ...

    def transcribe(self, audio: AudioChunk) -> Transcript:
        ...


@runtime_checkable
class TtsProvider(Protocol):
    """Text in, audio out. Local by default (PRD FR-030)."""

    @property
    def available(self) -> bool:
        ...

    def unavailable_reason(self) -> str | None:
        ...

    def voices(self) -> Sequence[VoiceDescription]:
        ...

    def synthesise(self, text: str, *, voice_id: str | None = None, speed: float = 1.0) -> SynthesisResult:
        ...
