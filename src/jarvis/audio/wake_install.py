"""One-time wake-word model installation (ADR-0016, PRD section 17.2).

**No wake-word model ships with Project Jarvis.** ADR-0016 chose per-user
enrolment partly to avoid redistributing a trained artefact, and the pretrained
openWakeWord models carry a **non-commercial** licence besides (see
:data:`LICENCE`). So the model is *fetched*, once, by explicit user action,
through openWakeWord's own official API — never bundled, never committed, never
pulled from an unofficial mirror.

What gets installed, all into the configured Jarvis application-data directory:

* ``hey_jarvis_v0.1.onnx`` — the wake model. ONNX on Windows, per the project
  owner's direction; the library defaults to tflite, so the framework is passed
  explicitly everywhere.
* ``melspectrogram.onnx`` and ``embedding_model.onnx`` — the shared feature
  models every openWakeWord model needs.
* ``silero_vad.onnx`` — the VAD model.

openWakeWord resolves its feature and VAD models from paths baked into the
installed package, so simply downloading them elsewhere would leave the library
looking in the wrong place. :func:`use_local_models` repoints them at the Jarvis
copies, which is what keeps the vault the single location and makes
uninstalling a matter of deleting one directory.

Installation is idempotent: a file that is already present and loadable is left
alone, and running the action again reports "already installed" rather than
re-downloading.
"""

from __future__ import annotations

import logging
import shutil
from dataclasses import dataclass, field
from pathlib import Path

from jarvis.audio.availability import VOICE_EXTRA_HINT, module_available

__all__ = [
    "WAKE_MODEL_FILENAME",
    "REQUIRED_FILES",
    "LICENCE",
    "LICENCE_URL",
    "PROVIDER",
    "InstallReport",
    "model_directory",
    "installed_files",
    "is_installed",
    "install_wake_model",
    "uninstall_wake_model",
    "use_local_models",
    "verify_detector_loads",
]

_LOG = logging.getLogger(__name__)

#: ONNX on Windows. openWakeWord defaults to tflite, so every load site passes
#: ``inference_framework="onnx"`` explicitly rather than relying on the default.
WAKE_MODEL_FILENAME = "hey_jarvis_v0.1.onnx"

#: Everything the detector needs before it can initialise. Checked by name so
#: a partial download is detected as "not installed" rather than failing later.
REQUIRED_FILES: tuple[str, ...] = (
    WAKE_MODEL_FILENAME,
    "melspectrogram.onnx",
    "embedding_model.onnx",
    "silero_vad.onnx",
)

PROVIDER = "openWakeWord (dscripka), pretrained model release v0.5.1"
LICENCE = "Creative Commons Attribution-NonCommercial-ShareAlike 4.0 (CC BY-NC-SA 4.0)"
LICENCE_URL = "https://github.com/dscripka/openWakeWord#licence"

#: Stated wherever the model is offered, because it constrains what this
#: project may later become (PRD §17.2, §17.3, ADR-0014's parallel problem).
LICENCE_WARNING = (
    "The pretrained openWakeWord models are licensed for NON-COMMERCIAL use "
    "(CC BY-NC-SA 4.0). They are downloaded to your own machine for your own "
    "use and are never bundled with Project Jarvis. They must NOT be included "
    "in any commercial or public distribution unless the licensing is resolved "
    "first — either by obtaining different terms, or by training a replacement."
)


def model_directory(vault_root: Path) -> Path:
    """Where the runtime models live. Application data, never the repository."""
    return Path(vault_root) / "models" / "wake"


@dataclass(frozen=True)
class InstallReport:
    """What happened, in enough detail to show the user the exact path."""

    installed: bool
    already_present: bool
    directory: Path
    files: tuple[str, ...] = ()
    missing: tuple[str, ...] = ()
    detector_loads: bool = False
    error: str | None = None
    notes: list[str] = field(default_factory=list)

    def describe(self) -> str:
        if self.error:
            return f"Wake-word model not installed: {self.error}"
        if self.already_present and not self.installed:
            return f"Already installed in {self.directory}."
        if self.installed:
            state = "and the detector initialises" if self.detector_loads else (
                "but the detector did NOT initialise, so it is not usable"
            )
            return f"Installed {len(self.files)} file(s) into {self.directory} {state}."
        return f"Not installed. Expected in {self.directory}."


def installed_files(vault_root: Path) -> tuple[str, ...]:
    directory = model_directory(vault_root)
    if not directory.is_dir():
        return ()
    return tuple(name for name in REQUIRED_FILES if (directory / name).is_file())


def missing_files(vault_root: Path) -> tuple[str, ...]:
    present = set(installed_files(vault_root))
    return tuple(name for name in REQUIRED_FILES if name not in present)


def is_installed(vault_root: Path) -> bool:
    """All required files present. Says nothing about whether they *work*."""
    return not missing_files(vault_root)


def use_local_models(vault_root: Path) -> dict[str, str]:
    """The keyword arguments that point openWakeWord at the vault's copies.

    ``AudioFeatures`` takes the feature-model paths as constructor arguments,
    and ``Model`` forwards ``**kwargs`` to it. Passing them is the supported
    route; the ``FEATURE_MODELS`` table is only a default and is resolved from
    the installed package, so relying on it would send the library looking
    inside ``site-packages`` for models that were downloaded to the vault.
    """
    directory = model_directory(vault_root)
    kwargs: dict[str, str] = {"inference_framework": "onnx"}
    melspec = directory / "melspectrogram.onnx"
    embedding = directory / "embedding_model.onnx"
    if melspec.is_file():
        kwargs["melspec_model_path"] = str(melspec)
    if embedding.is_file():
        kwargs["embedding_model_path"] = str(embedding)
    return kwargs


def verify_detector_loads(vault_root: Path) -> tuple[bool, str | None]:
    """Actually initialise the detector (ADR-0010).

    "The files are on disk" is not the same as "wake detection works". This is
    what ``--check`` reports against, so a partial or corrupt download is
    reported as not installed rather than as ready.
    """
    if not module_available("openwakeword"):
        return False, f"openwakeword is not installed; {VOICE_EXTRA_HINT}"
    missing = missing_files(vault_root)
    if missing:
        return False, f"missing model file(s): {', '.join(missing)}"

    try:
        from openwakeword.model import Model

        model = Model(
            wakeword_models=[str(model_directory(vault_root) / WAKE_MODEL_FILENAME)],
            # ONNX on Windows, and the vault's feature models rather than the
            # library's package-relative defaults.
            **use_local_models(vault_root),
        )
    except Exception as exc:  # noqa: BLE001 - reported, never swallowed
        _LOG.exception("the wake-word detector could not be initialised")
        return False, f"{type(exc).__name__}: {exc}"

    if not getattr(model, "models", None):
        return False, "the detector loaded no models"
    return True, None


def install_wake_model(vault_root: Path, *, force: bool = False) -> InstallReport:
    """Download the model through openWakeWord's official API. Idempotent.

    Uses ``openwakeword.utils.download_models``, which fetches from the URLs in
    the library's own ``MODELS`` table — the official GitHub release assets, not
    a third-party mirror. It also fetches the feature and VAD models, skipping
    any that are already present.
    """
    directory = model_directory(vault_root)

    if not module_available("openwakeword"):
        return InstallReport(
            installed=False, already_present=False, directory=directory,
            missing=REQUIRED_FILES,
            error=f"openwakeword is not installed; {VOICE_EXTRA_HINT}",
        )

    if is_installed(vault_root) and not force:
        loads, error = verify_detector_loads(vault_root)
        return InstallReport(
            installed=False,
            already_present=True,
            directory=directory,
            files=installed_files(vault_root),
            detector_loads=loads,
            error=error if not loads else None,
            notes=[LICENCE_WARNING],
        )

    directory.mkdir(parents=True, exist_ok=True)
    try:
        from openwakeword.utils import download_models

        _LOG.info("downloading the openWakeWord 'hey_jarvis' model into %s", directory)
        # Downloads hey_jarvis (ONNX and tflite) plus the melspectrogram,
        # embedding and Silero VAD models, skipping any already present.
        download_models(model_names=["hey_jarvis"], target_directory=str(directory))
    except Exception as exc:  # noqa: BLE001 - a failed download is reported
        _LOG.exception("the wake-word model download failed")
        return InstallReport(
            installed=False, already_present=False, directory=directory,
            missing=missing_files(vault_root),
            error=f"download failed: {type(exc).__name__}: {exc}",
        )

    missing = missing_files(vault_root)
    if missing:
        return InstallReport(
            installed=False, already_present=False, directory=directory,
            files=installed_files(vault_root), missing=missing,
            error=(
                "the download completed but these files are still missing: "
                f"{', '.join(missing)}"
            ),
        )

    loads, error = verify_detector_loads(vault_root)
    return InstallReport(
        installed=True,
        already_present=False,
        directory=directory,
        files=installed_files(vault_root),
        detector_loads=loads,
        error=error,
        notes=[LICENCE_WARNING],
    )


def uninstall_wake_model(vault_root: Path) -> tuple[bool, Path]:
    """Delete the whole model directory. The documented removal step."""
    directory = model_directory(vault_root)
    if not directory.exists():
        return False, directory
    shutil.rmtree(directory)
    _LOG.info("removed the wake-word model directory %s", directory)
    return True, directory
