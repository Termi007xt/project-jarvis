"""Short audio cues, so Jarvis is legible without looking at the screen.

The product is voice-first and lives in the tray, which means the user is
usually not looking at it. Without a sound there is no way to tell the
difference between "it did not hear me", "it heard me and is listening", and
"it is thinking" — the window is the only feedback, and needing the window
defeats the point.

Generated rather than shipped as files: three sine tones with a short fade cost
nothing, need no licence, and cannot go missing from an install.

Deliberately quiet and short. A cue that is louder or longer than it needs to be
becomes the most irritating part of the product very quickly.
"""

from __future__ import annotations

import logging
import math
from typing import Sequence

from jarvis.audio.ports import AudioChunk, AudioFormat

__all__ = ["Cue", "cue_audio", "CUE_SAMPLE_RATE"]

_LOG = logging.getLogger(__name__)

CUE_SAMPLE_RATE = 24_000

#: Peak amplitude. Low on purpose — these play while the microphone is open.
_AMPLITUDE = 0.18

#: Fade applied to both ends of every tone. Without it the abrupt start and
#: stop produce an audible click that sounds like a fault.
_FADE_SECONDS = 0.012


class Cue:
    """The cues this build makes, and what each one means."""

    #: The wake phrase was accepted and Jarvis is now recording a command.
    #: Rising, because something is beginning.
    WAKE = "wake"

    #: The command was captured and is being worked on. Lower and single, so it
    #: is clearly a different event from the wake cue.
    THINKING = "thinking"

    #: Nothing usable was heard, or the attempt was abandoned. Falling.
    FAILED = "failed"


#: (frequency Hz, seconds) pairs, played in order.
_TONES: dict[str, Sequence[tuple[float, float]]] = {
    Cue.WAKE: ((880.0, 0.07), (1318.5, 0.09)),
    Cue.THINKING: ((587.3, 0.10),),
    Cue.FAILED: ((587.3, 0.09), (392.0, 0.12)),
}


def cue_audio(name: str, sample_rate: int = CUE_SAMPLE_RATE) -> AudioChunk | None:
    """Render one cue, or None if numpy is unavailable or the name is unknown.

    Never raises: a missing cue must not stop the thing it was announcing.
    """
    tones = _TONES.get(name)
    if tones is None:
        _LOG.debug("no such cue: %s", name)
        return None
    try:
        import numpy  # noqa: PLC0415 - lazy, like the rest of the audio stack
    except ImportError:
        return None

    pieces = []
    for frequency, seconds in tones:
        count = max(1, int(sample_rate * seconds))
        time_axis = numpy.arange(count, dtype=numpy.float32) / sample_rate
        wave = numpy.sin(2.0 * math.pi * frequency * time_axis) * _AMPLITUDE
        pieces.append(_faded(wave, sample_rate, numpy))

    combined = numpy.concatenate(pieces).astype(numpy.float32)
    return AudioChunk(
        samples=combined.tobytes(),
        sample_rate=sample_rate,
        audio_format=AudioFormat.FLOAT32,
    )


def _faded(wave, sample_rate: int, numpy):
    """Taper both ends, or the tone starts and stops with a click."""
    fade = min(int(sample_rate * _FADE_SECONDS), len(wave) // 2)
    if fade <= 0:
        return wave
    ramp = numpy.linspace(0.0, 1.0, fade, dtype=numpy.float32)
    wave[:fade] *= ramp
    wave[-fade:] *= ramp[::-1]
    return wave
