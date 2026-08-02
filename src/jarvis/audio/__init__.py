"""Voice input and output (L3, PRD sections 10.2 to 10.4).

Every provider in this package imports its heavy dependency lazily. The engine
must import and test with no audio stack installed at all — CI runs on Linux
with no microphone and no GPU — so nothing here may import sounddevice, torch,
faster-whisper, Kokoro or openWakeWord at module scope.

Ask :mod:`jarvis.audio.availability` what is usable before offering a feature.
"""

from jarvis.audio.availability import (
    ComponentStatus,
    VoiceStackStatus,
    describe_voice_stack,
    module_available,
)

__all__ = [
    "ComponentStatus",
    "VoiceStackStatus",
    "describe_voice_stack",
    "module_available",
]
