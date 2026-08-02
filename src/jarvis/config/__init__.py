"""Configuration layer (L1). Must not import anything above L1."""

from __future__ import annotations

from jarvis.config.paths import DATA_DIR_ENV, VaultPaths, expand_path, find_defaults_config
from jarvis.config.schema import AppConfig, NetworkMode, SUPPORTED_SCHEMA_VERSION
from jarvis.config.store import ConfigError, ConfigStore, deep_merge

__all__ = [
    "AppConfig",
    "ConfigError",
    "ConfigStore",
    "DATA_DIR_ENV",
    "NetworkMode",
    "SUPPORTED_SCHEMA_VERSION",
    "VaultPaths",
    "deep_merge",
    "expand_path",
    "find_defaults_config",
]
