"""Typed configuration schema (ADR-0006).

Every model is frozen and uses ``extra="forbid"``. A misspelt settings key is a
startup error naming the exact path, not a silently ignored value.
"""

from __future__ import annotations

from enum import Enum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

__all__ = [
    "AppConfig",
    "AudioConfig",
    "LlmConfig",
    "LoggingConfig",
    "ModelProfile",
    "ModelRuntimeConfig",
    "ModelsConfig",
    "NetworkConfig",
    "NetworkMode",
    "OllamaConfig",
    "PermissionsConfig",
    "PrivacyConfig",
    "RuntimeConfig",
    "StorageConfig",
    "TasksConfig",
    "TtsProfile",
    "UiConfig",
    "SUPPORTED_SCHEMA_VERSION",
]

SUPPORTED_SCHEMA_VERSION = 1

NonNegativeFloat = Annotated[float, Field(ge=0)]
PositiveInt = Annotated[int, Field(gt=0)]


class _Base(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class NetworkMode(str, Enum):
    """PRD section 7.4."""

    OFFLINE = "offline"
    LOCAL_ASSISTANT = "local_assistant"
    CONNECTED = "connected"


class RuntimeConfig(_Base):
    required_python: str
    single_instance: bool = True


class NetworkConfig(_Base):
    mode: NetworkMode = NetworkMode.LOCAL_ASSISTANT


class OllamaConfig(_Base):
    base_url: str
    request_timeout_seconds: Annotated[float, Field(gt=0, le=300)] = 10.0
    health_check_interval_seconds: Annotated[int, Field(ge=0)] = 300
    require_loopback: bool = True


class LlmConfig(_Base):
    ollama: OllamaConfig


class ModelProfile(_Base):
    provider: str
    name: str
    context_length: PositiveInt


class ModelsConfig(_Base):
    planner: ModelProfile
    vision: ModelProfile
    embeddings: ModelProfile


class ModelRuntimeConfig(_Base):
    idle_unload_seconds: Annotated[int, Field(ge=0)] = 180
    load_strategy: Literal["sequential", "parallel"] = "sequential"
    allow_parallel_heavy_models: bool = False

    @model_validator(mode="after")
    def _sequential_forbids_parallel(self) -> "ModelRuntimeConfig":
        # PRD FR-039: 12 GB VRAM cannot hold two heavy models with large contexts.
        if self.load_strategy == "sequential" and self.allow_parallel_heavy_models:
            raise ValueError(
                "model_runtime.allow_parallel_heavy_models cannot be true "
                "while load_strategy is 'sequential'"
            )
        return self


class WakeWordConfig(_Base):
    provider: str
    phrase: str
    push_to_talk_enabled: bool = True
    #: PRD FR-018 and ADR-0027 specify bare F9. It is configurable because a
    #: global hook swallows the key from every other application, and F9 is
    #: heavily used by IDEs, spreadsheets and games.
    push_to_talk_hotkey: str = "F9"
    #: ADR-0016: always-listening stays off until enrolment has been measured
    #: and passed. Push-to-talk is the fallback until then.
    always_listening: bool = False
    enrolled: bool = False


class SpeechToTextConfig(_Base):
    provider: str
    model: str
    device: Literal["cpu", "cuda"] = "cpu"
    compute_type: str = "int8"
    language: str = "en"
    vad_filter: bool = True
    retain_raw_audio: bool = False
    beam_size: PositiveInt = 1
    preload_on_startup: bool = True
    warmup_on_startup: bool = True
    idle_unload_seconds: Annotated[int, Field(ge=0)] = 0


class TtsProfile(_Base):
    provider: str
    spoken_language: str
    enabled: bool = False
    model_repository: str | None = None
    python_runtime: str | None = None
    execution_mode: Literal["in_process", "isolated_worker"] = "in_process"
    language_code: str | None = None
    voice: str | None = None
    device: Literal["cpu", "cuda"] | None = None
    speed: Annotated[float, Field(gt=0, le=4)] | None = None
    sample_rate_hz: PositiveInt | None = None
    fallback_only: bool = False
    status: Literal["stable", "experimental"] = "stable"


class TextToSpeechConfig(_Base):
    active_profile: str
    profiles: dict[str, TtsProfile]

    @model_validator(mode="after")
    def _active_profile_exists_and_is_enabled(self) -> "TextToSpeechConfig":
        profile = self.profiles.get(self.active_profile)
        if profile is None:
            raise ValueError(
                f"audio.text_to_speech.active_profile '{self.active_profile}' "
                f"is not one of {sorted(self.profiles)}"
            )
        # PRD FR-036: the configured voice must be a real, usable selection.
        if not profile.enabled:
            raise ValueError(
                f"audio.text_to_speech.active_profile '{self.active_profile}' is disabled"
            )
        if profile.fallback_only:
            raise ValueError(
                f"audio.text_to_speech.active_profile '{self.active_profile}' is "
                "marked fallback_only and cannot be the primary voice"
            )
        return self


class PronunciationConfig(_Base):
    provider: str
    architecture: str
    installation_scope: str
    status: str


class RecognitionLanguageConfig(_Base):
    mode: str
    preferred_languages: tuple[str, ...]


class ConversationLanguageConfig(_Base):
    understand: tuple[str, ...]


class SpokenOutputConfig(_Base):
    default_language: str


class LanguageConfig(_Base):
    recognition: RecognitionLanguageConfig
    conversation: ConversationLanguageConfig
    response_language: str
    spoken_output: SpokenOutputConfig


class AudioConfig(_Base):
    wake_word: WakeWordConfig
    speech_to_text: SpeechToTextConfig
    text_to_speech: TextToSpeechConfig
    pronunciation: PronunciationConfig
    language: LanguageConfig


class DefaultPermissionPolicy(_Base):
    low: Literal["ask", "deny", "allow"] = "ask"
    medium: Literal["ask", "deny"] = "ask"
    high: Literal["ask"] = "ask"  # PRD section 11.1: never anything else.


class PermissionsConfig(_Base):
    default_policy: DefaultPermissionPolicy = DefaultPermissionPolicy()
    session_grant_ttl_seconds: Annotated[int, Field(ge=0)] = 3600
    allow_always_for_low_risk: bool = True


class TasksConfig(_Base):
    max_concurrent: PositiveInt = 2
    default_max_retries: Annotated[int, Field(ge=0, le=50)] = 3
    lock_acquire_timeout_seconds: NonNegativeFloat = 0.0
    scheduler_poll_interval_seconds: Annotated[float, Field(gt=0, le=10)] = 0.1
    step_timeout_seconds: Annotated[float, Field(gt=0)] = 120.0


class LoggingConfig(_Base):
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    audit_to_sqlite: bool = True
    max_audit_value_chars: Annotated[int, Field(ge=16, le=8192)] = 512


class UiConfig(_Base):
    start_minimised_to_tray: bool = True
    show_unavailable_features: bool = True
    emergency_stop_hotkey: str = "Ctrl+Alt+Pause"
    #: PRD FR-002. Registered per-user, so it never needs elevation (ADR-0009).
    start_at_sign_in: bool = False
    #: An unanswered approval is denied after this long (ADR-0027). Bounded by
    #: PRD NFR-013: there is no "wait forever" option.
    approval_timeout_seconds: Annotated[float, Field(gt=0, le=900)] = 120.0


class StorageConfig(_Base):
    huggingface_home: str
    application_data: str
    workspace: str


class PrivacyConfig(_Base):
    raw_audio_retention: Literal["disabled", "diagnostic"] = "disabled"
    generated_voice_retention: Literal["temporary", "session", "retained"] = "temporary"
    screenshot_retention: Literal["none", "task_only", "diagnostic", "selected"] = "task_only"
    telemetry_enabled: bool = False

    @field_validator("telemetry_enabled")
    @classmethod
    def _telemetry_default_off(cls, value: bool) -> bool:
        # PRD section 18.5 requires opt-in; the schema simply permits it to be
        # turned on. This validator documents the intent and is a hook for the
        # consent record that Phase 6 will require.
        return value


class AppConfig(_Base):
    """The whole validated configuration tree."""

    schema_version: int
    runtime: RuntimeConfig
    network: NetworkConfig
    llm: LlmConfig
    models: ModelsConfig
    model_runtime: ModelRuntimeConfig
    audio: AudioConfig
    permissions: PermissionsConfig
    tasks: TasksConfig
    logging: LoggingConfig
    ui: UiConfig
    storage: StorageConfig
    privacy: PrivacyConfig

    @field_validator("schema_version")
    @classmethod
    def _supported_schema_version(cls, value: int) -> int:
        if value != SUPPORTED_SCHEMA_VERSION:
            raise ValueError(
                f"configuration schema_version {value} is not supported by this "
                f"build (expected {SUPPORTED_SCHEMA_VERSION})"
            )
        return value

    @property
    def offline(self) -> bool:
        return self.network.mode is NetworkMode.OFFLINE
