"""Ollama health check (ADR-0007).

Two boundary rules are enforced here rather than by caller discipline, so they
hold no matter who calls:

* **Loopback only.** A configured base URL that does not resolve to a loopback
  address is refused. A remote "local" endpoint would silently ship every prompt
  off the machine.
* **Offline mode is honoured at the adapter.** In ``offline`` network mode no
  socket is opened at all, so PRD AT-001 is a property of this module.

Uses only the standard library. Adding an HTTP client for one GET would be a
dependency with no benefit.
"""

from __future__ import annotations

import ipaddress
import json
import socket
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime
from urllib.parse import urlparse

from jarvis.common import utc_now
from jarvis.config.schema import NetworkMode

__all__ = ["OllamaHealth", "OllamaHealthChecker", "is_loopback_url"]


def is_loopback_url(base_url: str) -> bool:
    """True when the URL's host is a loopback address or resolves only to one."""
    try:
        parsed = urlparse(base_url)
    except ValueError:
        return False
    host = parsed.hostname
    if not host:
        return False
    if host.lower() == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        pass
    # A hostname. Resolve it and require *every* address to be loopback, so a
    # name with one loopback and one public address cannot slip through.
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror:
        return False
    if not infos:
        return False
    for info in infos:
        address = info[4][0]
        try:
            if not ipaddress.ip_address(address).is_loopback:
                return False
        except ValueError:
            return False
    return True


@dataclass(frozen=True)
class OllamaHealth:
    """The result of one check. Never claims health it did not observe."""

    reachable: bool
    base_url: str
    checked_at: datetime = field(default_factory=utc_now)
    version: str | None = None
    models: tuple[str, ...] = ()
    error: str | None = None
    skipped_reason: str | None = None

    @property
    def skipped(self) -> bool:
        return self.skipped_reason is not None

    def describe(self) -> str:
        if self.skipped:
            return f"Not checked: {self.skipped_reason}."
        if self.reachable:
            model_count = len(self.models)
            version = f" version {self.version}" if self.version else ""
            return f"Ollama is reachable{version} with {model_count} model(s) installed."
        return f"Ollama is not reachable at {self.base_url}: {self.error}"


class OllamaHealthChecker:
    """Checks the local model runtime. Blocking; call it from a worker thread."""

    def __init__(
        self,
        base_url: str,
        *,
        timeout_seconds: float = 10.0,
        require_loopback: bool = True,
        network_mode: NetworkMode = NetworkMode.LOCAL_ASSISTANT,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout_seconds
        self._require_loopback = require_loopback
        self._network_mode = network_mode

    @property
    def base_url(self) -> str:
        return self._base_url

    def check(self) -> OllamaHealth:
        # Offline mode opens no socket. This is what makes AT-001 structural.
        if self._network_mode is NetworkMode.OFFLINE:
            return OllamaHealth(
                reachable=False,
                base_url=self._base_url,
                skipped_reason="offline mode is enabled, so no request was made",
            )

        if self._require_loopback and not is_loopback_url(self._base_url):
            return OllamaHealth(
                reachable=False,
                base_url=self._base_url,
                error=(
                    "refusing to contact a non-loopback model endpoint. Local "
                    "inference must stay on this computer; a remote endpoint would "
                    "send every prompt off the machine. Change llm.ollama.base_url "
                    "to a loopback address, or configure an external provider "
                    "explicitly."
                ),
                skipped_reason="endpoint is not loopback",
            )

        version = self._get_json("/api/version")
        if isinstance(version, Exception):
            return OllamaHealth(
                reachable=False,
                base_url=self._base_url,
                error=self._describe_error(version),
            )

        models: tuple[str, ...] = ()
        tags = self._get_json("/api/tags")
        if isinstance(tags, dict):
            entries = tags.get("models")
            if isinstance(entries, list):
                models = tuple(
                    str(entry.get("name"))
                    for entry in entries
                    if isinstance(entry, dict) and entry.get("name")
                )

        return OllamaHealth(
            reachable=True,
            base_url=self._base_url,
            version=str(version.get("version")) if isinstance(version, dict) else None,
            models=models,
        )

    def _get_json(self, path: str) -> object:
        url = f"{self._base_url}{path}"
        request = urllib.request.Request(url, method="GET", headers={"Accept": "application/json"})
        try:
            with urllib.request.urlopen(request, timeout=self._timeout) as response:  # noqa: S310
                # The URL was validated as loopback above; urlopen is bounded by
                # an explicit timeout (PRD NFR-013).
                payload = response.read(1_000_000)
            return json.loads(payload.decode("utf-8"))
        except (urllib.error.URLError, OSError, ValueError, json.JSONDecodeError) as exc:
            return exc

    @staticmethod
    def _describe_error(exc: Exception) -> str:
        if isinstance(exc, urllib.error.HTTPError):
            return f"HTTP {exc.code} from the endpoint"
        if isinstance(exc, urllib.error.URLError):
            return f"{exc.reason}. Is Ollama running?"
        if isinstance(exc, TimeoutError):
            return "the request timed out"
        return f"{type(exc).__name__}: {exc}"
