"""The pre-wake ring buffer (PRD FR-012, FR-025, AT-002).

Before a wake phrase is detected, audio may exist **only** in memory and may
never be written to disk. That is the whole requirement, and it is easy to
satisfy by accident and easy to break by accident — a debug dump, a diagnostic
flag defaulting on, a cache that spills.

So this buffer has no file handling of any kind. It cannot write to disk,
because it has no code that could: no path parameter, no open, no serialisation.
The privacy property is structural rather than conditional.

The buffer exists at all because a wake word is recognised slightly *after* the
user starts speaking. Without a short backward window, the first syllable of
every command is lost.
"""

from __future__ import annotations

import threading
from collections import deque
from datetime import datetime

from jarvis.audio.ports import SAMPLE_RATE, AudioChunk, AudioFormat
from jarvis.common import utc_now

__all__ = ["RingBuffer", "DEFAULT_WINDOW_SECONDS"]

#: How much audio is kept behind the present moment. Long enough to recover the
#: run-up to a wake phrase, short enough that it is not a recording.
DEFAULT_WINDOW_SECONDS = 3.0


class RingBuffer:
    """A bounded, in-memory window of the most recent audio.

    Thread-safe: the capture callback writes from an audio thread while the wake
    detector and the command capture read from others.
    """

    def __init__(
        self,
        window_seconds: float = DEFAULT_WINDOW_SECONDS,
        *,
        sample_rate: int = SAMPLE_RATE,
        audio_format: AudioFormat = AudioFormat.FLOAT32,
    ) -> None:
        if window_seconds <= 0:
            raise ValueError("the ring buffer window must be positive")
        self._window_seconds = window_seconds
        self._sample_rate = sample_rate
        self._format = audio_format
        self._sample_width = 2 if audio_format is AudioFormat.PCM16 else 4
        self._max_bytes = int(window_seconds * sample_rate) * self._sample_width
        self._chunks: deque[AudioChunk] = deque()
        self._bytes = 0
        self._lock = threading.RLock()
        self._total_written = 0

    # -- writing -----------------------------------------------------------
    def write(self, chunk: AudioChunk) -> None:
        """Append audio, discarding whatever falls out of the window."""
        if chunk.sample_rate != self._sample_rate:
            raise ValueError(
                f"expected {self._sample_rate} Hz audio, got {chunk.sample_rate} Hz. "
                "Resampling happens once, at capture."
            )
        if chunk.audio_format is not self._format:
            raise ValueError(
                f"expected {self._format.value}, got {chunk.audio_format.value}"
            )
        with self._lock:
            self._chunks.append(chunk)
            self._bytes += len(chunk.samples)
            self._total_written += len(chunk.samples)
            while self._bytes > self._max_bytes and self._chunks:
                oldest = self._chunks.popleft()
                self._bytes -= len(oldest.samples)

    # -- reading -----------------------------------------------------------
    def snapshot(self) -> AudioChunk:
        """Everything currently held, as one chunk. Does not clear the buffer."""
        with self._lock:
            samples = b"".join(chunk.samples for chunk in self._chunks)
            captured_at = self._chunks[0].captured_at if self._chunks else utc_now()
        return AudioChunk(
            samples=samples,
            sample_rate=self._sample_rate,
            audio_format=self._format,
            captured_at=captured_at,
        )

    def snapshot_frames(self) -> tuple[AudioChunk, ...]:
        """The held frames individually, for a consumer that wants to keep going."""
        with self._lock:
            return tuple(self._chunks)

    def take(self) -> AudioChunk:
        """Snapshot and clear, for when a wake event promotes it to a command."""
        with self._lock:
            chunk = self.snapshot()
            self._chunks.clear()
            self._bytes = 0
        return chunk

    def clear(self) -> None:
        """Forget everything held. Called whenever listening stops."""
        with self._lock:
            self._chunks.clear()
            self._bytes = 0

    # -- observation -------------------------------------------------------
    @property
    def held_bytes(self) -> int:
        with self._lock:
            return self._bytes

    @property
    def held_seconds(self) -> float:
        with self._lock:
            return self._bytes / (self._sample_rate * self._sample_width)

    @property
    def window_seconds(self) -> float:
        return self._window_seconds

    @property
    def total_written_bytes(self) -> int:
        """Everything ever accepted, so a test can prove discarding happened."""
        with self._lock:
            return self._total_written

    @property
    def oldest_captured_at(self) -> datetime | None:
        with self._lock:
            return self._chunks[0].captured_at if self._chunks else None

    def __len__(self) -> int:
        with self._lock:
            return len(self._chunks)
