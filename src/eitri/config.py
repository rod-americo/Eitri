"""Configuration loading and validation for Eitri."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    import yaml
except ModuleNotFoundError:  # pragma: no cover - exercised only before dependencies install
    yaml = None


DEFAULT_CONFIRMATION_PHRASE = "CONFIRMAR EXCLUSÃO"


@dataclass(frozen=True)
class HostConfig:
    name: str
    role: str
    ssh_alias: str | None = None
    responsibilities: tuple[str, ...] = ()


@dataclass(frozen=True)
class StorageConfig:
    datasets_root: Path = Path("data/datasets")
    artifacts_root: Path = Path("artifacts")
    checkpoints_root: Path = Path("checkpoints")
    logs_root: Path = Path("logs")
    cache_root: Path = Path("cache")


@dataclass(frozen=True)
class GuardrailConfig:
    require_git_commit: bool = True
    require_dataset_hash: bool = True
    require_config_hash: bool = True
    require_dry_run_before_remote: bool = True
    require_explicit_destructive_confirmation: bool = True
    destructive_confirmation_phrase: str = DEFAULT_CONFIRMATION_PHRASE


@dataclass(frozen=True)
class TelemetryConfig:
    event_log_path: Path = Path("logs/events.jsonl")
    persist_metrics: bool = True
    heartbeat_seconds: int = 30


@dataclass(frozen=True)
class MetastoreConfig:
    dialect: str = "postgresql"
    store_heavy_artifacts: bool = False
    database_url_env: str = "EITRI_DATABASE_URL"
    forbidden_payloads: tuple[str, ...] = (
        "images",
        "dicom",
        "png",
        "checkpoints",
        "long_logs",
    )


@dataclass(frozen=True)
class PluginConfig:
    enabled: bool = True
    search_paths: tuple[Path, ...] = (Path("plugins"),)


@dataclass(frozen=True)
class RegistryConfig:
    require_unique_run_name: bool = True
    compare_by_metric_set: bool = True
    objective_audit_required: bool = True
    persistent: bool = True


@dataclass(frozen=True)
class ControlPlaneConfig:
    host: str = "127.0.0.1"
    port: int = 8010
    polling_seconds: int = 2
    allow_public_bind: bool = False


@dataclass(frozen=True)
class EitriConfig:
    project_name: str = "Eitri"
    domain: str = "radiology"
    default_dry_run: bool = True
    owner_user: str = "unknown"
    hosts: dict[str, HostConfig] = field(default_factory=dict)
    storage: StorageConfig = field(default_factory=StorageConfig)
    guardrails: GuardrailConfig = field(default_factory=GuardrailConfig)
    telemetry: TelemetryConfig = field(default_factory=TelemetryConfig)
    metastore: MetastoreConfig = field(default_factory=MetastoreConfig)
    registry: RegistryConfig = field(default_factory=RegistryConfig)
    plugins: PluginConfig = field(default_factory=PluginConfig)
    control_plane: ControlPlaneConfig = field(default_factory=ControlPlaneConfig)


def load_config(path: str | Path) -> EitriConfig:
    """Load an Eitri YAML configuration file."""

    config_path = Path(path)
    raw = _load_yaml(config_path)
    return parse_config(raw)


def parse_config(raw: dict[str, Any]) -> EitriConfig:
    project = raw.get("project", {})
    hosts = {
        name: HostConfig(
            name=name,
            role=str(values.get("role", "")),
            ssh_alias=values.get("ssh_alias"),
            responsibilities=tuple(values.get("responsibilities", ())),
        )
        for name, values in raw.get("hosts", {}).items()
    }
    storage_raw = raw.get("storage", {})
    guardrails_raw = raw.get("guardrails", {})
    telemetry_raw = raw.get("telemetry", {})
    metastore_raw = raw.get("metastore", {})
    registry_raw = raw.get("registry", {})
    tyr = raw.get("hosts", {}).get("tyr", {})
    plugins_raw = raw.get("plugins", {})
    control_plane_raw = raw.get("control_plane", {})

    return EitriConfig(
        project_name=str(project.get("name", "Eitri")),
        domain=str(project.get("domain", "radiology")),
        default_dry_run=bool(project.get("default_dry_run", True)),
        owner_user=str(project.get("owner_user", "unknown")),
        hosts=hosts,
        storage=StorageConfig(
            datasets_root=Path(storage_raw.get("datasets_root", "data/datasets")),
            artifacts_root=Path(storage_raw.get("artifacts_root", "artifacts")),
            checkpoints_root=Path(storage_raw.get("checkpoints_root", "checkpoints")),
            logs_root=Path(storage_raw.get("logs_root", "logs")),
            cache_root=Path(storage_raw.get("cache_root", "cache")),
        ),
        guardrails=GuardrailConfig(
            require_git_commit=bool(guardrails_raw.get("require_git_commit", True)),
            require_dataset_hash=bool(guardrails_raw.get("require_dataset_hash", True)),
            require_config_hash=bool(guardrails_raw.get("require_config_hash", True)),
            require_dry_run_before_remote=bool(
                guardrails_raw.get("require_dry_run_before_remote", True)
            ),
            require_explicit_destructive_confirmation=bool(
                guardrails_raw.get("require_explicit_destructive_confirmation", True)
            ),
            destructive_confirmation_phrase=str(
                guardrails_raw.get(
                    "destructive_confirmation_phrase",
                    DEFAULT_CONFIRMATION_PHRASE,
                )
            ),
        ),
        telemetry=TelemetryConfig(
            event_log_path=Path(telemetry_raw.get("event_log_path", "logs/events.jsonl")),
            persist_metrics=bool(telemetry_raw.get("persist_metrics", True)),
            heartbeat_seconds=int(telemetry_raw.get("heartbeat_seconds", 30)),
        ),
        metastore=MetastoreConfig(
            dialect=str(metastore_raw.get("dialect", "postgresql")),
            store_heavy_artifacts=bool(metastore_raw.get("store_heavy_artifacts", False)),
            database_url_env=str(tyr.get("database_url_env", "EITRI_DATABASE_URL")),
            forbidden_payloads=tuple(
                metastore_raw.get(
                    "forbidden_payloads",
                    ["images", "dicom", "png", "checkpoints", "long_logs"],
                )
            ),
        ),
        registry=RegistryConfig(
            require_unique_run_name=bool(registry_raw.get("require_unique_run_name", True)),
            compare_by_metric_set=bool(registry_raw.get("compare_by_metric_set", True)),
            objective_audit_required=bool(registry_raw.get("objective_audit_required", True)),
            persistent=bool(registry_raw.get("persistent", True)),
        ),
        plugins=PluginConfig(
            enabled=bool(plugins_raw.get("enabled", True)),
            search_paths=tuple(Path(path) for path in plugins_raw.get("search_paths", ["plugins"])),
        ),
        control_plane=ControlPlaneConfig(
            host=str(control_plane_raw.get("host", "127.0.0.1")),
            port=int(control_plane_raw.get("port", 8010)),
            polling_seconds=int(control_plane_raw.get("polling_seconds", 2)),
            allow_public_bind=bool(control_plane_raw.get("allow_public_bind", False)),
        ),
    )


def _load_yaml(path: Path) -> dict[str, Any]:
    if yaml is None:
        raise RuntimeError("PyYAML is required to load Eitri configuration files.")
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Expected mapping at {path}")
    return data
