"""Guardrails that must pass before long-running or remote execution."""

from __future__ import annotations

import hashlib
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

from eitri.config import EitriConfig


@dataclass(frozen=True)
class GuardrailResult:
    name: str
    passed: bool
    detail: str
    severity: str = "error"


@dataclass(frozen=True)
class RunIntent:
    name: str
    dataset_ref: str | None = None
    dataset_hash: str | None = None
    dataset_path: Path | None = None
    labels_path: Path | None = None
    config_path: Path | None = None
    config_hash: str | None = None
    target_host: str = "odin"
    dry_run: bool = True
    heavy: bool = False
    override_git_dirty: bool = False
    patient_split: bool = True
    patient_leakage_detected: bool = False
    minimum_class_distribution_ok: bool = True


def evaluate_guardrails(intent: RunIntent, config: EitriConfig) -> list[GuardrailResult]:
    results = [
        GuardrailResult("valid_config", config.project_name == "Eitri", "Configuração carregada."),
        GuardrailResult("run_name", bool(intent.name.strip()), "Run name is required."),
        _dataset_hash_result(intent, config),
        _dataset_exists_result(intent),
        _file_integrity_result(intent),
        _labels_integrity_result(intent),
        _patient_split_result(intent),
        _patient_leakage_result(intent),
        _class_distribution_result(intent),
        _disk_space_result(config),
        _memory_result(),
        _gpu_result(intent),
        _host_compatibility_result(intent, config),
        _config_hash_result(intent, config),
        _dry_run_remote_result(intent, config),
        _git_commit_result(config),
        _git_branch_result(config),
        _git_clean_for_thor_result(intent),
        _heavy_training_on_odin_result(intent),
    ]
    return results


def guardrails_pass(results: list[GuardrailResult]) -> bool:
    return all(result.passed for result in results)


def hash_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_destructive_confirmation(
    confirmation: str,
    config: EitriConfig,
) -> GuardrailResult:
    expected = config.guardrails.destructive_confirmation_phrase
    return GuardrailResult(
        name="destructive_confirmation",
        passed=confirmation == expected,
        detail=f"Destructive operations require literal confirmation: {expected}",
    )


def _dataset_hash_result(intent: RunIntent, config: EitriConfig) -> GuardrailResult:
    required = config.guardrails.require_dataset_hash
    return GuardrailResult(
        "dataset_hash",
        bool(intent.dataset_hash) or not required,
        "Dataset hash is required for traceability.",
    )


def _dataset_exists_result(intent: RunIntent) -> GuardrailResult:
    if intent.dataset_path is None:
        return GuardrailResult(
            "dataset_exists",
            True,
            "Dataset path not supplied for dry planning.",
            "warning",
        )
    return GuardrailResult(
        "dataset_exists",
        intent.dataset_path.exists(),
        f"Dataset path must exist: {intent.dataset_path}",
    )


def _file_integrity_result(intent: RunIntent) -> GuardrailResult:
    if intent.dataset_path is None or not intent.dataset_path.exists():
        return GuardrailResult(
            "file_integrity",
            True,
            "Integrity check deferred until dataset path exists.",
            "warning",
        )
    files = [path for path in intent.dataset_path.rglob("*") if path.is_file()]
    return GuardrailResult("file_integrity", bool(files), "Dataset must contain readable files.")


def _labels_integrity_result(intent: RunIntent) -> GuardrailResult:
    if intent.labels_path is None:
        return GuardrailResult(
            "labels_integrity",
            True,
            "Labels path not supplied for dry planning.",
            "warning",
        )
    return GuardrailResult(
        "labels_integrity",
        intent.labels_path.exists() and intent.labels_path.stat().st_size > 0,
        "Labels file must exist and be non-empty.",
    )


def _patient_split_result(intent: RunIntent) -> GuardrailResult:
    return GuardrailResult("patient_split", intent.patient_split, "Split must be patient-level.")


def _patient_leakage_result(intent: RunIntent) -> GuardrailResult:
    return GuardrailResult(
        "patient_leakage",
        not intent.patient_leakage_detected,
        "Patient leakage must be absent across splits.",
    )


def _class_distribution_result(intent: RunIntent) -> GuardrailResult:
    return GuardrailResult(
        "minimum_class_distribution",
        intent.minimum_class_distribution_ok,
        "Each split must satisfy minimum class distribution thresholds.",
    )


def _disk_space_result(config: EitriConfig) -> GuardrailResult:
    root = config.storage.artifacts_root.parent
    if not root:
        root = Path(".")
    usage = os.statvfs(root)
    free_gb = usage.f_bavail * usage.f_frsize / 1024 / 1024 / 1024
    return GuardrailResult(
        "disk_space",
        free_gb >= 1.0,
        f"At least 1 GB free is required; found {free_gb:.1f} GB.",
    )


def _memory_result() -> GuardrailResult:
    try:
        import psutil
    except ModuleNotFoundError:
        return GuardrailResult(
            "memory_available",
            True,
            "psutil unavailable; memory check deferred.",
            "warning",
        )
    free_gb = psutil.virtual_memory().available / 1024 / 1024 / 1024
    return GuardrailResult(
        "memory_available",
        free_gb >= 1.0,
        f"At least 1 GB RAM free is required; found {free_gb:.1f} GB.",
    )


def _gpu_result(intent: RunIntent) -> GuardrailResult:
    if intent.target_host in {"odin", "local", "localhost"} and not intent.heavy:
        return GuardrailResult(
            "gpu_available",
            True,
            "GPU not required for light local dry-run.",
            "warning",
        )
    return GuardrailResult(
        "gpu_available",
        intent.dry_run,
        "GPU availability is simulated until Thor worker integration exists.",
        "warning",
    )


def _host_compatibility_result(intent: RunIntent, config: EitriConfig) -> GuardrailResult:
    host = config.hosts.get(intent.target_host)
    if host is None and intent.target_host not in {"local", "localhost"}:
        return GuardrailResult(
            "host_experiment_compatibility",
            False,
            "Target host is not configured.",
        )
    if intent.heavy and intent.target_host == "odin":
        return GuardrailResult("host_experiment_compatibility", False, "Heavy runs belong on Thor.")
    return GuardrailResult("host_experiment_compatibility", True, "Target host is compatible.")


def _config_hash_result(intent: RunIntent, config: EitriConfig) -> GuardrailResult:
    required = config.guardrails.require_config_hash
    supplied = bool(intent.config_hash)
    if not supplied and intent.config_path and intent.config_path.exists():
        supplied = bool(hash_file(intent.config_path))
    return GuardrailResult(
        "config_hash",
        supplied or not required,
        "Configuration hash is required for reproducibility.",
    )


def _dry_run_remote_result(intent: RunIntent, config: EitriConfig) -> GuardrailResult:
    remote_target = intent.target_host not in {"odin", "local", "localhost"}
    blocked = (
        config.guardrails.require_dry_run_before_remote
        and remote_target
        and not intent.dry_run
    )
    return GuardrailResult(
        "remote_dry_run",
        not blocked,
        "Remote execution must be preceded by a dry-run.",
    )


def _git_commit_result(config: EitriConfig) -> GuardrailResult:
    if not config.guardrails.require_git_commit:
        return GuardrailResult("git_commit", True, "Git commit guardrail disabled.")
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "--verify", "HEAD"],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError as exc:
        return GuardrailResult("git_commit", False, f"Could not inspect Git: {exc}")
    return GuardrailResult(
        "git_commit",
        completed.returncode == 0,
        "A Git commit must exist before experiments are registered.",
    )


def _git_branch_result(config: EitriConfig) -> GuardrailResult:
    if not config.guardrails.require_git_commit:
        return GuardrailResult("git_branch", True, "Git branch guardrail disabled.")
    completed = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        check=False,
        capture_output=True,
        text=True,
    )
    return GuardrailResult(
        "git_branch",
        completed.returncode == 0 and bool(completed.stdout.strip()),
        "Git branch must be recorded.",
    )


def _git_clean_for_thor_result(intent: RunIntent) -> GuardrailResult:
    if intent.target_host != "thor" or intent.dry_run or intent.override_git_dirty:
        return GuardrailResult(
            "git_clean_for_thor",
            True,
            "Clean tree check not required for this intent.",
        )
    completed = subprocess.run(
        ["git", "status", "--porcelain"],
        check=False,
        capture_output=True,
        text=True,
    )
    return GuardrailResult(
        "git_clean_for_thor",
        completed.returncode == 0 and completed.stdout.strip() == "",
        "Thor execution requires a clean Git tree unless explicitly overridden.",
    )


def _heavy_training_on_odin_result(intent: RunIntent) -> GuardrailResult:
    blocked = (
        intent.heavy
        and intent.target_host in {"odin", "local", "localhost"}
        and not intent.dry_run
    )
    return GuardrailResult(
        "heavy_training_on_odin",
        not blocked,
        "Heavy training on Odin requires explicit confirmation and remains blocked by default.",
    )
