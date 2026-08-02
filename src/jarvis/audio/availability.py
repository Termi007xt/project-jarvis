"""What of the voice stack is actually usable right now (ADR-0010, NFR-014).

Audio dependencies are an **optional extra**, not core requirements: Kokoro and
faster-whisper pull in torch and onnxruntime, CI runs on Linux with no
microphone or GPU, and ARCHITECTURE section 11 requires that no test need any of
those. So every provider imports lazily and every screen asks here first.

The rule this module exists to serve is that a missing dependency produces a
*named, honest* unavailable state — "faster-whisper is not installed, run
`pip install -e .[voice]`" — never a silent fallback and never a screen that
looks like it works.

Detection uses ``importlib.util.find_spec``, which locates a module without
importing it. Importing torch to find out whether torch exists would cost
seconds of start-up and several hundred megabytes of memory.
"""

from __future__ import annotations

import importlib.util
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

__all__ = [
    "ComponentStatus",
    "VoiceStackStatus",
    "describe_voice_stack",
    "module_available",
    "VOICE_EXTRA_HINT",
]

VOICE_EXTRA_HINT = "install the optional voice dependencies with: pip install -e .[voice]"


@lru_cache(maxsize=64)
def module_available(module: str) -> bool:
    """True if ``module`` could be imported, without importing it."""
    try:
        return importlib.util.find_spec(module) is not None
    except (ImportError, ValueError):
        # A namespace package with a broken parent raises rather than returning
        # None. Unimportable is unavailable either way.
        return False


@dataclass(frozen=True)
class ComponentStatus:
    """One part of the voice stack, and why it is or is not usable."""

    name: str
    available: bool
    detail: str
    requirement: str = ""

    def describe(self) -> str:
        return f"{self.name}: {'available' if self.available else 'unavailable'} — {self.detail}"


@dataclass(frozen=True)
class VoiceStackStatus:
    capture: ComponentStatus
    speech_to_text: ComponentStatus
    text_to_speech: ComponentStatus
    wake_word: ComponentStatus

    @property
    def components(self) -> tuple[ComponentStatus, ...]:
        return (self.capture, self.speech_to_text, self.text_to_speech, self.wake_word)

    @property
    def any_available(self) -> bool:
        return any(component.available for component in self.components)

    @property
    def fully_available(self) -> bool:
        return all(component.available for component in self.components)

    def missing(self) -> tuple[ComponentStatus, ...]:
        return tuple(c for c in self.components if not c.available)

    def summary(self) -> str:
        if self.fully_available:
            return "all four components available"
        missing = self.missing()
        if len(missing) == len(self.components):
            return f"not installed ({VOICE_EXTRA_HINT})"
        return f"{len(self.components) - len(missing)}/4 available; missing: " + ", ".join(
            component.name for component in missing
        )

    def describe(self) -> str:
        return "\n".join(component.describe() for component in self.components)


def _capture_status() -> ComponentStatus:
    missing = [m for m in ("sounddevice", "soundfile", "numpy") if not module_available(m)]
    if missing:
        return ComponentStatus(
            name="Audio capture and playback",
            available=False,
            detail=f"missing {', '.join(missing)}; {VOICE_EXTRA_HINT}",
            requirement="sounddevice, soundfile, numpy",
        )
    return ComponentStatus(
        name="Audio capture and playback",
        available=True,
        detail="sounddevice and soundfile are installed",
        requirement="sounddevice, soundfile, numpy",
    )


def _stt_status(model: str = "small") -> ComponentStatus:
    if not module_available("faster_whisper"):
        return ComponentStatus(
            name="Speech recognition",
            available=False,
            detail=f"faster-whisper is not installed; {VOICE_EXTRA_HINT}",
            requirement="faster-whisper",
        )
    return ComponentStatus(
        name="Speech recognition",
        available=True,
        detail=f"faster-whisper is installed; configured model '{model}'",
        requirement="faster-whisper",
    )


def _tts_status(provider: str = "kokoro", voice: str | None = None) -> ComponentStatus:
    if provider == "kokoro":
        if not module_available("kokoro"):
            return ComponentStatus(
                name="Voice output",
                available=False,
                detail=f"kokoro is not installed; {VOICE_EXTRA_HINT}",
                requirement="kokoro, torch",
            )
        return ComponentStatus(
            name="Voice output",
            available=True,
            detail=f"Kokoro is installed; configured voice '{voice or 'unset'}'",
            requirement="kokoro, torch",
        )
    if provider == "windows_sapi":
        available = module_available("win32com") or module_available("comtypes")
        return ComponentStatus(
            name="Voice output",
            available=available,
            detail=(
                "Windows SAPI is reachable"
                if available
                else "Windows SAPI needs pywin32 or comtypes"
            ),
            requirement="pywin32 or comtypes",
        )
    return ComponentStatus(
        name="Voice output",
        available=False,
        detail=f"'{provider}' is not a provider this build implements",
        requirement=provider,
    )


def _wake_status(model_path: Path | None = None) -> ComponentStatus:
    if not module_available("openwakeword"):
        return ComponentStatus(
            name="Wake word",
            available=False,
            detail=f"openwakeword is not installed; {VOICE_EXTRA_HINT}",
            requirement="openwakeword",
        )
    if model_path is None or not model_path.exists():
        # ADR-0016: no wake-word artefact ships with the product, and none is
        # present on the development machine. Push-to-talk is the fallback.
        return ComponentStatus(
            name="Wake word",
            available=False,
            detail=(
                "openwakeword is installed but no 'Hey Jarvis' base model is "
                "present. Wake detection stays off and push-to-talk is used "
                "instead (ADR-0016)."
            ),
            requirement="openwakeword base model",
        )
    return ComponentStatus(
        name="Wake word",
        available=True,
        detail=f"base model at {model_path}",
        requirement="openwakeword",
    )


def describe_voice_stack(config: object | None = None, model_path: Path | None = None) -> VoiceStackStatus:
    """Report each component's real state, reading configuration when given."""
    stt_model = "small"
    tts_provider = "kokoro"
    tts_voice: str | None = None

    audio = getattr(config, "audio", None)
    if audio is not None:
        stt_model = getattr(audio.speech_to_text, "model", stt_model)
        profiles = getattr(audio.text_to_speech, "profiles", {})
        active = getattr(audio.text_to_speech, "active_profile", "")
        profile = profiles.get(active) if isinstance(profiles, dict) else None
        if profile is not None:
            tts_provider = getattr(profile, "provider", tts_provider)
            tts_voice = getattr(profile, "voice", None)

    return VoiceStackStatus(
        capture=_capture_status(),
        speech_to_text=_stt_status(stt_model),
        text_to_speech=_tts_status(tts_provider, tts_voice),
        wake_word=_wake_status(model_path),
    )
