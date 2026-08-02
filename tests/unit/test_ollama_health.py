"""Ollama adapter boundary rules (ADR-0007, PRD AT-001)."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

import pytest

from jarvis.config.schema import NetworkMode
from jarvis.llm.ollama.health import OllamaHealthChecker, is_loopback_url


class _FakeResponse:
    def __init__(self, payload: dict[str, Any]) -> None:
        self._body = json.dumps(payload).encode("utf-8")

    def read(self, _limit: int | None = None) -> bytes:
        return self._body

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, *_exc: object) -> None:
        return None


@pytest.fixture
def fake_ollama(monkeypatch):
    """Replace urlopen so no test ever touches a real socket."""
    calls: list[str] = []

    def fake_urlopen(request, timeout=None):  # noqa: ARG001
        url = request.full_url
        calls.append(url)
        if url.endswith("/api/version"):
            return _FakeResponse({"version": "0.5.0"})
        if url.endswith("/api/tags"):
            return _FakeResponse({"models": [{"name": "qwen3:8b"}, {"name": "llava:7b"}]})
        raise urllib.error.URLError("unexpected path")

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    return calls


# -- loopback enforcement ---------------------------------------------------
@pytest.mark.parametrize(
    "url",
    ["http://127.0.0.1:11434", "http://localhost:11434", "http://[::1]:11434"],
)
def test_loopback_urls_are_recognised(url: str) -> None:
    assert is_loopback_url(url)


@pytest.mark.parametrize(
    "url",
    [
        "http://192.168.1.50:11434",
        "http://10.0.0.5:11434",
        "https://ollama.example.com",
        "http://8.8.8.8:11434",
    ],
)
def test_non_loopback_urls_are_rejected(url: str) -> None:
    assert not is_loopback_url(url)


def test_a_non_loopback_endpoint_is_refused_without_opening_a_socket(monkeypatch) -> None:
    """A remote 'local' endpoint would ship every prompt off the machine."""
    def explode(*_args, **_kwargs):
        raise AssertionError("no socket may be opened for a non-loopback endpoint")

    monkeypatch.setattr(urllib.request, "urlopen", explode)

    health = OllamaHealthChecker("http://192.168.1.50:11434").check()
    assert not health.reachable
    assert health.skipped_reason == "endpoint is not loopback"
    assert "non-loopback" in (health.error or "")


def test_loopback_can_be_disabled_explicitly(fake_ollama, monkeypatch) -> None:
    """Turning the check off is possible, but must be a deliberate configuration."""
    checker = OllamaHealthChecker("http://127.0.0.1:11434", require_loopback=False)
    assert checker.check().reachable


# -- offline mode (PRD AT-001) ---------------------------------------------
def test_offline_mode_opens_no_socket(monkeypatch) -> None:
    def explode(*_args, **_kwargs):
        raise AssertionError("offline mode must make no network request")

    monkeypatch.setattr(urllib.request, "urlopen", explode)

    health = OllamaHealthChecker(
        "http://127.0.0.1:11434", network_mode=NetworkMode.OFFLINE
    ).check()
    assert not health.reachable
    assert health.skipped_reason == "offline mode is enabled, so no request was made"
    assert health.skipped


# -- reachability -----------------------------------------------------------
def test_a_reachable_runtime_reports_version_and_models(fake_ollama) -> None:
    health = OllamaHealthChecker("http://127.0.0.1:11434").check()
    assert health.reachable
    assert health.version == "0.5.0"
    assert health.models == ("qwen3:8b", "llava:7b")
    assert "reachable" in health.describe()


def test_an_unreachable_runtime_is_reported_honestly(monkeypatch) -> None:
    def refuse(*_args, **_kwargs):
        raise urllib.error.URLError("connection refused")

    monkeypatch.setattr(urllib.request, "urlopen", refuse)

    health = OllamaHealthChecker("http://127.0.0.1:11434").check()
    assert not health.reachable
    assert "Is Ollama running?" in (health.error or "")
    assert "not reachable" in health.describe()


def test_a_timeout_is_reported_not_swallowed(monkeypatch) -> None:
    def stall(*_args, **_kwargs):
        raise TimeoutError()

    monkeypatch.setattr(urllib.request, "urlopen", stall)
    health = OllamaHealthChecker("http://127.0.0.1:11434", timeout_seconds=0.1).check()
    assert not health.reachable
    assert health.error


def test_malformed_json_does_not_crash_the_check(monkeypatch) -> None:
    class _Bad:
        def read(self, _limit=None):
            return b"not json"

        def __enter__(self):
            return self

        def __exit__(self, *_exc):
            return None

    monkeypatch.setattr(urllib.request, "urlopen", lambda *a, **k: _Bad())
    health = OllamaHealthChecker("http://127.0.0.1:11434").check()
    assert not health.reachable


def test_a_request_always_carries_a_timeout(monkeypatch) -> None:
    """PRD NFR-013: every external interaction has a timeout."""
    seen: dict[str, Any] = {}

    def capture(request, timeout=None):  # noqa: ARG001
        seen["timeout"] = timeout
        return _FakeResponse({"version": "0.5.0"})

    monkeypatch.setattr(urllib.request, "urlopen", capture)
    OllamaHealthChecker("http://127.0.0.1:11434", timeout_seconds=3.5).check()
    assert seen["timeout"] == 3.5
