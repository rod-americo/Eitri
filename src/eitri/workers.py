"""Contratos de worker e heartbeat para execução futura em Thor."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from socket import gethostname
from typing import Any

from eitri.metrics import collect_system_metrics, simulated_training_metrics
from eitri.telemetry import Event, JsonlEventSink


@dataclass(frozen=True)
class WorkerHeartbeat:
    worker_name: str
    host_name: str
    status: str
    queues: tuple[str, ...]
    observed_at: str
    metrics: list[dict[str, Any]] = field(default_factory=list)


@dataclass(frozen=True)
class WorkerJob:
    job_id: str
    run_id: str
    queue: str
    target_host: str
    command_ref: str
    dry_run: bool = True


@dataclass(frozen=True)
class WorkerStep:
    job_id: str
    run_id: str
    status: str
    progress: int
    epoch: int
    step: int
    loss: float
    validation_loss: float
    checkpoint: str
    event_type: str


@dataclass(frozen=True)
class WorkerExecutionReport:
    job: WorkerJob
    worker_name: str
    status: str
    steps: tuple[WorkerStep, ...]
    started_at: str
    finished_at: str

    @property
    def final_progress(self) -> int:
        return self.steps[-1].progress if self.steps else 0


def local_worker_heartbeat(
    worker_name: str = "odin-local",
    queues: tuple[str, ...] = ("dry-run", "control-plane"),
) -> WorkerHeartbeat:
    metrics = [
        {"name": metric.name, "value": metric.value, "unit": metric.unit}
        for metric in [*collect_system_metrics(), *simulated_training_metrics()]
    ]
    return WorkerHeartbeat(
        worker_name=worker_name,
        host_name=gethostname(),
        status="online",
        queues=queues,
        observed_at=datetime.now(UTC).isoformat(),
        metrics=metrics,
    )


def thor_worker_contract() -> dict[str, Any]:
    return {
        "host": "thor",
        "queues": ["gpu", "benchmark", "heavy-inference"],
        "required_transport": "git",
        "required_telemetry": [
            "heartbeat",
            "cpu",
            "ram",
            "gpu",
            "vram",
            "temperature",
            "progress",
            "loss",
            "validation_loss",
            "checkpoint",
        ],
    }


def simulate_worker_job(
    job: WorkerJob,
    worker_name: str = "odin-local",
    step_count: int = 5,
    sink: JsonlEventSink | None = None,
) -> WorkerExecutionReport:
    """Executa um job simulado, emitindo eventos observáveis sem treinamento real."""

    started_at = datetime.now(UTC).isoformat()
    steps: list[WorkerStep] = []
    for index in range(1, step_count + 1):
        progress = int(index * 100 / step_count)
        loss = round(max(0.05, 1.0 - progress / 130), 4)
        validation_loss = round(loss + 0.05, 4)
        step = WorkerStep(
            job_id=job.job_id,
            run_id=job.run_id,
            status="running" if progress < 100 else "completed",
            progress=progress,
            epoch=index,
            step=index * 100,
            loss=loss,
            validation_loss=validation_loss,
            checkpoint=f"epoch-{index:03d}.ckpt",
            event_type="worker.job.progress" if progress < 100 else "worker.job.completed",
        )
        steps.append(step)
        if sink is not None:
            sink.emit(
                Event(
                    event_type=step.event_type,
                    run_id=job.run_id,
                    payload={
                        "job_id": job.job_id,
                        "worker_name": worker_name,
                        "status": step.status,
                        "progress": step.progress,
                        "epoch": step.epoch,
                        "step": step.step,
                        "loss": step.loss,
                        "validation_loss": step.validation_loss,
                        "checkpoint": step.checkpoint,
                        "dry_run": job.dry_run,
                    },
                )
            )
    return WorkerExecutionReport(
        job=job,
        worker_name=worker_name,
        status="completed",
        steps=tuple(steps),
        started_at=started_at,
        finished_at=datetime.now(UTC).isoformat(),
    )


def report_to_registry(registry, report: WorkerExecutionReport, db_run_id: int) -> dict[str, int]:
    """Persiste relatório de worker por meio do contrato de registry."""

    metric_count = 0
    event_count = 0
    artifact_count = 0
    for step in report.steps:
        registry.record_metric(
            run_id=db_run_id,
            name="loss",
            value=step.loss,
            step=step.step,
            epoch=step.epoch,
        )
        registry.record_metric(
            run_id=db_run_id,
            name="validation_loss",
            value=step.validation_loss,
            step=step.step,
            epoch=step.epoch,
        )
        metric_count += 2
        registry.record_event(
            run_id=db_run_id,
            event_type=step.event_type,
            payload={
                "job_id": step.job_id,
                "progress": step.progress,
                "checkpoint": step.checkpoint,
            },
        )
        event_count += 1
    if report.steps:
        registry.register_artifact(
            run_id=db_run_id,
            name="checkpoint atual",
            uri=f"checkpoints/{report.job.run_id}/{report.steps[-1].checkpoint}",
            artifact_type="checkpoint",
            content_hash="sha256:simulated-worker",
        )
        artifact_count += 1
    return {"metrics": metric_count, "events": event_count, "artifacts": artifact_count}
