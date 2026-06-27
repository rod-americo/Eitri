"""Contratos de domínio independentes de banco para a plataforma Eitri."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Literal
from uuid import uuid4


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


@dataclass(frozen=True)
class AuditEntry:
    action: str
    actor: str
    detail: str
    observed_at: str = field(default_factory=utc_now)


@dataclass(frozen=True)
class EntityIdentity:
    uuid: str = field(default_factory=lambda: str(uuid4()))
    version: str = "0.1.0"
    content_hash: str | None = None
    owner_user: str = "unknown"
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)
    audit_trail: tuple[AuditEntry, ...] = ()


@dataclass(frozen=True)
class Host(EntityIdentity):
    name: str = "odin"
    role: Literal["local_development", "gpu_execution", "metastore"] = "local_development"
    ssh_alias: str | None = None
    capabilities: tuple[str, ...] = ()


@dataclass(frozen=True)
class Worker(EntityIdentity):
    host_uuid: str = ""
    name: str = ""
    status: str = "idle"
    queues: tuple[str, ...] = ()


@dataclass(frozen=True)
class Model(EntityIdentity):
    name: str = ""
    task_uuid: str | None = None
    framework: str = "unknown"
    artifact_uri: str | None = None


@dataclass(frozen=True)
class Task(EntityIdentity):
    name: str = ""
    plugin_name: str = ""
    output_mode: str = "structured"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Dataset(EntityIdentity):
    name: str = ""
    description: str = ""
    domain: str = "radiology"


@dataclass(frozen=True)
class DatasetVersion(EntityIdentity):
    dataset_uuid: str = ""
    uri: str = ""
    statistics: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DatasetFile(EntityIdentity):
    dataset_version_uuid: str = ""
    uri: str = ""
    media_type: str = "unknown"
    size_bytes: int = 0


@dataclass(frozen=True)
class Split(EntityIdentity):
    dataset_version_uuid: str = ""
    name: str = "train"
    strategy: str = "patient"
    patient_ids_hash: str | None = None


@dataclass(frozen=True)
class Experiment(EntityIdentity):
    name: str = ""
    objective: str = ""
    task_uuid: str | None = None
    dataset_version_uuid: str | None = None
    metric_set: tuple[str, ...] = ()


@dataclass(frozen=True)
class Run(EntityIdentity):
    experiment_uuid: str = ""
    target_host_uuid: str | None = None
    status: str = "planned"
    dry_run: bool = True
    git_commit: str | None = None
    git_branch: str | None = None


@dataclass(frozen=True)
class Job(EntityIdentity):
    run_uuid: str = ""
    host_uuid: str = ""
    status: str = "queued"
    queue: str = "default"
    command_ref: str = ""


@dataclass(frozen=True)
class Metric(EntityIdentity):
    run_uuid: str = ""
    name: str = ""
    value: float | str = 0.0
    step: int | None = None


@dataclass(frozen=True)
class Event(EntityIdentity):
    run_uuid: str | None = None
    event_type: str = ""
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Artifact(EntityIdentity):
    run_uuid: str = ""
    name: str = ""
    uri: str = ""
    artifact_type: str = "generic"


@dataclass(frozen=True)
class Config(EntityIdentity):
    name: str = ""
    uri: str = ""
    config_type: str = "experiment"


@dataclass(frozen=True)
class GuardrailReport(EntityIdentity):
    run_uuid: str | None = None
    status: Literal["passed", "failed", "warning"] = "warning"
    results: tuple[dict[str, Any], ...] = ()
