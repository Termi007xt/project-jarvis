project_codename: Project Jarvis
public_product_name: undecided

primary_os: Windows 11 x64

hardware:
gpu: NVIDIA RTX 5070 12GB
cpu: AMD Ryzen 9 7900X
ram: 32GB
storage: 1TB SSD

models:
planner: qwen3.5:9b-q4_K_M
vision: qwen3-vl:8b-instruct-q4_K_M
embeddings: qwen3-embedding:0.6b

voice_stack:
default_provider:
provider: kokoro
python_runtime: "3.11"
model_repository: hexgrad/Kokoro-82M
language: British English
language_code: "b"
voice: bm_george
device: CPU
speed: 1.0
status: selected_and_verified

fallback_provider:
provider: Windows SAPI
enabled: true

expressive_provider: (for later phases, not now)
provider: qwen3_tts
model_repository: Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice
python_runtime: "3.12"
execution_mode: isolated_worker
device: CUDA
enabled_by_default: false
status: deferred_benchmark
intended_capabilities:

- expressive_speech
- emotion_instructions
- streaming_audio
- optional_voice_profiles
  activation_policy:
- never_switch_voice_silently
- user_selects_active_voice_profile
- benchmark_before_product_activation

pronunciation:
provider: espeak-ng
architecture: x64
installation_scope: Windows
status: installed_and_verified

speech_recognition:
  provider: faster-whisper
  python_runtime: "3.11"
  model: small
  device: CPU
  compute_type: int8
  language_mode: english
  preferred_languages:
    - English
  preload_on_startup: true
  keep_loaded: true
  retain_raw_audio: false
  status: installed_and_verified

language_policy:
  understand:
    - English
  spoken_output_language: English
  preserve_original_transcript: true

implementation_language:
version_1: Python
python_version: "3.11"
rust_status: deferred
rust_reconsideration_point: after_phase_3
rust_potential_scope:

- native_shell
- tray
- global_hotkeys
- updater
- secure_ipc

wake_word:
development_phrase: Hey Jarvis
desired_phrase: Jarvis
push_to_talk: enabled (preferred: always listening, activate when wake word identified)

storage:
application_data: "%LOCALAPPDATA%\\ProjectJarvis"
workspace: "%USERPROFILE%\\Documents\\Jarvis Workspace"
test_data: "%USERPROFILE%\\Documents\\Jarvis Test Data"

privacy:
default_network_mode: local_assistant
telemetry: disabled
raw_audio_retention: disabled
screenshot_retention: task_only
permanent_memory: approval_required

automation:
administrator_mode: disabled
dedicated_browser_profile: Jarvis
force_close_requires_confirmation: true
file_delete_requires_confirmation: true
emergency_stop_hotkey: Ctrl+Alt+Pause

python_runtime:
development_version: "3.11"
environment_policy: project_specific_virtual_environment
architecture: x64
