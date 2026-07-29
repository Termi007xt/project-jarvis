from typing import Any
import os
import torch
import soundfile as sf
import librosa
from qwen_tts import Qwen3TTSModel

# 1. Setup paths
script_dir = os.path.dirname(os.path.abspath(__file__))
raw_ref_path = os.path.join(script_dir, "lucky.wav")

# 2. Pre-process Reference Audio using Librosa (Safe on Windows/Python 3.14)
print("Preprocessing reference audio...")

# librosa automatically handles converting stereo to mono and resampling to 16kHz
# This is much safer and more robust than torchaudio on Windows.
audio_data, sample_rate = librosa.load(raw_ref_path, sr=16000, mono=True)

# 3. Load Qwen3-TTS Model on GPU
print("Loading Qwen3-TTS model onto GPU...")
model: Any = Qwen3TTSModel.from_pretrained(
    "Qwen/Qwen3-TTS-12Hz-1.7B-Base",
    device_map="cuda:0",
    dtype=torch.bfloat16,
)

# 4. Define text
# IMPORTANT: Update this string to match the exact dialogue in jarvis.wav
reference_transcript = "Good evening sir today is quick fox lazy jump valorant" 
target_text = "I am so bad at valorant, i am a sussy baka makima MOMMY lover, and i love peak yuri 3000!!! miyabi peak as hell too not gon lie "

# 5. Generate Voice Clone
print("Generating cloned audio...")
# Instead of passing a file path, we pass the tuple (audio_data, sample_rate) directly
wavs, sr = model.generate_voice_clone(
    text=target_text,
    language="English",
    ref_audio=(audio_data, sample_rate),
    ref_text=reference_transcript, 
)

# 6. Save final output
output_file = "cloned_output_fixed.wav"
sf.write(output_file, wavs[0], sr)
print(f"Success! Cloned audio saved to {output_file}")