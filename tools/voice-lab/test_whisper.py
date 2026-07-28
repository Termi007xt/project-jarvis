from __future__ import annotations

import os
from pathlib import Path

import sounddevice as sd
import soundfile as sf
from faster_whisper import WhisperModel


SAMPLE_RATE = 16_000
RECORD_SECONDS = 8

OUTPUT_DIR = Path(__file__).resolve().parent / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

RECORDING_PATH = OUTPUT_DIR / "whisper_microphone_test.wav"


def list_audio_devices() -> None:
    print("\nAvailable audio devices:\n")
    print(sd.query_devices())
    print()


def record_audio() -> None:
    print(
        f"Recording for {RECORD_SECONDS} seconds.\n"
        "Say: Hello Jarvis, open Downloads and find my latest resume PDF."
    )

    audio = sd.rec(
        int(RECORD_SECONDS * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="float32",
    )

    sd.wait()

    sf.write(
        RECORDING_PATH,
        audio,
        SAMPLE_RATE,
    )

    print(f"Recording saved to: {RECORDING_PATH}")


def transcribe_audio() -> None:
    print("\nLoading faster-whisper small model on CPU...")

    model = WhisperModel(
        "small",
        device="cpu",
        compute_type="int8",
    )

    segments, info = model.transcribe(
        str(RECORDING_PATH),
        language="en",
        beam_size=1,
        vad_filter=True,
        condition_on_previous_text=False,
    )

    completed_segments = list(segments)

    transcript = " ".join(
        segment.text.strip()
        for segment in completed_segments
        if segment.text.strip()
    )

    print(f"\nDetected language: {info.language}")
    print(f"Language probability: {info.language_probability:.3f}")
    print(f"Transcript: {transcript}")


def main() -> None:
    print(
        "HF_HOME:",
        os.environ.get("HF_HOME", "Not configured"),
    )

    list_audio_devices()
    record_audio()
    transcribe_audio()


if __name__ == "__main__":
    main()