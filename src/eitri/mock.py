"""Dados simulados contínuos para desenvolver UI antes do treinamento real."""

from __future__ import annotations

from dataclasses import asdict
from datetime import UTC, datetime
from random import Random
from typing import Any

from eitri.metrics import collect_system_metrics, simulated_training_metrics


def mock_control_plane_state(seed: int | None = None) -> dict[str, Any]:
    rng = Random(seed if seed is not None else int(datetime.now(UTC).timestamp()) // 2)
    progress = rng.randint(18, 94)
    loss = round(1.2 * (100 - progress) / 100 + rng.random() * 0.05, 4)
    validation_loss = round(loss + rng.random() * 0.1, 4)
    system_metrics = collect_system_metrics()
    training_metrics = simulated_training_metrics(seed=seed)
    return {
        "observed_at": datetime.now(UTC).isoformat(),
        "summary": {
            "experiments": 5,
            "queued_jobs": 3,
            "running_jobs": 1,
            "blocked_jobs": 2,
            "alerts": 2,
            "polling_seconds": 2,
        },
        "hosts": [
            {"name": "odin", "role": "local_development", "status": "online", "cpu": 31, "ram": 58},
            {"name": "thor", "role": "gpu_execution", "status": "simulated", "gpu": 82, "vram": 74},
            {"name": "tyr", "role": "metastore", "status": "configured", "postgres": "required"},
        ],
        "experiments": [
            {
                "name": "chest-xray-ct-24h-structured",
                "status": "running",
                "progress": progress,
                "epoch": max(1, progress // 5),
                "step": progress * 53,
                "loss": loss,
                "validation_loss": validation_loss,
                "learning_rate": 0.00012,
                "eta": f"{max(1, 100 - progress)} min",
            },
            {
                "name": "cxr-baseline-dry-run",
                "status": "planned",
                "progress": 0,
                "epoch": 0,
                "step": 0,
                "loss": None,
                "validation_loss": None,
                "learning_rate": None,
                "eta": "pending",
            },
        ],
        "jobs": [
            {
                "id": "job-thor-001",
                "host": "thor",
                "status": "running",
                "queue": "gpu",
                "progress": progress,
            },
            {
                "id": "job-odin-002",
                "host": "odin",
                "status": "planned",
                "queue": "dry-run",
                "progress": 0,
            },
            {
                "id": "job-thor-003",
                "host": "thor",
                "status": "blocked",
                "queue": "gpu",
                "progress": 0,
            },
        ],
        "metrics": [asdict(metric) for metric in [*system_metrics, *training_metrics]],
        "events": [
            {"level": "info", "message": "run heartbeat recebido", "source": "mock"},
            {
                "level": "warning",
                "message": "guardrail dataset_hash aguardando confirmação",
                "source": "guardrails",
            },
            {"level": "info", "message": "checkpoint simulado persistido", "source": "artifacts"},
        ],
        "artifacts": [
            {"name": "checkpoint atual", "uri": "checkpoints/chest-xray-ct-24h/epoch-current.ckpt"},
            {"name": "relatório de métricas", "uri": "artifacts/chest-xray-ct-24h/metrics.json"},
        ],
        "alerts": [
            {"severity": "warning", "message": "Execução em Thor exige árvore Git limpa."},
            {"severity": "info", "message": "Temperatura de GPU simulada até integração real."},
        ],
    }
