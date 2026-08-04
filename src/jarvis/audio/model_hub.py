"""Keep the speech model hubs off the network in offline mode (PRD AT-001).

The Ollama adapters were written so that offline mode opens no socket at all.
The speech stack quietly broke that rule from the other end: both Kokoro and
faster-whisper resolve their weights through ``huggingface_hub``, which contacts
the Hub when a model is loaded — visible in the logs as "You are sending
unauthenticated requests to the HF Hub".

That is a real request to a real remote host, made by a component the user
believes is local. AT-001 says offline mode makes none, so in offline mode the
hub libraries are told to use their local cache only. A model that has not been
downloaded yet then fails with a clear error instead of silently reaching out.

Environment variables are the only switch these libraries offer, and they are
read when the model loads, so this must be applied before the first load and
again whenever the mode changes.
"""

from __future__ import annotations

import logging
import os

from jarvis.config.schema import NetworkMode

__all__ = ["apply_network_policy", "hub_is_offline", "HUB_OFFLINE_VARIABLES"]

_LOG = logging.getLogger(__name__)

#: Every switch that stops a speech model hub reaching the network.
HUB_OFFLINE_VARIABLES = ("HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE", "HF_DATASETS_OFFLINE")


def apply_network_policy(config: object) -> bool:
    """Pin the hubs to their local cache when offline. Returns True if offline.

    Applied at construction and again on every network-mode change, because the
    libraries read these when a model is loaded, which may be much later.
    """
    network = getattr(config, "network", None)
    mode = getattr(network, "mode", None)
    offline = mode is NetworkMode.OFFLINE

    for name in HUB_OFFLINE_VARIABLES:
        if offline:
            os.environ[name] = "1"
        else:
            # Only clear what we set. A user who exported these deliberately
            # keeps them, because they asked for local-only loading.
            if os.environ.get(name) == "1" and _was_set_here(name):
                del os.environ[name]

    if offline:
        _mark_set_here()
        _LOG.info(
            "offline mode: speech model hubs are pinned to the local cache "
            "(%s)", ", ".join(HUB_OFFLINE_VARIABLES)
        )
    else:
        _clear_mark()
    return offline


def hub_is_offline() -> bool:
    return all(os.environ.get(name) == "1" for name in HUB_OFFLINE_VARIABLES)


#: Distinguishes "we set this" from "the user set this", so leaving offline mode
#: does not undo a deliberate local-only setup.
_MARKER = "JARVIS_SET_HUB_OFFLINE"


def _mark_set_here() -> None:
    os.environ[_MARKER] = "1"


def _clear_mark() -> None:
    os.environ.pop(_MARKER, None)


def _was_set_here(_name: str) -> bool:
    return os.environ.get(_MARKER) == "1"
