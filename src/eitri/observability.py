"""Serviços de observabilidade compartilhados por CLI, TUI, Web e registry."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from eitri.metrics import MetricSample, collect_system_metrics, simulated_training_metrics
from eitri.mock import mock_control_plane_state
from eitri.registry import PersistentRegistry


@dataclass(frozen=True)
class ObservabilityFrame:
    metrics: tuple[MetricSample, ...]
    events: tuple[dict[str, Any], ...]
    artifacts: tuple[dict[str, Any], ...]


def collect_observability_frame(seed: int | None = None) -> ObservabilityFrame:
    state = mock_control_plane_state(seed=seed)
    metrics = tuple([*collect_system_metrics(), *simulated_training_metrics(seed=seed)])
    return ObservabilityFrame(
        metrics=metrics,
        events=tuple(state["events"]),
        artifacts=tuple(state["artifacts"]),
    )


def persist_observability_frame(
    registry: PersistentRegistry,
    run_id: int,
    frame: ObservabilityFrame,
) -> dict[str, int]:
    metric_count = 0
    event_count = 0
    artifact_count = 0
    for metric in frame.metrics:
        registry.record_metric(
            run_id=run_id,
            name=metric.name,
            value=metric.value,
            unit=metric.unit,
        )
        metric_count += 1
    for event in frame.events:
        registry.record_event(
            run_id=run_id,
            event_type=f"mock.{event['level']}",
            payload=event,
        )
        event_count += 1
    for artifact in frame.artifacts:
        registry.register_artifact(
            run_id=run_id,
            name=artifact["name"],
            uri=artifact["uri"],
            artifact_type="mock",
            content_hash="sha256:mock",
        )
        artifact_count += 1
    return {"metrics": metric_count, "events": event_count, "artifacts": artifact_count}
