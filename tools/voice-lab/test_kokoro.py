from __future__ import annotations

from pathlib import Path

import numpy as np
import soundfile as sf
from kokoro import KPipeline


OUTPUT_DIR = Path(__file__).resolve().parent / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SAMPLE_RATE = 24_000

TEST_TEXT = (
    "Good evening, Maulik. Jarvis is online. "
    "All local systems are operational. "
    "I am ready to help you organise your work, Sir, "
    "search for information, and operate approved applications."
)

VOICE_TESTS = {
    "am_fenrir": "a",
    "am_michael": "a",
    "bm_fable": "b",
    "bm_george": "b",
}


def normalise_audio(audio: object) -> np.ndarray:
    """Convert Kokoro output into a one-dimensional NumPy array."""
    if hasattr(audio, "detach"):
        audio = audio.detach()

    if hasattr(audio, "cpu"):
        audio = audio.cpu()

    if hasattr(audio, "numpy"):
        audio = audio.numpy()

    result = np.asarray(audio, dtype=np.float32)
    return result.reshape(-1)


def generate_voice_sample(voice: str, language_code: str) -> Path:
    print(f"Loading pipeline for {voice}...")

    pipeline = KPipeline(lang_code=language_code)

    generator = pipeline(
        TEST_TEXT,
        voice=voice,
        speed=1.0,
    )

    chunks: list[np.ndarray] = []

    for _, _, audio in generator:
        chunks.append(normalise_audio(audio))

    if not chunks:
        raise RuntimeError(f"Kokoro produced no audio for {voice}")

    combined_audio = np.concatenate(chunks)

    output_path = OUTPUT_DIR / f"{voice}.wav"

    sf.write(
        output_path,
        combined_audio,
        SAMPLE_RATE,
    )

    return output_path


def main() -> None:
    generated_files: list[Path] = []

    for voice, language_code in VOICE_TESTS.items():
        try:
            output_path = generate_voice_sample(
                voice=voice,
                language_code=language_code,
            )
            generated_files.append(output_path)
            print(f"Created: {output_path}")

        except Exception as exc:
            print(f"FAILED {voice}: {exc}")

    print("\nGenerated voice samples:")

    for generated_file in generated_files:
        print(generated_file)


if __name__ == "__main__":
    main()