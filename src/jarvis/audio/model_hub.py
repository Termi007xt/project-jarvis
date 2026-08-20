"""Keep the speech model hubs local: local cache, local storage (PRD AT-001).

The Ollama adapters were written so that offline mode opens no socket at all.
The speech stack quietly broke that rule from the other end: both Kokoro and
faster-whisper resolve their weights through ``huggingface_hub``, which contacts
the Hub when a model is loaded — visible in the logs as "You are sending
unauthenticated requests to the HF Hub".

Two separate things are wrong with that, and they need separate answers.

**Where the weights live.** ``storage.huggingface_home`` names a directory
inside the Jarvis data folder, and nothing ever applied it, so the libraries
used their own default under the user's profile. On this machine it happened to
be right because the owner had exported ``HF_HOME`` by hand — a configuration
value that only works if you already knew to set it is not configuration. It is
applied here now, and a deliberate environment setting still wins.

**When the network is touched.** Even a fully cached model is revalidated: the
Hub is asked whether the copy on disk is current, on every resolve. Kokoro loads
its voice tensors per voice at synthesis time, so that lands on the *reply
path* — a remote request every time Jarvis speaks. faster-whisper does the same
once, when the model loads. Nothing confidential goes out, but it is a request
to a remote host from a component the user believes is local, it makes speech
depend on a network round trip, and the owner asked for local-only on
2026-08-06.

So the default is now local-only in **every** network mode, not just offline:
the network is for *fetching a model that is missing*, which is a deliberate
act, and never for confirming one that is already here.

**These switches are read at import, not at load.** The previous version of this
module said otherwise and a test asserted only that the environment variable was
set, which it always was. Measured against ``huggingface_hub`` 1.26: the value
is captured into ``constants.HF_HUB_OFFLINE`` when the package is imported, so
setting the variable afterwards changes nothing the library will ever read. The
library is therefore updated in place as well, which works because every call
site reads it as ``constants.HF_HUB_OFFLINE`` rather than binding it at import.
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

from jarvis.config.schema import NetworkMode

__all__ = [
    "apply_network_policy",
    "hub_is_offline",
    "hub_library_is_offline",
    "model_store_directory",
    "HUB_OFFLINE_VARIABLES",
]

_LOG = logging.getLogger(__name__)

#: Every switch that stops a speech model hub reaching the network.
HUB_OFFLINE_VARIABLES = ("HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE", "HF_DATASETS_OFFLINE")

#: Where the hub libraries keep their cache. Set from ``storage.huggingface_home``.
_HOME_VARIABLE = "HF_HOME"


def model_store_directory(config: object) -> Path | None:
    """The configured model store, with ``%VARIABLES%`` expanded."""
    storage = getattr(config, "storage", None)
    configured = getattr(storage, "huggingface_home", None)
    if not configured:
        return None
    return Path(os.path.expandvars(str(configured))).expanduser()


def _apply_model_store(config: object) -> None:
    """Point the hub libraries at the Jarvis model directory.

    An ``HF_HOME`` the user exported themselves is left alone. Someone who set
    it meant it, and silently redirecting their model cache would move several
    gigabytes of downloads somewhere they did not choose.
    """
    directory = model_store_directory(config)
    if directory is None:
        return

    existing = os.environ.get(_HOME_VARIABLE)
    if existing and Path(existing) != directory and not _was_set_here(_HOME_VARIABLE):
        _LOG.info(
            "HF_HOME is already set to %s, so speech models stay there rather "
            "than in the configured store %s", existing, directory
        )
        return

    os.environ[_HOME_VARIABLE] = str(directory)
    _mark_set_here(_HOME_VARIABLE)


def _local_only(config: object) -> bool:
    """Whether weights must be resolved from disk alone. Default: yes."""
    storage = getattr(config, "storage", None)
    return bool(getattr(storage, "speech_models_local_only", True))


def apply_network_policy(config: object) -> bool:
    """Pin the hubs to local storage and the local cache. True if pinned.

    Applied at construction and again on every network-mode change. It must run
    before anything imports ``huggingface_hub``; when that has already happened
    the library is updated in place too, because the environment variable alone
    would be read too late to matter.
    """
    _apply_model_store(config)

    network = getattr(config, "network", None)
    mode = getattr(network, "mode", None)
    offline_mode = mode is NetworkMode.OFFLINE
    pinned = offline_mode or _local_only(config)

    for name in HUB_OFFLINE_VARIABLES:
        if pinned:
            os.environ[name] = "1"
        else:
            # Only clear what we set. A user who exported these deliberately
            # keeps them, because they asked for local-only loading.
            if os.environ.get(name) == "1" and _was_set_here(name):
                del os.environ[name]

    if pinned:
        for name in HUB_OFFLINE_VARIABLES:
            _mark_set_here(name)
        _LOG.info(
            "speech model hubs are pinned to local storage (%s)",
            "offline mode" if offline_mode else "storage.speech_models_local_only",
        )
    else:
        for name in HUB_OFFLINE_VARIABLES:
            _clear_mark(name)

    _sync_live_library(pinned)
    return pinned


def _sync_live_library(pinned: bool) -> None:
    """Tell an already-imported ``huggingface_hub`` about the change.

    Its constants are captured at import, so a run that loaded a model before
    the policy was applied would otherwise keep the value it started with. Not
    imported here — only updated if it is already loaded, so this never pulls a
    heavy optional dependency into a headless run.
    """
    module = sys.modules.get("huggingface_hub.constants")
    if module is None:
        return
    try:
        module.HF_HUB_OFFLINE = pinned  # type: ignore[attr-defined]
    except Exception:  # noqa: BLE001 - a library that will not be told is not fatal
        _LOG.debug("could not update huggingface_hub in place", exc_info=True)


def hub_is_offline() -> bool:
    """What the environment says. See `hub_library_is_offline` for the truth."""
    return all(os.environ.get(name) == "1" for name in HUB_OFFLINE_VARIABLES)


def hub_library_is_offline() -> bool | None:
    """What ``huggingface_hub`` itself believes, or None if it is not loaded.

    The environment variable is the switch; this is whether the library ever
    read it. They come apart whenever the policy is applied after an import,
    which is exactly the case a test asserting only the variable cannot see.
    """
    module = sys.modules.get("huggingface_hub.constants")
    if module is None:
        return None
    return bool(getattr(module, "HF_HUB_OFFLINE", False))


#: Distinguishes "we set this" from "the user set this", so leaving local-only
#: never undoes a deliberate setup, and never claims someone else's HF_HOME.
_MARKER = "JARVIS_SET_HUB_OFFLINE"


def _marked(name: str) -> str:
    return f"{_MARKER}__{name}"


def _mark_set_here(name: str) -> None:
    os.environ[_marked(name)] = "1"
    # The un-suffixed marker is what the first version of this module wrote and
    # what `hub_is_offline`-era tests look for; kept so a config written by an
    # older build is still recognised as ours rather than as the user's.
    os.environ[_MARKER] = "1"


def _clear_mark(name: str) -> None:
    os.environ.pop(_marked(name), None)
    if not any(
        os.environ.get(_marked(other)) == "1"
        for other in (*HUB_OFFLINE_VARIABLES, _HOME_VARIABLE)
    ):
        os.environ.pop(_MARKER, None)


def _was_set_here(name: str) -> bool:
    return os.environ.get(_marked(name)) == "1" or os.environ.get(_MARKER) == "1"
