"""Serviços de experimentos e planejamento de runs."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from eitri.guardrails import RunIntent, hash_file
from eitri.mock import mock_control_plane_state
from eitri.schemas import ExperimentYaml, load_experiment_yaml


@dataclass(frozen=True)
class ExperimentCatalogItem:
    name: str
    status: str
    progress: int
    loss: float | None
    validation_loss: float | None
    dataset_name: str


@dataclass(frozen=True)
class ExperimentPlan:
    intent: RunIntent
    config_hash: str
    experiment_name: str


def list_mock_experiments() -> list[ExperimentCatalogItem]:
    state = mock_control_plane_state()
    return [
        ExperimentCatalogItem(
            name=item["name"],
            status=item["status"],
            progress=item["progress"],
            loss=item["loss"],
            validation_loss=item["validation_loss"],
            dataset_name="bedside-chest-xray-ct-24h",
        )
        for item in state["experiments"]
    ]


def experiment_from_yaml(path: str | Path) -> ExperimentYaml:
    return load_experiment_yaml(path)


def build_experiment_plan(
    name: str,
    config_path: Path,
    experiment_path: Path | None,
    dataset_hash: str | None,
    target_host: str,
    dry_run: bool,
    heavy: bool,
) -> ExperimentPlan:
    effective_config = experiment_path or config_path
    intent = RunIntent(
        name=name,
        dataset_hash=dataset_hash,
        config_path=effective_config,
        config_hash=hash_file(effective_config),
        target_host=target_host,
        dry_run=dry_run,
        heavy=heavy,
    )
    return ExperimentPlan(
        intent=intent,
        config_hash=hash_file(effective_config),
        experiment_name=name,
    )
