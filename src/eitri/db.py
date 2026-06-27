"""Modelos SQLAlchemy 2 para o metastore PostgreSQL do Eitri."""

from __future__ import annotations

from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class AuditMixin:
    uuid: Mapped[object] = mapped_column(
        UUID(as_uuid=True),
        default=uuid4,
        unique=True,
        nullable=False,
    )
    version: Mapped[str] = mapped_column(String(80), default="0.1.0", nullable=False)
    content_hash: Mapped[str | None] = mapped_column(String(128))
    owner_user: Mapped[str] = mapped_column(String(120), nullable=False)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[object] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
    audit_trail: Mapped[dict] = mapped_column(JSONB, default=list, nullable=False)


class Host(AuditMixin, Base):
    __tablename__ = "hosts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    role: Mapped[str] = mapped_column(String(80), nullable=False)
    ssh_alias: Mapped[str | None] = mapped_column(String(120))
    capabilities: Mapped[dict] = mapped_column(JSONB, default=list, nullable=False)


class Worker(AuditMixin, Base):
    __tablename__ = "workers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    host_id: Mapped[int] = mapped_column(ForeignKey("hosts.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    status: Mapped[str] = mapped_column(String(60), nullable=False)
    queues: Mapped[dict] = mapped_column(JSONB, default=list, nullable=False)

    host = relationship("Host")


class Task(AuditMixin, Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    plugin_name: Mapped[str] = mapped_column(String(200), nullable=False)
    output_mode: Mapped[str] = mapped_column(String(80), nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)


class Model(AuditMixin, Base):
    __tablename__ = "models"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    task_id: Mapped[int | None] = mapped_column(ForeignKey("tasks.id"))
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    framework: Mapped[str] = mapped_column(String(120), nullable=False)
    artifact_uri: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    task = relationship("Task")


class Dataset(AuditMixin, Base):
    __tablename__ = "datasets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text)
    domain: Mapped[str] = mapped_column(String(120), nullable=False)


class DatasetVersion(AuditMixin, Base):
    __tablename__ = "dataset_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    dataset_id: Mapped[int] = mapped_column(ForeignKey("datasets.id"), nullable=False)
    uri: Mapped[str] = mapped_column(Text, nullable=False)
    statistics: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    dataset = relationship("Dataset")


class DatasetFile(AuditMixin, Base):
    __tablename__ = "dataset_files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    dataset_version_id: Mapped[int] = mapped_column(
        ForeignKey("dataset_versions.id"),
        nullable=False,
    )
    uri: Mapped[str] = mapped_column(Text, nullable=False)
    media_type: Mapped[str] = mapped_column(String(120), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)

    dataset_version = relationship("DatasetVersion")


class Split(AuditMixin, Base):
    __tablename__ = "splits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    dataset_version_id: Mapped[int] = mapped_column(
        ForeignKey("dataset_versions.id"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    strategy: Mapped[str] = mapped_column(String(80), nullable=False)
    patient_ids_hash: Mapped[str | None] = mapped_column(String(128))
    distribution: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    dataset_version = relationship("DatasetVersion")


class Experiment(AuditMixin, Base):
    __tablename__ = "experiments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    task_id: Mapped[int | None] = mapped_column(ForeignKey("tasks.id"))
    dataset_version_id: Mapped[int | None] = mapped_column(ForeignKey("dataset_versions.id"))
    name: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    objective: Mapped[str] = mapped_column(Text, nullable=False)
    metric_set: Mapped[dict] = mapped_column(JSONB, default=list, nullable=False)
    config_hash: Mapped[str | None] = mapped_column(String(128))

    task = relationship("Task")
    dataset_version = relationship("DatasetVersion")


class Config(AuditMixin, Base):
    __tablename__ = "configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    experiment_id: Mapped[int | None] = mapped_column(ForeignKey("experiments.id"))
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    uri: Mapped[str] = mapped_column(Text, nullable=False)
    config_type: Mapped[str] = mapped_column(String(80), nullable=False)
    payload_ref: Mapped[str | None] = mapped_column(Text)


class Run(AuditMixin, Base):
    __tablename__ = "runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    experiment_id: Mapped[int] = mapped_column(ForeignKey("experiments.id"), nullable=False)
    target_host_id: Mapped[int | None] = mapped_column(ForeignKey("hosts.id"))
    status: Mapped[str] = mapped_column(String(40), nullable=False)
    dry_run: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    config_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    dataset_hash: Mapped[str | None] = mapped_column(String(128))
    git_commit: Mapped[str] = mapped_column(String(80), nullable=False)
    git_branch: Mapped[str] = mapped_column(String(200), nullable=False)
    started_at: Mapped[object | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[object | None] = mapped_column(DateTime(timezone=True))
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    experiment = relationship("Experiment")
    target_host = relationship("Host")


class Job(AuditMixin, Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[int | None] = mapped_column(ForeignKey("runs.id"))
    host_id: Mapped[int | None] = mapped_column(ForeignKey("hosts.id"))
    status: Mapped[str] = mapped_column(String(40), nullable=False)
    queue: Mapped[str] = mapped_column(String(120), nullable=False)
    command_ref: Mapped[str] = mapped_column(Text, nullable=False)
    progress: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    eta_seconds: Mapped[int | None] = mapped_column(Integer)


class Metric(AuditMixin, Base):
    __tablename__ = "metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("runs.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    value_float: Mapped[float | None] = mapped_column(Float)
    value_text: Mapped[str | None] = mapped_column(Text)
    unit: Mapped[str | None] = mapped_column(String(80))
    step: Mapped[int | None] = mapped_column(Integer)
    epoch: Mapped[int | None] = mapped_column(Integer)
    recorded_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())

    run = relationship("Run")


class Event(AuditMixin, Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[int | None] = mapped_column(ForeignKey("runs.id"))
    event_type: Mapped[str] = mapped_column(String(200), nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    observed_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Artifact(AuditMixin, Base):
    __tablename__ = "artifacts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("runs.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    uri: Mapped[str] = mapped_column(Text, nullable=False)
    artifact_type: Mapped[str] = mapped_column(String(80), nullable=False)
    size_bytes: Mapped[int | None] = mapped_column(Integer)
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)


class GuardrailReport(AuditMixin, Base):
    __tablename__ = "guardrail_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[int | None] = mapped_column(ForeignKey("runs.id"))
    status: Mapped[str] = mapped_column(String(40), nullable=False)
    results: Mapped[dict] = mapped_column(JSONB, default=list, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)


METASTORE_TABLES = tuple(Base.metadata.tables.keys())
