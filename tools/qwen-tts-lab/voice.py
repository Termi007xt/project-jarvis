from typing import Any
import os
import torch
import soundfile as sf
import librosa
from qwen_tts import Qwen3TTSModel
from faster_whisper import WhisperModel

# 1. Setup paths
script_dir = os.path.dirname(os.path.abspath(__file__))
raw_ref_path = os.path.join(script_dir, "lucky.wav")
if not os.path.exists(raw_ref_path):
    raw_ref_path = os.path.join(script_dir, "jarvis.wav")

# 2. Pre-process Reference Audio using Librosa (Safe on Windows/Python 3.14)
print(f"Preprocessing reference audio ({os.path.basename(raw_ref_path)})...")
audio_data, sample_rate = librosa.load(raw_ref_path, sr=16000, mono=True)

# 3. Automatically Transcribe Reference Audio using faster-whisper
print("Transcribing reference audio using faster-whisper...")
device = "cuda" if torch.cuda.is_available() else "cpu"
compute_type = "float16" if device == "cuda" else "int8"
whisper_model: Any = WhisperModel("small", device=device, compute_type=compute_type)

segments, info = whisper_model.transcribe(
    raw_ref_path,
    language="en",
    beam_size=1,
    vad_filter=True,
    condition_on_previous_text=False,
)
reference_transcript = " ".join(segment.text.strip() for segment in segments if segment.text.strip())
print(f"\n[Transcribed Reference]: \"{reference_transcript}\"\n")

# 4. Get Target Text interactively at runtime
print("=" * 60)
user_input = input("Enter target text for voice cloning (Press Enter for default): ").strip()
target_text = user_input if user_input else "Good evening sir, ready to assist, all systems are operational."
print(f"[Target Text]: \"{target_text}\"")
print("=" * 60)

# 5. Load Qwen3-TTS Model on GPU
print("\nLoading Qwen3-TTS model onto GPU...")
model: Any = Qwen3TTSModel.from_pretrained(
    "Qwen/Qwen3-TTS-12Hz-1.7B-Base",
    device_map="cuda:0",
    dtype=torch.bfloat16,
)

# 6. Generate Voice Clone
print("Generating cloned audio...")
wavs, sr = model.generate_voice_clone(
    text=target_text,
    language="English",
    ref_audio=(audio_data, sample_rate),
    ref_text=reference_transcript, 
)

# 7. Save final output
output_file = os.path.join(script_dir, "cloned_output_fixed.wav")
sf.write(output_file, wavs[0], sr)
print(f"\nSuccess! Cloned audio saved to {output_file}")