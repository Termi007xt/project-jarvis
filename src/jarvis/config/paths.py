"""Data-vault path resolution.

This is the *only* module permitted to expand Windows environment variables or
decide where user data lives (ARCHITECTURE.md section 6.1). Everything else asks
:class:`VaultPaths`.

Resolution order for the vault root:

1. an explicit override passed to :meth:`VaultPaths.resolve`
2. the ``JARVIS_DATA_DIR`` environment variable (tests and relocation)
3. ``%LOCALAPPDATA%\\ProjectJarvis`` on Windows (PRD section 14.2)
4. ``~/.local/share/ProjectJarvis`` on other platforms, for development only
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from jarvis import VAULT_DIR_NAME

__all__ = [
    "DATA_DIR_ENV",
    "DEFAULTS_CONFIG_ENV",
    "VaultPaths",
    "expand_path",
    "find_defaults_config",
]

DATA_DIR_ENV = "JARVIS_DATA_DIR"
DEFAULTS_CONFIG_ENV = "JARVIS_DEFAULTS_CONFIG"


def expand_path(value: str | os.PathLike[str]) -> Path:
    """Expand ``%VARS%``, ``$VARS`` and ``~`` then normalise to an absolute path."""
    text = os.fspath(value)
    expanded = os.path.expanduser(os.path.expandvars(text))
    return Path(expanded).resolve()


def _platform_default_root() -> Path:
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        return Path(local_app_data) / VAULT_DIR_NAME
    if os.name == "nt":  # pragma: no cover - LOCALAPPDATA is always set on Windows
        return Path.home() / "AppData" / "Local" / VAULT_DIR_NAME
    return Path.home() / ".local" / "share" / VAULT_DIR_NAME


@dataclass(frozen=True)
class VaultPaths:
    """Every path the application is allowed to write to, derived from one root."""

    root: Path

    @classmethod
    def resolve(
        cls,
        override: str | os.PathLike[str] | None = None,
        env: dict[str, str] | None = None,
    ) -> "VaultPaths":
        environ = os.environ if env is None else env
        if override is not None:
            return cls(root=expand_path(override))
        from_env = environ.get(DATA_DIR_ENV)
        if from_env:
            return cls(root=expand_path(from_env))
        return cls(root=expand_path(_platform_default_root()))

    # -- configuration -----------------------------------------------------
    @property
    def config_dir(self) -> Path:
        return self.root / "config"

    @property
    def user_config_path(self) -> Path:
        return self.config_dir / "user.yaml"

    # -- canonical data ----------------------------------------------------
    @property
    def data_dir(self) -> Path:
        return self.root / "data"

    @property
    def db_path(self) -> Path:
        return self.data_dir / "jarvis.db"

    # -- logs --------------------------------------------------------------
    @property
    def logs_dir(self) -> Path:
        return self.root / "logs"

    @property
    def app_log_path(self) -> Path:
        return self.logs_dir / "app.log"

    @property
    def audit_log_path(self) -> Path:
        return self.logs_dir / "audit.jsonl"

    @property
    def crash_dir(self) -> Path:
        return self.logs_dir / "crashes"

    # -- attachments -------------------------------------------------------
    @property
    def attachments_dir(self) -> Path:
        return self.root / "attachments"

    @property
    def screenshots_dir(self) -> Path:
        return self.attachments_dir / "screenshots"

    @property
    def audio_diagnostics_dir(self) -> Path:
        return self.attachments_dir / "audio_diagnostics"

    @property
    def task_evidence_dir(self) -> Path:
        return self.attachments_dir / "task_evidence"

    # -- other vault areas -------------------------------------------------
    @property
    def browser_dir(self) -> Path:
        return self.root / "browser"

    @property
    def models_dir(self) -> Path:
        return self.root / "models"

    @property
    def exports_dir(self) -> Path:
        return self.root / "exports"

    @property
    def backups_dir(self) -> Path:
        return self.root / "backups"

    @property
    def temp_dir(self) -> Path:
        return self.root / "temp"

    @property
    def runtime_dir(self) -> Path:
        """Instance-scoped files such as the single-instance lock."""
        return self.root / "runtime"

    def all_directories(self) -> tuple[Path, ...]:
        return (
            self.root,
            self.config_dir,
            self.data_dir,
            self.logs_dir,
            self.crash_dir,
            self.attachments_dir,
            self.screenshots_dir,
            self.audio_diagnostics_dir,
            self.task_evidence_dir,
            self.browser_dir,
            self.models_dir,
            self.exports_dir,
            self.backups_dir,
            self.temp_dir,
            self.runtime_dir,
        )

    def ensure(self) -> "VaultPaths":
        """Create the vault layout. Idempotent."""
        for directory in self.all_directories():
            directory.mkdir(parents=True, exist_ok=True)
        return self


def find_defaults_config() -> Path:
    """Locate the shipped ``defaults.yaml``.

    Order: ``JARVIS_DEFAULTS_CONFIG`` env override, a copy bundled next to the
    package (populated at packaging time), then the repository ``config/``
    directory found by walking upwards from this file.
    """
    override = os.environ.get(DEFAULTS_CONFIG_ENV)
    if override:
        candidate = expand_path(override)
        if candidate.is_file():
            return candidate
        raise FileNotFoundError(f"{DEFAULTS_CONFIG_ENV} points at a missing file: {candidate}")

    bundled = Path(__file__).resolve().parent.parent / "_bundled" / "defaults.yaml"
    if bundled.is_file():
        return bundled

    for parent in Path(__file__).resolve().parents:
        candidate = parent / "config" / "defaults.yaml"
        if candidate.is_file():
            return candidate

    raise FileNotFoundError(
        "Could not locate config/defaults.yaml. Set JARVIS_DEFAULTS_CONFIG to its path."
    )
