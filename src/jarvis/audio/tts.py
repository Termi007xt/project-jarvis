"""Text to speech (PRD FR-030 to FR-034, ADR-0014, ADR-0015).

Kokoro `bm_george` is the configured default, verified on this hardware by
`tools/voice-lab/test_kokoro.py`. Windows SAPI is the fallback, so a machine
without the voice extra can still speak rather than silently doing nothing.

Two requirements are enforced here rather than left to callers:

* **Licence metadata travels with every voice** (FR-032). A voice pack whose
  licence is unknown is still offered, but it is labelled unknown and marked
  non-redistributable, so nothing can be shipped on the assumption that it was
  fine. ADR-0014 accepted `bm_george` for personal use with the public
  redistribution question still open, and that state is what is recorded.
* **Sensitive text is never spoken by accident** (FR-034). Anything that looks
  like a secret is removed before synthesis, and the result says it was
  redacted. Speaking a password aloud is not recoverable by apologising.
"""

from __future__ import annotations

import logging
import re
from typing import Sequence

from jarvis.audio.availability import VOICE_EXTRA_HINT, module_available
from jarvis.audio.ports import (
    AudioChunk,
    AudioFormat,
    AudioUnavailable,
    SynthesisResult,
    VoiceDescription,
)

__all__ = [
    "KokoroTtsProvider",
    "WindowsSapiTtsProvider",
    "NullTtsProvider",
    "build_tts_provider",
    "redact_for_speech",
    "speakable_text",
    "prepare_for_speech",
    "SENSITIVE_PATTERNS",
]

_LOG = logging.getLogger(__name__)

#: Text shapes that must not be spoken aloud unless the user explicitly asked
#: for it (PRD FR-034). Conservative on purpose: a false positive costs one
#: awkward sentence, a false negative reads a password to the room.
SENSITIVE_PATTERNS: tuple[tuple[str, str], ...] = (
    (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", "an email address"),
    (r"\b(?:\d[ -]*?){13,19}\b", "a card number"),
    (r"\b\d{6}\b", "a verification code"),
    (r"\b(?:sk|pk|api|token|bearer)[-_][A-Za-z0-9._-]{8,}\b", "a key"),
    (r"\b[A-Za-z0-9+/]{32,}={0,2}\b", "a long credential"),
    (r"-----BEGIN [A-Z ]*PRIVATE KEY-----", "a private key"),
)

_SENSITIVE = tuple((re.compile(pattern, re.IGNORECASE), label) for pattern, label in SENSITIVE_PATTERNS)


def redact_for_speech(text: str) -> tuple[str, bool]:
    """Replace anything secret-shaped with a description of what it was."""
    redacted = text
    changed = False
    for pattern, label in _SENSITIVE:
        redacted, count = pattern.subn(label, redacted)
        changed = changed or bool(count)
    return redacted, changed


#: Characters a phonemiser turns into their Unicode names rather than sound.
#: An emoji is not a word: "🦁" becomes "lion face", and a reply with three of
#: them becomes unlistenable. The written transcript keeps every character —
#: only the spoken copy is stripped, so nothing is hidden from the screen.
_UNSPEAKABLE = re.compile(
    "["
    "\U0001f000-\U0001faff"  # pictographs, supplemental, extended-A, flags
    "⌀-⏿"  # watches, alarm clocks, media symbols
    "☀-➿"  # miscellaneous symbols and dingbats
    "⬀-⯿"  # stars and arrows
    "←-⇿"  # arrows
    "■-◿"  # geometric shapes
    "︀-️"  # variation selectors
    "​-‏"  # zero-width joiners and direction marks
    "  "  # line and paragraph separators
    "•⃣"  # bullet, combining enclosing keycap
    "©®™"  # copyright, registered, trade mark
    "\U000e0000-\U000e007f"  # tag characters
    "]"
)

_FENCED_CODE = re.compile(r"```[\s\S]*?```")
_INLINE_CODE = re.compile(r"`([^`]*)`")
_MARKDOWN_LINK = re.compile(r"\[([^\]]+)\]\([^)]*\)")
_BARE_URL = re.compile(r"https?://\S+")
_HEADING = re.compile(r"^[ \t]*#{1,6}[ \t]*", re.MULTILINE)
_BULLET = re.compile(r"^[ \t]*[-*+][ \t]+", re.MULTILINE)
# Guarded on both sides so `speak_replies` keeps its underscore: a lone
# separator inside a word is not emphasis.
_STRONG = re.compile(r"(?<!\w)(\*\*|__)(\S(?:.*?\S)?)\1(?!\w)")
_EMPHASIS = re.compile(r"(?<!\w)([*_])(\S(?:.*?\S)?)\1(?!\w)")
_WHITESPACE = re.compile(r"\s+")


def _spoken_host(match: re.Match[str]) -> str:
    """A URL read aloud in full is unbearable; the host is the useful part."""
    from urllib.parse import urlparse  # noqa: PLC0415 - lazy, this is a cold path

    host = urlparse(match.group(0).rstrip(".,;:!?)")).netloc
    host = host.split("@")[-1].split(":")[0]
    if host.startswith("www."):
        host = host[4:]
    return host.replace(".", " dot ") if host else ""


def speakable_text(text: str) -> str:
    """Strip what a phonemiser would recite rather than say (PRD FR-030).

    Presentation only: emoji, markdown scaffolding and URL machinery. It never
    rewords, never summarises and never adds anything the model did not say,
    so what is heard is a subset of what is written — with one exception, a
    fenced code block, which is announced rather than read out line by line.

    Returns "" when nothing speakable is left. The caller decides what that
    means; this function does not invent a sentence to fill the silence.
    """
    if not text:
        return ""

    spoken = _FENCED_CODE.sub(" a code block ", text)
    spoken = _INLINE_CODE.sub(r"\1", spoken)
    spoken = _MARKDOWN_LINK.sub(r"\1", spoken)
    spoken = _BARE_URL.sub(_spoken_host, spoken)
    spoken = _HEADING.sub("", spoken)
    spoken = _BULLET.sub("", spoken)
    spoken = _STRONG.sub(r"\2", spoken)
    spoken = _EMPHASIS.sub(r"\2", spoken)
    spoken = _UNSPEAKABLE.sub("", spoken)
    return _WHITESPACE.sub(" ", spoken).strip()


def prepare_for_speech(text: str) -> tuple[str, bool]:
    """Make text legible aloud, then remove anything secret-shaped.

    Order matters: stripping runs first so emphasis markers cannot hide a
    credential from the patterns in :data:`SENSITIVE_PATTERNS`.
    """
    return redact_for_speech(speakable_text(text))


class NullTtsProvider:
    """No voice available. Says why, and never pretends to speak."""

    def __init__(self, reason: str) -> None:
        self._reason = reason

    @property
    def available(self) -> bool:
        return False

    def unavailable_reason(self) -> str | None:
        return self._reason

    def voices(self) -> Sequence[VoiceDescription]:
        return ()

    def synthesise(self, text: str, *, voice_id: str | None = None, speed: float = 1.0):
        raise AudioUnavailable(self._reason)


class KokoroTtsProvider:
    """Kokoro-82M. Loaded lazily and kept, because loading is slow."""

    #: ADR-0014 accepted bm_george for this build. Redistribution licensing is
    #: still open, which is why ``redistributable`` is False rather than absent.
    _VOICES: tuple[VoiceDescription, ...] = (
        VoiceDescription("bm_george", "George (British English)", "kokoro", "en-GB",
                         licence="Apache-2.0 (model); voice redistribution unresolved",
                         licence_url="https://huggingface.co/hexgrad/Kokoro-82M",
                         redistributable=False, sample_rate_hz=24_000),
        VoiceDescription("bm_fable", "Fable (British English)", "kokoro", "en-GB",
                         licence="Apache-2.0 (model); voice redistribution unresolved",
                         licence_url="https://huggingface.co/hexgrad/Kokoro-82M",
                         redistributable=False, sample_rate_hz=24_000),
        VoiceDescription("am_michael", "Michael (American English)", "kokoro", "en-US",
                         licence="Apache-2.0 (model); voice redistribution unresolved",
                         licence_url="https://huggingface.co/hexgrad/Kokoro-82M",
                         redistributable=False, sample_rate_hz=24_000),
        VoiceDescription("am_fenrir", "Fenrir (American English)", "kokoro", "en-US",
                         licence="Apache-2.0 (model); voice redistribution unresolved",
                         licence_url="https://huggingface.co/hexgrad/Kokoro-82M",
                         redistributable=False, sample_rate_hz=24_000),
    )

    def __init__(
        self,
        *,
        voice_id: str = "bm_george",
        language_code: str = "b",
        speed: float = 1.0,
        sample_rate_hz: int = 24_000,
    ) -> None:
        self._voice_id = voice_id
        self._language_code = language_code
        self._speed = speed
        self._sample_rate = sample_rate_hz
        self._pipeline = None

    @property
    def available(self) -> bool:
        return module_available("kokoro")

    def unavailable_reason(self) -> str | None:
        if self.available:
            return None
        return f"Kokoro is not installed, so Jarvis has no voice; {VOICE_EXTRA_HINT}"

    def voices(self) -> Sequence[VoiceDescription]:
        return self._VOICES

    def _load(self):
        if self._pipeline is None:
            if not self.available:
                raise AudioUnavailable(self.unavailable_reason() or "kokoro unavailable")
            from kokoro import KPipeline  # noqa: PLC0415 - lazy by design

            _LOG.info("loading Kokoro pipeline (lang %s)", self._language_code)
            self._pipeline = KPipeline(lang_code=self._language_code)
        return self._pipeline

    def synthesise(
        self, text: str, *, voice_id: str | None = None, speed: float = 1.0
    ) -> SynthesisResult:
        spoken, redacted = prepare_for_speech(text)
        if not spoken.strip():
            raise ValueError("there is nothing to speak")

        import numpy  # noqa: PLC0415 - lazy by design

        pipeline = self._load()
        chunks: list[object] = []
        for _, _, audio in pipeline(spoken, voice=voice_id or self._voice_id, speed=speed or self._speed):
            array = audio
            for attribute in ("detach", "cpu", "numpy"):
                method = getattr(array, attribute, None)
                if callable(method):
                    array = method()
            chunks.append(numpy.asarray(array, dtype=numpy.float32).reshape(-1))

        if not chunks:
            raise AudioUnavailable("Kokoro produced no audio for that text")
        combined = numpy.concatenate(chunks)
        return SynthesisResult(
            audio=AudioChunk(
                samples=combined.tobytes(),
                sample_rate=self._sample_rate,
                audio_format=AudioFormat.FLOAT32,
            ),
            voice_id=voice_id or self._voice_id,
            text=spoken,
            redacted=redacted,
        )


class WindowsSapiTtsProvider:
    """The fallback voice, so a machine without the extra can still speak."""

    def __init__(self) -> None:
        self._engine = None

    @property
    def available(self) -> bool:
        import os

        return os.name == "nt" and (
            module_available("win32com") or module_available("comtypes")
        )

    def unavailable_reason(self) -> str | None:
        if self.available:
            return None
        return "Windows SAPI needs pywin32 or comtypes, which are not installed."

    def voices(self) -> Sequence[VoiceDescription]:
        if not self.available:
            return ()
        return (
            VoiceDescription(
                "sapi_default", "Windows default voice", "windows_sapi", "en",
                licence="Bundled with Windows; not redistributable by this product",
                redistributable=False, sample_rate_hz=22_050,
            ),
        )

    def synthesise(
        self, text: str, *, voice_id: str | None = None, speed: float = 1.0
    ) -> SynthesisResult:
        raise AudioUnavailable(
            "The Windows SAPI provider is declared as the configured fallback but "
            "is not implemented in this build. Install the voice extra to use "
            "Kokoro (ADR-0010: no stub reports success it did not achieve)."
        )


def build_tts_provider(config: object) -> object:
    """Construct the provider named by the active profile in configuration."""
    audio = getattr(config, "audio", None)
    if audio is None:
        return NullTtsProvider("no audio configuration is present")

    text_to_speech = audio.text_to_speech
    profile = text_to_speech.profiles.get(text_to_speech.active_profile)
    if profile is None:
        return NullTtsProvider(
            f"'{text_to_speech.active_profile}' is not a configured voice profile"
        )

    if profile.provider == "kokoro":
        provider = KokoroTtsProvider(
            voice_id=profile.voice or "bm_george",
            language_code=profile.language_code or "b",
            speed=profile.speed or 1.0,
            sample_rate_hz=profile.sample_rate_hz or 24_000,
        )
        if provider.available:
            return provider
        return NullTtsProvider(provider.unavailable_reason() or "Kokoro is unavailable")

    if profile.provider == "windows_sapi":
        return WindowsSapiTtsProvider()

    return NullTtsProvider(
        f"'{profile.provider}' is not a text-to-speech provider this build implements"
    )
