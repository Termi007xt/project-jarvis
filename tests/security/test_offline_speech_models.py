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
    hub_library_is_offline,
)
from jarvis.config.schema import NetworkMode


class FakeConfig:
    def __init__(
        self,
        mode: NetworkMode,
        *,
        local_only: bool = True,
        huggingface_home: str = "",
    ) -> None:
        self.network = type("N", (), {"mode": mode})()
        self.storage = type(
            "S",
            (),
            {
                "speech_models_local_only": local_only,
                "huggingface_home": huggingface_home,
            },
        )()


@pytest.fixture(autouse=True)
def clean_environment(monkeypatch):
    for name in (*HUB_OFFLINE_VARIABLES, "HF_HOME", "JARVIS_SET_HUB_OFFLINE"):
        monkeypatch.delenv(name, raising=False)
    for name in (*HUB_OFFLINE_VARIABLES, "HF_HOME"):
        monkeypatch.delenv(f"JARVIS_SET_HUB_OFFLINE__{name}", raising=False)
    yield


def test_offline_mode_pins_every_hub_to_the_local_cache() -> None:
    assert apply_network_policy(FakeConfig(NetworkMode.OFFLINE))
    for name in HUB_OFFLINE_VARIABLES:
        assert os.environ.get(name) == "1", f"{name} was not set"
    assert hub_is_offline()


# =========================================================================
# Local-only is the default, in every mode
# =========================================================================
def test_weights_are_resolved_from_disk_even_when_not_in_offline_mode() -> None:
    """Reported by the owner on 2026-08-06, from the log of an ordinary reply.

    Kokoro resolves its voice tensors at *synthesis* time, so a cached, local,
    already-downloaded voice still produced a request to huggingface.co every
    time Jarvis spoke — asking whether the copy on disk was current. Nothing
    confidential leaves, but it is a remote request from a component the user
    believes is local, and it puts the network on the path of every reply.

    Offline mode was not the right switch for it: the owner is not offline, they
    want the models local. So the network is for fetching a model that is
    missing, and never for confirming one that is already here.
    """
    assert apply_network_policy(FakeConfig(NetworkMode.LOCAL_ASSISTANT))
    assert hub_is_offline()


def test_the_pin_can_be_turned_off_to_download_a_new_model() -> None:
    """Local-only has to be releasable, or a missing voice is unfixable."""
    assert not apply_network_policy(
        FakeConfig(NetworkMode.LOCAL_ASSISTANT, local_only=False)
    )
    assert not hub_is_offline()


def test_offline_mode_still_wins_over_a_released_pin() -> None:
    """Turning local-only off is permission to download, not to go online."""
    assert apply_network_policy(FakeConfig(NetworkMode.OFFLINE, local_only=False))
    assert hub_is_offline()


# =========================================================================
# Where the weights are kept
# =========================================================================
def test_the_configured_model_directory_is_actually_applied(tmp_path) -> None:
    """It was configuration in name only.

    `storage.huggingface_home` has named a directory inside the Jarvis data
    folder since Phase 1, and nothing ever read it, so the libraries used their
    own default under the user's profile. On this machine it happened to be
    right because the owner had exported HF_HOME by hand — which is not the
    configuration working, it is someone knowing to work around it.
    """
    store = tmp_path / "models"
    apply_network_policy(
        FakeConfig(NetworkMode.LOCAL_ASSISTANT, huggingface_home=str(store))
    )

    assert os.environ.get("HF_HOME") == str(store)


def test_an_hf_home_the_user_exported_is_left_alone(monkeypatch, tmp_path) -> None:
    """Several gigabytes of downloads are not moved behind someone's back."""
    theirs = tmp_path / "their-own-cache"
    monkeypatch.setenv("HF_HOME", str(theirs))

    apply_network_policy(
        FakeConfig(NetworkMode.LOCAL_ASSISTANT, huggingface_home=str(tmp_path / "ours"))
    )

    assert os.environ.get("HF_HOME") == str(theirs)


def test_leaving_offline_mode_releases_only_what_we_set() -> None:
    """Coming back online is not on its own permission to fetch weights.

    It used to be: leaving offline mode unpinned the hubs. Local-only is now the
    default in every mode, so releasing takes turning that off as well — which
    is the point. Coming online is about Ollama and the browser; whether Jarvis
    downloads a speech model is a separate question with a separate answer.
    """
    apply_network_policy(FakeConfig(NetworkMode.OFFLINE))
    apply_network_policy(FakeConfig(NetworkMode.LOCAL_ASSISTANT))
    assert hub_is_offline(), "local-only was released by a change of network mode"

    apply_network_policy(FakeConfig(NetworkMode.LOCAL_ASSISTANT, local_only=False))
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
    core.set_network_mode(NetworkMode.OFFLINE)
    assert hub_is_offline(), "switching to offline left the speech hubs online"


def test_the_library_itself_is_told_not_only_the_environment() -> None:
    """The assertion the old test was missing, and the reason it was missing it.

    This test used to say the switch "is read when a model loads, which is long
    after start-up", and checked only that the environment variable was set —
    which it always was. Measured against huggingface_hub 1.26 on 2026-08-06:
    the value is captured into `constants.HF_HUB_OFFLINE` at **import**, so
    setting the variable after anything has imported the library changes nothing
    it will ever read. An environment variable nobody reads is not a control.
    """
    pytest.importorskip("huggingface_hub")
    import huggingface_hub.constants as constants

    constants.HF_HUB_OFFLINE = False  # as if a model had loaded first
    apply_network_policy(FakeConfig(NetworkMode.LOCAL_ASSISTANT))

    assert hub_library_is_offline() is True, (
        "the environment says local-only and huggingface_hub does not; it read "
        "the variable at import and will not read it again"
    )
