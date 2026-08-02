"""Layered configuration loading and override-only persistence (ADR-0006).

    defaults.yaml  ->  user.yaml (overrides only)  ->  JARVIS__* env  ->  AppConfig
"""

from __future__ import annotations

import copy
import os
from pathlib import Path
from typing import Any, Mapping

import yaml
from pydantic import ValidationError

from jarvis.config.paths import VaultPaths, find_defaults_config
from jarvis.config.schema import AppConfig

__all__ = ["ConfigError", "ConfigStore", "ENV_PREFIX", "deep_merge"]

#: ``JARVIS__NETWORK__MODE=offline`` overrides ``network.mode``.
ENV_PREFIX = "JARVIS__"
ENV_PATH_SEPARATOR = "__"


class ConfigError(Exception):
    """Configuration could not be loaded, validated or saved."""


def deep_merge(base: dict[str, Any], override: Mapping[str, Any]) -> dict[str, Any]:
    """Recursively merge ``override`` into a copy of ``base``.

    Mappings merge key-by-key; every other value (including lists) replaces
    wholesale, because a partially merged list is never what anyone means.
    """
    result = copy.deepcopy(base)
    for key, value in override.items():
        existing = result.get(key)
        if isinstance(existing, dict) and isinstance(value, Mapping):
            result[key] = deep_merge(existing, value)
        else:
            result[key] = copy.deepcopy(value)
    return result


def _parse_env_value(raw: str) -> Any:
    """Interpret an environment override as a YAML scalar (so ``false`` is bool)."""
    try:
        return yaml.safe_load(raw)
    except yaml.YAMLError:
        return raw


def _env_overrides(env: Mapping[str, str]) -> dict[str, Any]:
    overrides: dict[str, Any] = {}
    for key, raw in env.items():
        if not key.startswith(ENV_PREFIX):
            continue
        path = [part.lower() for part in key[len(ENV_PREFIX) :].split(ENV_PATH_SEPARATOR) if part]
        if not path:
            continue
        cursor = overrides
        for part in path[:-1]:
            nxt = cursor.get(part)
            if not isinstance(nxt, dict):
                nxt = {}
                cursor[part] = nxt
            cursor = nxt
        cursor[path[-1]] = _parse_env_value(raw)
    return overrides


def _read_yaml_mapping(path: Path) -> dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ConfigError(f"could not read configuration file {path}: {exc}") from exc
    try:
        loaded = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise ConfigError(f"{path} is not valid YAML: {exc}") from exc
    if loaded is None:
        return {}
    if not isinstance(loaded, dict):
        raise ConfigError(f"{path} must contain a YAML mapping at the top level")
    return loaded


def _atomic_write(path: Path, text: str) -> None:
    """Write via a temporary file in the same directory, then replace.

    A crash mid-save leaves either the old file or the new one, never a partial
    one.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def _set_by_path(target: dict[str, Any], dotted_key: str, value: Any) -> None:
    parts = [part for part in dotted_key.split(".") if part]
    if not parts:
        raise ConfigError("setting key must not be empty")
    cursor = target
    for part in parts[:-1]:
        nxt = cursor.get(part)
        if not isinstance(nxt, dict):
            nxt = {}
            cursor[part] = nxt
        cursor = nxt
    cursor[parts[-1]] = value


def _get_by_path(source: Mapping[str, Any], dotted_key: str) -> Any:
    cursor: Any = source
    for part in dotted_key.split("."):
        if not isinstance(cursor, Mapping) or part not in cursor:
            return None
        cursor = cursor[part]
    return cursor


def _delete_by_path(target: dict[str, Any], dotted_key: str) -> bool:
    parts = [part for part in dotted_key.split(".") if part]
    cursor: Any = target
    stack: list[tuple[dict[str, Any], str]] = []
    for part in parts[:-1]:
        if not isinstance(cursor, dict) or part not in cursor:
            return False
        stack.append((cursor, part))
        cursor = cursor[part]
    if not isinstance(cursor, dict) or parts[-1] not in cursor:
        return False
    del cursor[parts[-1]]
    # Prune containers that became empty so user.yaml stays a clean diff.
    for parent, key in reversed(stack):
        if isinstance(parent[key], dict) and not parent[key]:
            del parent[key]
    return True


class ConfigStore:
    """Loads, validates and persists configuration.

    Only the *difference from defaults* is written to ``user.yaml``, so shipping
    a new default changes untouched settings and never silently reverts a
    deliberate user choice.
    """

    def __init__(
        self,
        paths: VaultPaths,
        defaults_path: Path | None = None,
        env: Mapping[str, str] | None = None,
    ) -> None:
        self._paths = paths
        self._defaults_path = defaults_path or find_defaults_config()
        self._env = dict(os.environ if env is None else env)
        self._defaults: dict[str, Any] = _read_yaml_mapping(self._defaults_path)
        self._overrides: dict[str, Any] = {}
        self._config: AppConfig | None = None

    # -- loading -----------------------------------------------------------
    def load(self) -> AppConfig:
        self._overrides = (
            _read_yaml_mapping(self._paths.user_config_path)
            if self._paths.user_config_path.is_file()
            else {}
        )
        self._config = self._validate(self._merged())
        return self._config

    @property
    def config(self) -> AppConfig:
        if self._config is None:
            return self.load()
        return self._config

    @property
    def defaults_path(self) -> Path:
        return self._defaults_path

    @property
    def user_config_path(self) -> Path:
        return self._paths.user_config_path

    def user_overrides(self) -> dict[str, Any]:
        """The persisted overrides only, i.e. the diff from shipped defaults."""
        return copy.deepcopy(self._overrides)

    def _merged(self) -> dict[str, Any]:
        merged = deep_merge(self._defaults, self._overrides)
        return deep_merge(merged, _env_overrides(self._env))

    def _validate(self, raw: Mapping[str, Any]) -> AppConfig:
        try:
            return AppConfig.model_validate(raw)
        except ValidationError as exc:
            problems = "; ".join(
                f"{'.'.join(str(part) for part in error['loc'])}: {error['msg']}"
                for error in exc.errors()
            )
            raise ConfigError(f"invalid configuration: {problems}") from exc

    # -- mutation ----------------------------------------------------------
    def set(self, dotted_key: str, value: Any) -> AppConfig:
        """Validate then persist a single override. Returns the new config.

        The candidate is validated *before* anything is written, so an invalid
        setting cannot leave the vault in a state that fails to start.
        """
        candidate_overrides = copy.deepcopy(self._overrides)
        _set_by_path(candidate_overrides, dotted_key, value)
        candidate = deep_merge(self._defaults, candidate_overrides)
        candidate = deep_merge(candidate, _env_overrides(self._env))
        validated = self._validate(candidate)

        self._overrides = candidate_overrides
        self._persist()
        self._config = validated
        return validated

    def unset(self, dotted_key: str) -> AppConfig:
        """Remove an override, returning the setting to its shipped default."""
        candidate_overrides = copy.deepcopy(self._overrides)
        if not _delete_by_path(candidate_overrides, dotted_key):
            return self.config
        candidate = deep_merge(self._defaults, candidate_overrides)
        candidate = deep_merge(candidate, _env_overrides(self._env))
        validated = self._validate(candidate)

        self._overrides = candidate_overrides
        self._persist()
        self._config = validated
        return validated

    def effective_value(self, dotted_key: str) -> Any:
        return _get_by_path(self._merged(), dotted_key)

    def default_value(self, dotted_key: str) -> Any:
        return _get_by_path(self._defaults, dotted_key)

    def _persist(self) -> None:
        header = (
            "# Project Jarvis user configuration.\n"
            "# Overrides only: anything absent here follows config/defaults.yaml.\n"
            "# Written by the application; hand edits are validated at startup.\n"
        )
        body = yaml.safe_dump(self._overrides, sort_keys=True, allow_unicode=True, default_flow_style=False)
        _atomic_write(self._paths.user_config_path, header + body)
