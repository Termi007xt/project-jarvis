"""Speech to text (PRD FR-020 to FR-025).

faster-whisper `small`, CPU, `int8`, `beam_size=1`, `vad_filter=True` — the
settings verified against a real microphone in `tools/voice-lab/test_whisper.py`,
carried over rather than re-guessed.

Three requirements beyond "audio in, text out":

* **No raw-audio retention by default** (FR-025). ``transcribe`` receives audio
  in memory and returns text. It never takes a path and never writes one, so the
  only way audio reaches disk is if a caller does it deliberately with
  diagnostics enabled — and that path is not in this module. faster-whisper will
  happily accept a filename, which makes writing a temporary WAV on every
  utterance the *convenient* implementation and a silent breach of FR-025; the
  in-memory array path is used instead.
* **The wake phrase is removed** before the command goes anywhere (FR-024).
  Otherwise every command begins with "Hey Jarvis" and the planner has to learn
  to ignore it.
* **Low confidence asks rather than acts** (FR-023). A misheard command that
  could cause an action is confirmed first; the threshold is what makes that
  decidable rather than a matter of taste.
"""

from __future__ import annotations

import logging
import math
import re
from pathlib import Path

from jarvis.audio.availability import VOICE_EXTRA_HINT, module_available
from jarvis.audio.ports import (
    AudioChunk,
    AudioFormat,
    AudioUnavailable,
    Transcript,
    TranscriptSegment,
)

__all__ = [
    "FasterWhisperSttProvider",
    "NullSttProvider",
    "build_stt_provider",
    "strip_wake_phrase",
    "needs_confirmation",
    "CONFIRMATION_THRESHOLD",
]

_LOG = logging.getLogger(__name__)

#: Below this average confidence, a command that could cause an action is
#: confirmed rather than acted on (PRD FR-023).
CONFIRMATION_THRESHOLD = 0.55


def strip_wake_phrase(text: str, phrase: str) -> str:
    """Remove a leading wake phrase (PRD FR-024).

    Only from the start, and only once. "Hey Jarvis, remind me to say hey
    Jarvis" must keep its second occurrence — that is the command, not a wake.
    """
    if not text or not phrase:
        return text.strip()
    words = [re.escape(word) for word in phrase.split() if word]
    if not words:
        return text.strip()
    pattern = re.compile(
        r"^\W*" + r"[\s,.\-]*".join(words) + r"\s*[,.:;!?]*\s*", re.IGNORECASE
    )
    stripped = pattern.sub("", text, count=1).strip()
    if stripped != text.strip():
        return stripped
    return _strip_misheard_wake_word(text, phrase)


#: Greetings that may precede the name and are part of the wake, not the command.
_WAKE_GREETINGS = frozenset(
    {"hey", "hi", "hello", "ok", "okay", "yo", "hey,", "so", "a"}
)


def _strip_misheard_wake_word(text: str, phrase: str) -> str:
    """Remove a leading wake word the recogniser spelled wrong (FR-024).

    The exact match above wants every word of "Hey Jarvis" in order, and what
    actually arrives is whatever faster-whisper made of a word shouted at a
    microphone. Reported by the owner on 2026-08-06:

        Sir: H-Arvis Open MS Edge and Brave
        Jarvis: ... I notice you mentioned "H-Arvis" and "Open MS Edge and
                Brave" - it seems there may have been some text mixed together.

    The wake word then reaches the planner as part of the instruction, and the
    model quite reasonably tries to make sense of it — spending a turn asking
    about a word the owner never said.

    Only the first token or two, only when it is a near-miss of the name, and
    never the whole word: "jar" and "Java" are ordinary words and must survive.
    Matching is on the name alone, because that is the part being misheard —
    "Hey" comes through fine.
    """
    from difflib import SequenceMatcher

    name = (phrase.split() or [""])[-1].casefold()
    if not name:
        return text.strip()

    tokens = text.strip().split()
    if not tokens:
        return text.strip()

    index = 0
    if len(tokens) > 1 and _letters(tokens[0]) in _WAKE_GREETINGS:
        index = 1
    if index >= len(tokens):
        return text.strip()

    candidate = _letters(tokens[index])
    # 0.75 keeps "harvis" (0.83) and "jarviss" (0.92) and rejects "java" (0.4)
    # and "jar" (0.67). A near-miss of a six-letter name is a mishearing; a
    # short word that merely starts the same way is a word.
    if candidate and SequenceMatcher(None, candidate, name).ratio() >= 0.75:
        return " ".join(tokens[index + 1 :]).lstrip(" ,.:;!?").strip()
    return text.strip()


def _letters(token: str) -> str:
    return re.sub(r"[^a-z]", "", token.casefold())


def needs_confirmation(
    transcript: Transcript, *, threshold: float = CONFIRMATION_THRESHOLD
) -> bool:
    """Whether this transcript is too uncertain to act on (PRD FR-023)."""
    if transcript.empty:
        return False
    if transcript.confidence is None:
        # No confidence reported is not the same as high confidence.
        return True
    return transcript.confidence < threshold


class NullSttProvider:
    """No recogniser available. Says why."""

    def __init__(self, reason: str) -> None:
        self._reason = reason

    @property
    def available(self) -> bool:
        return False

    def unavailable_reason(self) -> str | None:
        return self._reason

    def transcribe(self, audio: AudioChunk) -> Transcript:
        raise AudioUnavailable(self._reason)


class FasterWhisperSttProvider:
    """Local transcription. The model is loaded once and kept (preload/keep)."""

    def __init__(
        self,
        *,
        model: str = "small",
        device: str = "cpu",
        compute_type: str = "int8",
        language: str = "en",
        beam_size: int = 1,
        vad_filter: bool = True,
    ) -> None:
        self._model_name = model
        self._device = device
        self._compute_type = compute_type
        self._language = language
        self._beam_size = beam_size
        self._vad_filter = vad_filter
        self._model = None

    @property
    def available(self) -> bool:
        return module_available("faster_whisper") and module_available("numpy")

    def unavailable_reason(self) -> str | None:
        if self.available:
            return None
        return f"faster-whisper is not installed, so Jarvis cannot hear; {VOICE_EXTRA_HINT}"

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def loaded(self) -> bool:
        return self._model is not None

    def load(self) -> None:
        """Load the model. Slow; call it from a worker at start-up."""
        if self._model is not None:
            return
        if not self.available:
            raise AudioUnavailable(self.unavailable_reason() or "faster-whisper unavailable")
        from faster_whisper import WhisperModel  # noqa: PLC0415 - lazy by design

        _LOG.info(
            "loading faster-whisper '%s' on %s (%s)",
            self._model_name, self._device, self._compute_type,
        )
        self._model = WhisperModel(
            self._model_name, device=self._device, compute_type=self._compute_type
        )

    def transcribe(self, audio: AudioChunk) -> Transcript:
        """Audio in, text out. The audio is never written to disk by this method."""
        self.load()
        import numpy  # noqa: PLC0415 - lazy by design

        if audio.audio_format is not AudioFormat.FLOAT32:
            raise ValueError("faster-whisper expects float32 audio")
        samples = numpy.frombuffer(audio.samples, dtype=numpy.float32)
        if samples.size == 0:
            return Transcript(text="", model=self._model_name)

        segments, info = self._model.transcribe(  # type: ignore[union-attr]
            samples,
            language=self._language,
            beam_size=self._beam_size,
            vad_filter=self._vad_filter,
            condition_on_previous_text=False,
        )

        collected: list[TranscriptSegment] = []
        confidences: list[float] = []
        for segment in segments:
            text = (segment.text or "").strip()
            if not text:
                continue
            # avg_logprob is a log probability; exponentiating gives something
            # comparable to a confidence, which is what FR-023 needs.
            confidence = None
            logprob = getattr(segment, "avg_logprob", None)
            if logprob is not None:
                confidence = math.exp(logprob)
                confidences.append(confidence)
            collected.append(
                TranscriptSegment(
                    text=text,
                    start_seconds=float(getattr(segment, "start", 0.0)),
                    end_seconds=float(getattr(segment, "end", 0.0)),
                    confidence=confidence,
                )
            )

        return Transcript(
            text=" ".join(segment.text for segment in collected).strip(),
            language=str(getattr(info, "language", self._language)),
            confidence=(sum(confidences) / len(confidences)) if confidences else None,
            segments=tuple(collected),
            duration_seconds=audio.duration_seconds,
            model=self._model_name,
        )


def build_stt_provider(config: object) -> object:
    audio = getattr(config, "audio", None)
    if audio is None:
        return NullSttProvider("no audio configuration is present")
    settings = audio.speech_to_text
    if settings.provider != "faster_whisper":
        return NullSttProvider(
            f"'{settings.provider}' is not a speech-recognition provider this build implements"
        )
    provider = FasterWhisperSttProvider(
        model=settings.model,
        device=settings.device,
        compute_type=settings.compute_type,
        language=settings.language,
        beam_size=settings.beam_size,
        vad_filter=settings.vad_filter,
    )
    if provider.available:
        return provider
    return NullSttProvider(provider.unavailable_reason() or "faster-whisper is unavailable")


def diagnostic_audio_path(root: Path, name: str) -> Path:
    """Where opt-in diagnostic audio would go (PRD FR-025).

    Exists so the location is defined in one place and is obviously separate
    from the transcription path. Nothing writes here unless the user turns
    diagnostic retention on.
    """
    directory = root / "audio_diagnostics"
    directory.mkdir(parents=True, exist_ok=True)
    return directory / f"{name}.wav"
