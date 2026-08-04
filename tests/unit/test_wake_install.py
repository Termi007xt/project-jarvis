"""The wake-model bootstrap (ADR-0016, PRD section 17.2).

No test here downloads anything: the network is not a test dependency
(ARCHITECTURE section 11). What is asserted is the contract around the
download — where it goes, that it is idempotent, that "installed" means
*loadable* rather than merely present, and that the licence is stated.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from jarvis.audio import wake_install
from jarvis.audio.wake_install import (
    LICENCE,
    LICENCE_WARNING,
    REQUIRED_FILES,
    WAKE_MODEL_FILENAME,
    install_wake_model,
    is_installed,
    missing_files,
    model_directory,
    uninstall_wake_model,
    use_local_models,
)


def make_files(root: Path, names=REQUIRED_FILES) -> Path:
    directory = model_directory(root)
    directory.mkdir(parents=True, exist_ok=True)
    for name in names:
        (directory / name).write_bytes(b"not a real model")
    return directory


# -- where things go -------------------------------------------------------
def test_models_live_in_application_data_not_in_the_repository(tmp_path: Path) -> None:
    directory = model_directory(tmp_path)
    assert directory == tmp_path / "models" / "wake"
    assert "src" not in directory.parts


def test_the_windows_model_is_the_onnx_one() -> None:
    """ONNX on Windows; the library's own default is tflite."""
    assert WAKE_MODEL_FILENAME == "hey_jarvis_v0.1.onnx"
    assert WAKE_MODEL_FILENAME.endswith(".onnx")


def test_the_feature_and_vad_models_are_required_too() -> None:
    """A wake model alone cannot initialise a detector."""
    assert "melspectrogram.onnx" in REQUIRED_FILES
    assert "embedding_model.onnx" in REQUIRED_FILES
    assert "silero_vad.onnx" in REQUIRED_FILES


def test_the_repository_contains_no_model_files(repo_root: Path) -> None:
    """ADR-0016: no wake-word artefact ships with the product."""
    tracked = [
        path
        for pattern in ("*.onnx", "*.tflite")
        for path in repo_root.rglob(pattern)
        if ".venv" not in path.parts and "tools" not in path.parts
    ]
    assert not tracked, f"model files must never be committed: {tracked}"


def test_gitignore_excludes_downloaded_models(repo_root: Path) -> None:
    text = (repo_root / ".gitignore").read_text(encoding="utf-8")
    assert "*.onnx" in text
    assert "models/" in text
    assert "--install-wake-model" in text, "the install command must be documented there"


# -- completeness ----------------------------------------------------------
def test_a_partial_download_counts_as_not_installed(tmp_path: Path) -> None:
    make_files(tmp_path, names=(WAKE_MODEL_FILENAME,))
    assert not is_installed(tmp_path)
    assert "melspectrogram.onnx" in missing_files(tmp_path)


def test_all_files_present_counts_as_installed(tmp_path: Path) -> None:
    make_files(tmp_path)
    assert is_installed(tmp_path)
    assert missing_files(tmp_path) == ()


def test_nothing_present_is_not_installed(tmp_path: Path) -> None:
    assert not is_installed(tmp_path)
    assert set(missing_files(tmp_path)) == set(REQUIRED_FILES)


# -- idempotence -----------------------------------------------------------
def test_installing_twice_does_not_download_again(tmp_path: Path, monkeypatch) -> None:
    downloads: list[str] = []

    def fake_download(model_names, target_directory):  # noqa: ANN001
        downloads.append(target_directory)
        make_files(tmp_path)

    monkeypatch.setattr(wake_install, "module_available", lambda name: True)
    monkeypatch.setitem(
        __import__("sys").modules,
        "openwakeword.utils",
        type("m", (), {"download_models": staticmethod(fake_download)}),
    )
    monkeypatch.setattr(wake_install, "verify_detector_loads", lambda root: (True, None))

    first = install_wake_model(tmp_path)
    assert first.installed
    assert len(downloads) == 1

    second = install_wake_model(tmp_path)
    assert second.already_present
    assert not second.installed
    assert len(downloads) == 1, "a second install must not re-download"
    assert "Already installed" in second.describe()


# -- installed means loadable, not merely present --------------------------
def test_files_present_but_unloadable_is_reported_as_a_failure(tmp_path: Path) -> None:
    """A corrupt download must not be reported as ready (ADR-0010)."""
    make_files(tmp_path)  # plausible names, meaningless bytes
    loads, error = wake_install.verify_detector_loads(tmp_path)
    assert not loads
    assert error


def test_verification_names_the_missing_file_when_incomplete(tmp_path: Path) -> None:
    make_files(tmp_path, names=(WAKE_MODEL_FILENAME,))
    loads, error = wake_install.verify_detector_loads(tmp_path)
    assert not loads
    assert "missing model file" in (error or "")


# -- pointing the library at the vault -------------------------------------
def test_the_library_is_pointed_at_the_vault_copies(tmp_path: Path) -> None:
    make_files(tmp_path)
    kwargs = use_local_models(tmp_path)
    assert kwargs["inference_framework"] == "onnx"
    assert str(tmp_path) in kwargs["melspec_model_path"]
    assert str(tmp_path) in kwargs["embedding_model_path"]


def test_no_paths_are_claimed_when_nothing_is_installed(tmp_path: Path) -> None:
    kwargs = use_local_models(tmp_path)
    assert "melspec_model_path" not in kwargs


# -- removal ---------------------------------------------------------------
def test_uninstalling_removes_everything(tmp_path: Path) -> None:
    make_files(tmp_path)
    removed, directory = uninstall_wake_model(tmp_path)
    assert removed
    assert not directory.exists()
    assert not is_installed(tmp_path)


def test_uninstalling_when_nothing_is_there_is_harmless(tmp_path: Path) -> None:
    removed, _directory = uninstall_wake_model(tmp_path)
    assert not removed


# -- licensing (PRD 17.2, 17.3) -------------------------------------------
def test_the_licence_is_stated_and_says_non_commercial() -> None:
    assert "NonCommercial" in LICENCE or "NC" in LICENCE
    assert "NON-COMMERCIAL" in LICENCE_WARNING
    assert "never bundled" in LICENCE_WARNING


def test_the_report_carries_the_licence_warning(tmp_path: Path, monkeypatch) -> None:
    make_files(tmp_path)
    monkeypatch.setattr(wake_install, "verify_detector_loads", lambda root: (True, None))
    report = install_wake_model(tmp_path)
    assert any("NON-COMMERCIAL" in note for note in report.notes)


def test_the_report_always_shows_the_destination(tmp_path: Path) -> None:
    report = install_wake_model(tmp_path)
    assert str(model_directory(tmp_path)) in report.describe()


# -- the CLI surface -------------------------------------------------------
def test_the_install_and_uninstall_flags_exist() -> None:
    from jarvis.main import build_parser

    args = build_parser().parse_args(["--install-wake-model"])
    assert args.install_wake_model
    args = build_parser().parse_args(["--uninstall-wake-model"])
    assert args.uninstall_wake_model


def test_installing_exits_non_zero_when_the_detector_will_not_load(
    tmp_path: Path, capsys
) -> None:
    """The command's exit code reflects usability, not download success."""
    from jarvis.main import main

    make_files(tmp_path)  # present but meaningless
    exit_code = main(["--install-wake-model", "--data-dir", str(tmp_path)])
    assert exit_code == 1
    output = capsys.readouterr().out
    assert str(model_directory(tmp_path)) in output
    assert "NON-COMMERCIAL" in output


def test_the_threshold_default_reflects_the_measurement() -> None:
    """"Hey Travis" measured 0.489, so 0.5 left almost no margin."""
    from jarvis.audio.wake import DEFAULT_THRESHOLD

    assert DEFAULT_THRESHOLD > 0.5
