"""Layered configuration (ADR-0006)."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
import yaml

from jarvis.config.paths import DATA_DIR_ENV, VaultPaths, expand_path, find_defaults_config
from jarvis.config.schema import AppConfig, NetworkMode
from jarvis.config.store import ConfigError, ConfigStore, deep_merge


# -- paths ------------------------------------------------------------------
def test_vault_layout_is_created_under_one_root(tmp_path: Path) -> None:
    paths = VaultPaths.resolve(tmp_path / "vault").ensure()
    for directory in paths.all_directories():
        assert directory.is_dir()
        assert paths.root in directory.parents or directory == paths.root


def test_data_dir_env_relocates_the_whole_vault(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv(DATA_DIR_ENV, str(tmp_path / "elsewhere"))
    paths = VaultPaths.resolve()
    assert paths.root == (tmp_path / "elsewhere").resolve()
    assert paths.db_path.parent == paths.data_dir


def test_explicit_override_beats_the_environment(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv(DATA_DIR_ENV, str(tmp_path / "from-env"))
    paths = VaultPaths.resolve(tmp_path / "explicit")
    assert paths.root == (tmp_path / "explicit").resolve()


def test_windows_environment_variables_are_expanded(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("JARVIS_TEST_BASE", str(tmp_path))
    if os.name == "nt":
        assert expand_path("%JARVIS_TEST_BASE%\\sub") == (tmp_path / "sub").resolve()
    assert expand_path("$JARVIS_TEST_BASE/sub") == (tmp_path / "sub").resolve()


def test_defaults_file_is_locatable() -> None:
    assert find_defaults_config().is_file()


# -- merging ----------------------------------------------------------------
def test_deep_merge_merges_mappings_and_replaces_scalars() -> None:
    base = {"a": {"b": 1, "c": 2}, "list": [1, 2], "scalar": "x"}
    override = {"a": {"c": 99}, "list": [3], "scalar": "y"}
    merged = deep_merge(base, override)
    assert merged == {"a": {"b": 1, "c": 99}, "list": [3], "scalar": "y"}
    assert base["a"]["c"] == 2, "deep_merge must not mutate its input"


# -- validation -------------------------------------------------------------
def test_shipped_defaults_validate(config: AppConfig) -> None:
    assert config.schema_version == 1
    assert config.network.mode is NetworkMode.LOCAL_ASSISTANT
    assert config.models.planner.name


def test_unknown_setting_key_is_a_startup_error(vault, config_store) -> None:
    vault.user_config_path.write_text("nonsense_section:\n  x: 1\n", encoding="utf-8")
    with pytest.raises(ConfigError, match="nonsense_section"):
        config_store.load()


def test_misspelt_nested_key_names_the_exact_path(vault, config_store) -> None:
    vault.user_config_path.write_text("network:\n  moed: offline\n", encoding="utf-8")
    with pytest.raises(ConfigError) as excinfo:
        config_store.load()
    assert "network.moed" in str(excinfo.value)


def test_invalid_value_is_rejected(vault, config_store) -> None:
    vault.user_config_path.write_text("network:\n  mode: sideways\n", encoding="utf-8")
    with pytest.raises(ConfigError, match="network.mode"):
        config_store.load()


def test_unsupported_schema_version_is_rejected(vault, config_store) -> None:
    vault.user_config_path.write_text("schema_version: 99\n", encoding="utf-8")
    with pytest.raises(ConfigError, match="schema_version"):
        config_store.load()


def test_active_voice_profile_must_exist_and_be_usable(vault, config_store) -> None:
    vault.user_config_path.write_text(
        "audio:\n  text_to_speech:\n    active_profile: does_not_exist\n", encoding="utf-8"
    )
    with pytest.raises(ConfigError, match="active_profile"):
        config_store.load()


def test_a_fallback_only_voice_cannot_be_the_primary(vault, config_store) -> None:
    """PRD FR-036: the configured voice must be a real selection, not a fallback."""
    vault.user_config_path.write_text(
        "audio:\n  text_to_speech:\n    active_profile: windows_sapi\n", encoding="utf-8"
    )
    with pytest.raises(ConfigError, match="fallback_only"):
        config_store.load()


def test_sequential_loading_forbids_parallel_heavy_models(vault, config_store) -> None:
    """PRD FR-039: 12 GB VRAM cannot hold two heavy models at once."""
    vault.user_config_path.write_text(
        "model_runtime:\n  allow_parallel_heavy_models: true\n", encoding="utf-8"
    )
    with pytest.raises(ConfigError, match="allow_parallel_heavy_models"):
        config_store.load()


def test_high_risk_default_policy_cannot_be_relaxed(vault, config_store) -> None:
    """PRD 11.1: high risk is always 'ask'; the schema will not accept otherwise."""
    vault.user_config_path.write_text(
        "permissions:\n  default_policy:\n    high: allow\n", encoding="utf-8"
    )
    with pytest.raises(ConfigError, match="permissions.default_policy.high"):
        config_store.load()


# -- persistence ------------------------------------------------------------
def test_settings_persist_across_restarts(vault, config_store) -> None:
    """Phase 0 exit criterion: settings persist."""
    config_store.load()
    config_store.set("network.mode", "offline")

    reloaded = ConfigStore(vault, env={}).load()
    assert reloaded.network.mode is NetworkMode.OFFLINE


def test_only_the_difference_from_defaults_is_written(vault, config_store) -> None:
    config_store.load()
    config_store.set("ui.start_minimised_to_tray", False)

    written = yaml.safe_load(vault.user_config_path.read_text(encoding="utf-8"))
    assert written == {"ui": {"start_minimised_to_tray": False}}, (
        "user.yaml must record only overrides, so new shipped defaults still apply"
    )


def test_unset_returns_a_setting_to_its_default(vault, config_store) -> None:
    config_store.load()
    config_store.set("logging.level", "DEBUG")
    assert config_store.config.logging.level == "DEBUG"

    config_store.unset("logging.level")
    assert config_store.config.logging.level == "INFO"
    assert config_store.user_overrides() == {}, "empty containers should be pruned"


def test_an_invalid_setting_is_rejected_before_anything_is_written(vault, config_store) -> None:
    config_store.load()
    with pytest.raises(ConfigError):
        config_store.set("network.mode", "not-a-mode")
    assert not vault.user_config_path.exists(), (
        "an invalid setting must not leave a vault that fails to start"
    )


def test_saving_is_atomic_and_leaves_no_partial_file(vault, config_store) -> None:
    config_store.load()
    config_store.set("logging.level", "WARNING")
    assert vault.user_config_path.is_file()
    assert not list(vault.config_dir.glob("*.tmp"))


# -- environment overrides --------------------------------------------------
def test_environment_variables_override_files(vault) -> None:
    store = ConfigStore(vault, env={"JARVIS__NETWORK__MODE": "offline"})
    assert store.load().network.mode is NetworkMode.OFFLINE


def test_environment_values_are_parsed_as_yaml_scalars(vault) -> None:
    store = ConfigStore(vault, env={"JARVIS__UI__START_MINIMISED_TO_TRAY": "false"})
    assert store.load().ui.start_minimised_to_tray is False


def test_environment_override_is_not_persisted(vault) -> None:
    store = ConfigStore(vault, env={"JARVIS__LOGGING__LEVEL": "DEBUG"})
    store.load()
    store.set("ui.show_unavailable_features", False)
    written = yaml.safe_load(vault.user_config_path.read_text(encoding="utf-8"))
    assert "logging" not in written
