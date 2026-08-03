"""Offline mode must silence the speech model hubs too (PRD AT-001).

The Ollama adapters refuse to open a socket in offline mode, and that was
tested. The speech stack broke the same rule from the other end: Kokoro and
faster-whisper both resolve weights through ``huggingface_hub``, which contacts
the Hub when a model loads. A real run printed "You are sending unauthenticated
requests to the HF Hub" — a remote request from a component the user believes is
entirely local.

Offline means offline for every component, not only the ones we wrote.
"""

from __future__ import annotations

import os

import pytest

from jarvis.audio.model_hub import (
    HUB_OFFLINE_VARIABLES,
    apply_network_policy,
    hub_is_offline,
)
from jarvis.config.schema import NetworkMode


class FakeConfig:
    def __init__(self, mode: NetworkMode) -> None:
        self.network = type("N", (), {"mode": mode})()


@pytest.fixture(autouse=True)
def clean_environment(monkeypatch):
    for name in (*HUB_OFFLINE_VARIABLES, "JARVIS_SET_HUB_OFFLINE"):
        monkeypatch.delenv(name, raising=False)
    yield


def test_offline_mode_pins_every_hub_to_the_local_cache() -> None:
    assert apply_network_policy(FakeConfig(NetworkMode.OFFLINE))
    for name in HUB_OFFLINE_VARIABLES:
        assert os.environ.get(name) == "1", f"{name} was not set"
    assert hub_is_offline()


def test_local_assistant_mode_does_not_pin_them() -> None:
    """Local assistant still permits fetching a model the user asked for."""
    assert not apply_network_policy(FakeConfig(NetworkMode.LOCAL_ASSISTANT))
    assert not hub_is_offline()


def test_leaving_offline_mode_releases_what_we_set() -> None:
    apply_network_policy(FakeConfig(NetworkMode.OFFLINE))
    apply_network_policy(FakeConfig(NetworkMode.LOCAL_ASSISTANT))
    for name in HUB_OFFLINE_VARIABLES:
        assert name not in os.environ


def test_a_deliberate_user_setting_survives_leaving_offline_mode(monkeypatch) -> None:
    """Someone who exported these wants local-only loading. Do not undo it."""
    for name in HUB_OFFLINE_VARIABLES:
        monkeypatch.setenv(name, "1")

    apply_network_policy(FakeConfig(NetworkMode.LOCAL_ASSISTANT))

    for name in HUB_OFFLINE_VARIABLES:
        assert os.environ.get(name) == "1", f"{name} was cleared behind the user's back"


def test_the_policy_is_applied_when_the_voice_service_is_built(vault, monkeypatch) -> None:
    from jarvis.audio.service import VoiceService
    from jarvis.config.store import ConfigStore

    store = ConfigStore(vault, env={})
    store.set("network.mode", NetworkMode.OFFLINE.value)
    service = VoiceService(store.load(), vault.root)
    try:
        assert hub_is_offline(), "building the voice service left the hubs online"
    finally:
        service.shutdown()


def test_switching_to_offline_at_runtime_pins_them(core) -> None:
    """The switch is read when a model loads, which is long after start-up."""
    assert not hub_is_offline()
    core.set_network_mode(NetworkMode.OFFLINE)
    assert hub_is_offline(), "switching to offline left the speech hubs online"
