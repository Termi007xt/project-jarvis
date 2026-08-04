"""Wake-word detection and per-user enrolment (ADR-0016, PRD FR-010, FR-011).

ADR-0016 chose **Path 1**: a pretrained base model with a personal verifier
fitted from a small number of the user's own recordings. That choice constrains
the phrase, and the constraint is not something to be quiet about:

* openWakeWord ships a pretrained **"Hey Jarvis"** model. It does **not** ship
  one for the bare word "Jarvis" — that is exactly what the deferred Path 2
  exists to serve.
* FR-011 names "Jarvis" as the product default *and* forbids the GUI implying
  that a model trained for "Hey Jarvis" detects "Jarvis" alone. So this module
  reports the phrase it actually detects, and :func:`phrase_disclosure` is the
  sentence the Voice screen must show. Nothing here will label itself "Jarvis".

The base model is **not shipped and not present** by default. Phase 1 has to
obtain it, and until it exists wake detection reports itself unavailable and
push-to-talk is the activation route (ADR-0027).

Enrolment is not "we trained a model". ADR-0016's decision criterion 1 requires
a *measured* false-accept and false-reject indication from held-out samples
before always-listening is enabled, and :class:`EnrolmentMeasurement` is that
measurement. Below the bar, Jarvis says so plainly.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterator, Sequence

from jarvis.audio.availability import VOICE_EXTRA_HINT, module_available
from jarvis.audio.ports import SAMPLE_RATE, AudioChunk, AudioFormat, WakeEvent
from jarvis.common import utc_now

__all__ = [
    "OpenWakeWordDetector",
    "NullWakeDetector",
    "EnrolmentSample",
    "EnrolmentMeasurement",
    "EnrolmentResult",
    "measure_enrolment",
    "build_wake_detector",
    "phrase_disclosure",
    "wake_model_path",
    "PHASE_1_PHRASE",
    "DESIRED_PHRASE",
    "DEFAULT_THRESHOLD",
    "MINIMUM_SAMPLES",
    "QUALITY_BAR",
]

_LOG = logging.getLogger(__name__)

#: What Phase 1 can honestly detect, per ADR-0016 Path 1.
PHASE_1_PHRASE = "Hey Jarvis"

#: What FR-011 names as the product default, and what Path 2 would unlock.
DESIRED_PHRASE = "Jarvis"

#: Score above which a frame counts as a detection, before playback gating.
#:
#: 0.6 rather than the more usual 0.5, on measurement rather than taste. Against
#: synthesised speech on this build, "Hey Jarvis" scored 0.994-0.998 while the
#: near-miss "Hey Travis" scored 0.489 — only 0.011 below a 0.5 threshold. 0.6
#: keeps every genuine utterance (the weakest was 0.994) and roughly doubles the
#: margin against the closest confusable phrase. Per-user enrolment will refit
#: this to the actual speaker (ADR-0016).
DEFAULT_THRESHOLD = 0.6

#: Fewer recordings than this cannot support a held-out measurement at all.
MINIMUM_SAMPLES = 6

#: ADR-0016 criterion 2: always-listening stays off below this.
QUALITY_BAR = 0.8


def phrase_disclosure(enrolled_phrase: str = PHASE_1_PHRASE) -> str:
    """The sentence the Voice screen must show (FR-011).

    It states the phrase actually detected and says plainly that the bare word
    is not available, so nothing implies a capability that does not exist.
    """
    return (
        f'Jarvis listens for "{enrolled_phrase}". The single word '
        f'"{DESIRED_PHRASE}" is not available in this build: it needs a wake-word '
        "model trained for a single-word phrase, which is planned work and not "
        "something the current model can do. Push-to-talk works regardless."
    )


def wake_model_path(vault_root: Path) -> Path:
    """Where the pretrained base model is expected to live (PRD section 17.2).

    Installed by ``jarvis.audio.wake_install`` on explicit user action; never
    bundled and never committed.
    """
    from jarvis.audio.wake_install import WAKE_MODEL_FILENAME, model_directory

    return model_directory(vault_root) / WAKE_MODEL_FILENAME


@dataclass(frozen=True)
class EnrolmentSample:
    """One recording of the user saying the phrase. Personal data (criterion 3)."""

    sample_id: str
    audio: AudioChunk
    recorded_at: datetime
    score: float | None = None


@dataclass(frozen=True)
class EnrolmentMeasurement:
    """The measured result. ADR-0016 criterion 1: without this, no enabling."""

    accepted_positive: int
    total_positive: int
    accepted_negative: int
    total_negative: int
    threshold: float

    @property
    def true_accept_rate(self) -> float:
        return self.accepted_positive / self.total_positive if self.total_positive else 0.0

    @property
    def false_accept_rate(self) -> float:
        return self.accepted_negative / self.total_negative if self.total_negative else 0.0

    @property
    def false_reject_rate(self) -> float:
        return 1.0 - self.true_accept_rate

    @property
    def passed(self) -> bool:
        """Good enough to enable always-listening (criterion 2)."""
        return self.true_accept_rate >= QUALITY_BAR and self.false_accept_rate <= 0.1

    def describe(self) -> str:
        if not self.total_positive:
            return "Not measured — no held-out samples were available."
        return (
            f"Detected {self.accepted_positive} of {self.total_positive} held-out "
            f"recordings of your phrase ({self.true_accept_rate:.0%}), and "
            f"{self.accepted_negative} of {self.total_negative} recordings that were "
            f"not the phrase ({self.false_accept_rate:.0%} false activations), at "
            f"threshold {self.threshold:.2f}."
        )

    def verdict(self) -> str:
        if self.passed:
            return "Good enough to listen continuously."
        return (
            "Not good enough to listen continuously, so always-listening stays "
            "off and push-to-talk remains the way to talk to Jarvis. Re-record "
            "your samples somewhere quieter, or keep using push-to-talk."
        )


@dataclass(frozen=True)
class EnrolmentResult:
    phrase: str
    threshold: float
    measurement: EnrolmentMeasurement
    sample_count: int
    enrolled_at: datetime

    @property
    def always_listening_allowed(self) -> bool:
        return self.measurement.passed


def measure_enrolment(
    positive_scores: Sequence[float],
    negative_scores: Sequence[float],
    *,
    threshold: float = DEFAULT_THRESHOLD,
) -> EnrolmentMeasurement:
    """Score held-out positives and negatives at a threshold.

    Kept free of any model so the measurement itself is testable, and so the
    quality bar is enforced by arithmetic rather than by a library's opinion.
    """
    return EnrolmentMeasurement(
        accepted_positive=sum(1 for score in positive_scores if score >= threshold),
        total_positive=len(positive_scores),
        accepted_negative=sum(1 for score in negative_scores if score >= threshold),
        total_negative=len(negative_scores),
        threshold=threshold,
    )


def choose_threshold(
    positive_scores: Sequence[float],
    negative_scores: Sequence[float],
    *,
    candidates: Sequence[float] = (0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9),
) -> tuple[float, EnrolmentMeasurement]:
    """Pick the threshold that separates this speaker best.

    This is the personal part of "personal verifier": the same base model with
    a threshold fitted to one voice, one microphone and one room.
    """
    best: tuple[float, EnrolmentMeasurement] | None = None
    for candidate in candidates:
        measurement = measure_enrolment(positive_scores, negative_scores, threshold=candidate)
        score = measurement.true_accept_rate - measurement.false_accept_rate
        if best is None or score > (
            best[1].true_accept_rate - best[1].false_accept_rate
        ):
            best = (candidate, measurement)
    assert best is not None
    return best


class NullWakeDetector:
    """No wake detection. Says exactly why, and never fabricates an event."""

    def __init__(self, reason: str) -> None:
        self._reason = reason

    @property
    def available(self) -> bool:
        return False

    def unavailable_reason(self) -> str | None:
        return self._reason

    def stream(self, frames: Iterator[AudioChunk]) -> Iterator[WakeEvent]:
        # Consume nothing and yield nothing. A detector that cannot hear must
        # not silently swallow the audio either.
        return iter(())

    def reset(self) -> None:
        return None


class OpenWakeWordDetector:
    """openWakeWord over a pretrained base model, with a personal threshold."""

    def __init__(
        self,
        vault_root: Path,
        *,
        phrase: str = PHASE_1_PHRASE,
        threshold: float = DEFAULT_THRESHOLD,
    ) -> None:
        self._vault_root = Path(vault_root)
        self._model_path = wake_model_path(self._vault_root)
        self._phrase = phrase
        self._threshold = threshold
        self._model = None

    @property
    def model_path(self) -> Path:
        return self._model_path

    @property
    def phrase(self) -> str:
        return self._phrase

    @property
    def threshold(self) -> float:
        return self._threshold

    def set_threshold(self, threshold: float) -> None:
        """Applied after enrolment measurement chooses one."""
        self._threshold = threshold

    @property
    def available(self) -> bool:
        from jarvis.audio.wake_install import missing_files

        return module_available("openwakeword") and not missing_files(
            self._vault_root
        )

    def unavailable_reason(self) -> str | None:
        from jarvis.audio.wake_install import missing_files

        if not module_available("openwakeword"):
            return f"openwakeword is not installed; {VOICE_EXTRA_HINT}"
        missing = missing_files(self._vault_root)
        if missing:
            # ADR-0016: no artefact ships with the product. Say what is missing
            # and how to get it, rather than only that it is absent.
            return (
                f'No "{self._phrase}" wake-word model is installed, so Jarvis is '
                "not listening for a wake phrase. Push-to-talk still works. "
                f"Missing: {', '.join(missing)}. Install it with "
                "`python -m jarvis.main --install-wake-model`, which downloads it "
                f"to {self._model_path.parent}."
            )
        return None

    def load(self) -> None:
        if self._model is not None:
            return
        reason = self.unavailable_reason()
        if reason is not None:
            from jarvis.audio.ports import AudioUnavailable

            raise AudioUnavailable(reason)
        from openwakeword.model import Model  # noqa: PLC0415 - lazy by design

        from jarvis.audio.wake_install import use_local_models

        _LOG.info("loading wake-word model from %s", self._model_path)
        # ONNX on Windows, and the vault's feature models: the library resolves
        # its defaults relative to its own package directory.
        self._model = Model(
            wakeword_models=[str(self._model_path)], **use_local_models(self._vault_root)
        )

    def reset(self) -> None:
        if self._model is not None and hasattr(self._model, "reset"):
            self._model.reset()

    def score(self, chunk: AudioChunk) -> float:
        """Highest score this frame produced across the loaded models."""
        self.load()
        import numpy  # noqa: PLC0415 - lazy by design

        if chunk.audio_format is AudioFormat.FLOAT32:
            samples = numpy.frombuffer(chunk.samples, dtype=numpy.float32)
            # openWakeWord expects 16-bit PCM.
            samples = (samples * 32767.0).astype(numpy.int16)
        else:
            samples = numpy.frombuffer(chunk.samples, dtype=numpy.int16)
        if samples.size == 0:
            return 0.0
        predictions = self._model.predict(samples)  # type: ignore[union-attr]
        return max((float(value) for value in predictions.values()), default=0.0)

    def stream(self, frames: Iterator[AudioChunk]) -> Iterator[WakeEvent]:
        """Yield an event whenever a frame crosses the threshold."""
        for frame in frames:
            score = self.score(frame)
            if score >= self._threshold:
                yield WakeEvent(phrase=self._phrase, score=score, detected_at=utc_now())
                self.reset()


def build_wake_detector(config: object, vault_root: Path) -> object:
    """Construct the configured detector, or a Null one that explains itself."""
    audio = getattr(config, "audio", None)
    if audio is None:
        return NullWakeDetector("no audio configuration is present")
    settings = audio.wake_word
    if settings.provider != "openwakeword":
        return NullWakeDetector(
            f"'{settings.provider}' is not a wake-word provider this build implements"
        )

    detector = OpenWakeWordDetector(
        vault_root, phrase=settings.phrase or PHASE_1_PHRASE
    )
    if detector.available:
        return detector
    return NullWakeDetector(detector.unavailable_reason() or "wake detection is unavailable")


def silence(seconds: float = 1.0, *, sample_rate: int = SAMPLE_RATE) -> AudioChunk:
    """A block of silence. Used as a negative sample and in tests."""
    return AudioChunk(
        samples=b"\x00" * (int(seconds * sample_rate) * 4),
        sample_rate=sample_rate,
        audio_format=AudioFormat.FLOAT32,
    )
