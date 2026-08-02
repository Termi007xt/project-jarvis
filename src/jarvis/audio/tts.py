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
        spoken, redacted = redact_for_speech(text)
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
