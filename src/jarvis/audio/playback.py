"""Audio playback (PRD FR-030, FR-033, ADR-0028).

The missing half of the voice stack. Synthesis produced an :class:`AudioChunk`
and nothing ever played it, so ``voice.speak`` reported "Spoken." while the room
stayed silent — a verified-success claim for something that never happened
(PRD FR-048).

Two obligations shape this module:

* **Playback must be interruptible.** ADR-0028 gives barge-in a contract the
  coordinator already declares — ``DuplexCoordinator.stop_requested`` is
  documented as "polled by the playback loop between buffers". This is that
  loop. Audio goes out in short blocks and the flag is checked between each, so
  an interruption is heard within a block rather than at the end of a sentence.
* **It must report what actually happened.** Playback returns how much audio
  reached the device and whether it finished, because the caller has to be able
  to tell the truth about it afterwards.

``sounddevice`` is imported inside the functions that need it, exactly as in
:mod:`jarvis.audio.capture`, so this module imports with no voice extra present.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Callable

from jarvis.audio.availability import VOICE_EXTRA_HINT, module_available
from jarvis.audio.ports import AudioChunk, AudioFormat, AudioUnavailable

__all__ = [
    "playback_available",
    "playback_unavailable_reason",
    "default_output_device",
    "play",
    "PlaybackReport",
]

_LOG = logging.getLogger(__name__)

#: Audio is written in blocks of this many milliseconds. The stop flag is
#: checked between blocks, so this is also the worst-case barge-in latency.
#: Short enough to feel immediate, long enough not to underrun.
BLOCK_MILLISECONDS = 40

#: A single utterance may not hold the output device longer than this. Without
#: a bound, a runaway synthesis would occupy the speakers indefinitely.
MAX_PLAYBACK_SECONDS = 300.0


@dataclass(frozen=True)
class PlaybackReport:
    """What playback actually did. Never assumed by the caller."""

    played: bool
    seconds: float
    interrupted: bool = False
    error: str | None = None

    def describe(self) -> str:
        if self.error:
            return f"nothing was played: {self.error}"
        if self.interrupted:
            return f"interrupted after {self.seconds:.1f}s"
        if not self.played:
            return "nothing was played"
        return f"played {self.seconds:.1f}s of audio"


def playback_available() -> bool:
    return module_available("sounddevice") and module_available("numpy")


def playback_unavailable_reason() -> str | None:
    if playback_available():
        return None
    return f"audio playback needs sounddevice and numpy; {VOICE_EXTRA_HINT}"


def _require_sounddevice():
    reason = playback_unavailable_reason()
    if reason is not None:
        raise AudioUnavailable(reason)
    import sounddevice  # noqa: PLC0415 - lazy by design

    return sounddevice


def default_output_device() -> int | None:
    """The device index Windows would pick, or None if it cannot be read."""
    if not playback_available():
        return None
    try:
        sounddevice = _require_sounddevice()
        _, default_out = sounddevice.default.device
        return int(default_out) if default_out is not None and default_out >= 0 else None
    except Exception:  # noqa: BLE001 - never break a caller over device query
        _LOG.exception("could not read the default output device")
        return None


def _as_float_array(chunk: AudioChunk):
    """Decode the chunk's bytes into the float32 mono array a stream wants."""
    import numpy  # noqa: PLC0415 - lazy by design

    if chunk.audio_format is AudioFormat.PCM16:
        samples = numpy.frombuffer(chunk.samples, dtype=numpy.int16)
        return (samples.astype(numpy.float32) / 32768.0).reshape(-1)
    return numpy.frombuffer(chunk.samples, dtype=numpy.float32).reshape(-1)


def play(
    chunk: AudioChunk,
    *,
    device_index: int | None = None,
    should_stop: Callable[[], bool] | None = None,
    on_block: Callable[[AudioChunk], None] | None = None,
    max_seconds: float = MAX_PLAYBACK_SECONDS,
) -> PlaybackReport:
    """Play one chunk, blocking, and report what was heard.

    Blocking by design: the caller is already on a worker thread, and the tool
    contract wants the outcome, not a promise. ``should_stop`` is polled between
    blocks so barge-in cuts the audio mid-sentence (ADR-0028); ``on_block``
    receives what was emitted, which is how the duplex coordinator learns how
    loud Jarvis's own voice was for echo attribution.
    """
    if chunk.frame_count == 0:
        return PlaybackReport(played=False, seconds=0.0, error="there was no audio to play")

    reason = playback_unavailable_reason()
    if reason is not None:
        return PlaybackReport(played=False, seconds=0.0, error=reason)

    try:
        sounddevice = _require_sounddevice()
        audio = _as_float_array(chunk)
    except Exception as exc:  # noqa: BLE001 - reported, never raised at a tool
        _LOG.exception("could not prepare audio for playback")
        return PlaybackReport(played=False, seconds=0.0, error=str(exc))

    rate = chunk.sample_rate or 24_000
    block = max(1, int(rate * BLOCK_MILLISECONDS / 1000))
    limit = min(len(audio), int(rate * max_seconds))
    if limit < len(audio):
        _LOG.warning(
            "truncating playback at %.0fs; the utterance was %.0fs",
            max_seconds,
            len(audio) / rate,
        )

    played_samples = 0
    interrupted = False
    try:
        stream = sounddevice.OutputStream(
            samplerate=rate,
            channels=1,
            dtype="float32",
            device=device_index,
            blocksize=block,
        )
        with stream:
            for start in range(0, limit, block):
                if should_stop is not None and should_stop():
                    interrupted = True
                    break
                piece = audio[start : start + block]
                stream.write(piece)
                played_samples += len(piece)
                if on_block is not None:
                    on_block(
                        AudioChunk(
                            samples=piece.tobytes(),
                            sample_rate=rate,
                            audio_format=AudioFormat.FLOAT32,
                        )
                    )
    except Exception as exc:  # noqa: BLE001 - a dead speaker is not a crash
        _LOG.exception("playback failed")
        return PlaybackReport(
            played=played_samples > 0,
            seconds=played_samples / rate if rate else 0.0,
            interrupted=interrupted,
            error=str(exc),
        )

    seconds = played_samples / rate if rate else 0.0
    return PlaybackReport(played=played_samples > 0, seconds=seconds, interrupted=interrupted)
