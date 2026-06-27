"""In-memory registry contracts for datasets, experiments, models, and runs."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from sqlalchemy.orm import Session

from eitri import db


@dataclass(frozen=True)
class DatasetVersion:
    name: str
    version: str
    content_hash: str
    uri: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ExperimentSpec:
    name: str
    objective: str
    dataset: DatasetVersion
    metric_set: tuple[str, ...]
    config_hash: str
    tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class RunRecord:
    experiment_name: str
    run_id: str
    status: str
    target_host: str
    dry_run: bool
    created_at: str


class Registry:
    """Registry transitório para dry-runs locais antes da conexão com Tyr."""

    def __init__(self) -> None:
        self.datasets: dict[tuple[str, str], DatasetVersion] = {}
        self.experiments: dict[str, ExperimentSpec] = {}
        self.runs: dict[str, RunRecord] = {}

    def register_dataset(self, dataset: DatasetVersion) -> DatasetVersion:
        key = (dataset.name, dataset.version)
        if key in self.datasets:
            raise ValueError(
                f"Dataset version already registered: {dataset.name}:{dataset.version}"
            )
        self.datasets[key] = dataset
        return dataset

    def register_experiment(self, spec: ExperimentSpec) -> ExperimentSpec:
        if spec.name in self.experiments:
            raise ValueError(f"Experiment already registered: {spec.name}")
        self.experiments[spec.name] = spec
        return spec

    def create_run(self, experiment_name: str, target_host: str, dry_run: bool) -> RunRecord:
        if experiment_name not in self.experiments:
            raise ValueError(f"Unknown experiment: {experiment_name}")
        record = RunRecord(
            experiment_name=experiment_name,
            run_id=str(uuid4()),
            status="planned" if dry_run else "queued",
            target_host=target_host,
            dry_run=dry_run,
            created_at=datetime.now(UTC).isoformat(),
        )
        self.runs[record.run_id] = record
        return record


class PersistentRegistry:
    """Registry persistente sobre PostgreSQL via SQLAlchemy."""

    def __init__(self, session: Session, owner_user: str) -> None:
        self.session = session
        self.owner_user = owner_user

    def register_host(
        self,
        name: str,
        role: str,
        ssh_alias: str | None = None,
        capabilities: list[str] | None = None,
    ) -> db.Host:
        host = db.Host(
            name=name,
            role=role,
            ssh_alias=ssh_alias,
            capabilities=capabilities or [],
            owner_user=self.owner_user,
            audit_trail=[{"action": "register_host", "actor": self.owner_user}],
        )
        self.session.add(host)
        return host

    def register_worker(
        self,
        host_id: int,
        name: str,
        status: str = "idle",
        queues: list[str] | None = None,
    ) -> db.Worker:
        record = db.Worker(
            host_id=host_id,
            name=name,
            status=status,
            queues=queues or [],
            owner_user=self.owner_user,
            audit_trail=[{"action": "register_worker", "actor": self.owner_user}],
        )
        self.session.add(record)
        return record

    def register_task(
        self,
        name: str,
        plugin_name: str,
        output_mode: str,
        metadata: dict[str, Any] | None = None,
    ) -> db.Task:
        record = db.Task(
            name=name,
            plugin_name=plugin_name,
            output_mode=output_mode,
            metadata_json=metadata or {},
            owner_user=self.owner_user,
            audit_trail=[{"action": "register_task", "actor": self.owner_user}],
        )
        self.session.add(record)
        return record

    def register_model(
        self,
        name: str,
        framework: str,
        task_id: int | None = None,
        artifact_uri: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> db.Model:
        record = db.Model(
            task_id=task_id,
            name=name,
            framework=framework,
            artifact_uri=artifact_uri,
            metadata_json=metadata or {},
            owner_user=self.owner_user,
            audit_trail=[{"action": "register_model", "actor": self.owner_user}],
        )
        self.session.add(record)
        return record

    def register_dataset(self, dataset: DatasetVersion) -> db.Dataset:
        record = db.Dataset(
            name=dataset.name,
            description=dataset.metadata.get("description"),
            domain=str(dataset.metadata.get("domain", "radiology")),
            version=dataset.version,
            content_hash=dataset.content_hash,
            owner_user=self.owner_user,
            audit_trail=[{"action": "register_dataset", "actor": self.owner_user}],
        )
        self.session.add(record)
        self.session.flush()
        self.session.add(
            db.DatasetVersion(
                dataset_id=record.id,
                uri=dataset.uri,
                version=dataset.version,
                content_hash=dataset.content_hash,
                statistics=dataset.metadata.get("statistics", {}),
                owner_user=self.owner_user,
                audit_trail=[
                    {"action": "register_dataset_version", "actor": self.owner_user}
                ],
            )
        )
        return record

    def register_dataset_file(
        self,
        dataset_version_id: int,
        uri: str,
        media_type: str,
        size_bytes: int,
        content_hash: str,
    ) -> db.DatasetFile:
        record = db.DatasetFile(
            dataset_version_id=dataset_version_id,
            uri=uri,
            media_type=media_type,
            size_bytes=size_bytes,
            content_hash=content_hash,
            owner_user=self.owner_user,
            audit_trail=[{"action": "register_dataset_file", "actor": self.owner_user}],
        )
        self.session.add(record)
        return record

    def register_split(
        self,
        dataset_version_id: int,
        name: str,
        strategy: str,
        patient_ids_hash: str | None = None,
        distribution: dict[str, Any] | None = None,
    ) -> db.Split:
        record = db.Split(
            dataset_version_id=dataset_version_id,
            name=name,
            strategy=strategy,
            patient_ids_hash=patient_ids_hash,
            distribution=distribution or {},
            owner_user=self.owner_user,
            audit_trail=[{"action": "register_split", "actor": self.owner_user}],
        )
        self.session.add(record)
        return record

    def register_experiment(self, spec: ExperimentSpec) -> db.Experiment:
        record = db.Experiment(
            name=spec.name,
            objective=spec.objective,
            metric_set=list(spec.metric_set),
            config_hash=spec.config_hash,
            owner_user=self.owner_user,
            audit_trail=[{"action": "register_experiment", "actor": self.owner_user}],
        )
        self.session.add(record)
        return record

    def register_config(
        self,
        name: str,
        uri: str,
        config_type: str,
        content_hash: str,
        experiment_id: int | None = None,
        payload_ref: str | None = None,
    ) -> db.Config:
        record = db.Config(
            experiment_id=experiment_id,
            name=name,
            uri=uri,
            config_type=config_type,
            payload_ref=payload_ref,
            content_hash=content_hash,
            owner_user=self.owner_user,
            audit_trail=[{"action": "register_config", "actor": self.owner_user}],
        )
        self.session.add(record)
        return record

    def create_run(
        self,
        experiment_id: int,
        config_hash: str,
        git_commit: str,
        git_branch: str,
        target_host_id: int | None = None,
        dataset_hash: str | None = None,
        dry_run: bool = True,
    ) -> db.Run:
        record = db.Run(
            experiment_id=experiment_id,
            target_host_id=target_host_id,
            status="planned" if dry_run else "queued",
            dry_run=dry_run,
            config_hash=config_hash,
            dataset_hash=dataset_hash,
            git_commit=git_commit,
            git_branch=git_branch,
            owner_user=self.owner_user,
            audit_trail=[{"action": "create_run", "actor": self.owner_user}],
        )
        self.session.add(record)
        return record

    def queue_job(
        self,
        run_id: int,
        host_id: int,
        queue: str,
        command_ref: str,
    ) -> db.Job:
        record = db.Job(
            run_id=run_id,
            host_id=host_id,
            status="queued",
            queue=queue,
            command_ref=command_ref,
            owner_user=self.owner_user,
            audit_trail=[{"action": "queue_job", "actor": self.owner_user}],
        )
        self.session.add(record)
        return record

    def record_metric(
        self,
        run_id: int,
        name: str,
        value: float | str,
        unit: str | None = None,
        step: int | None = None,
        epoch: int | None = None,
    ) -> db.Metric:
        record = db.Metric(
            run_id=run_id,
            name=name,
            value_float=value if isinstance(value, int | float) else None,
            value_text=None if isinstance(value, int | float) else str(value),
            unit=unit,
            step=step,
            epoch=epoch,
            owner_user=self.owner_user,
            audit_trail=[{"action": "record_metric", "actor": self.owner_user}],
        )
        self.session.add(record)
        return record

    def record_event(
        self,
        event_type: str,
        payload: dict[str, Any],
        run_id: int | None = None,
    ) -> db.Event:
        record = db.Event(
            run_id=run_id,
            event_type=event_type,
            payload=payload,
            owner_user=self.owner_user,
            audit_trail=[{"action": "record_event", "actor": self.owner_user}],
        )
        self.session.add(record)
        return record

    def register_artifact(
        self,
        run_id: int,
        name: str,
        uri: str,
        artifact_type: str,
        content_hash: str,
        size_bytes: int | None = None,
    ) -> db.Artifact:
        record = db.Artifact(
            run_id=run_id,
            name=name,
            uri=uri,
            artifact_type=artifact_type,
            content_hash=content_hash,
            size_bytes=size_bytes,
            owner_user=self.owner_user,
            audit_trail=[{"action": "register_artifact", "actor": self.owner_user}],
        )
        self.session.add(record)
        return record

    def record_guardrail_report(
        self,
        status: str,
        results: list[dict[str, Any]],
        summary: str,
        run_id: int | None = None,
    ) -> db.GuardrailReport:
        record = db.GuardrailReport(
            run_id=run_id,
            status=status,
            results=results,
            summary=summary,
            owner_user=self.owner_user,
            audit_trail=[{"action": "record_guardrail_report", "actor": self.owner_user}],
        )
        self.session.add(record)
        return record
