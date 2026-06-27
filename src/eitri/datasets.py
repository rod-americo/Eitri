"""Serviços de dataset independentes da CLI."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from eitri.schemas import ExperimentYaml, load_experiment_yaml


@dataclass(frozen=True)
class DatasetCatalogItem:
    name: str
    version: str
    strategy: str
    uri: str
    structured_labels: bool


def dataset_from_experiment_config(
    path: str | Path = "configs/experiments/chest_xray_ct_24h.yaml",
) -> DatasetCatalogItem:
    experiment = load_experiment_yaml(path)
    return dataset_from_experiment(experiment)


def dataset_from_experiment(experiment: ExperimentYaml) -> DatasetCatalogItem:
    return DatasetCatalogItem(
        name=experiment.dataset.name,
        version=experiment.dataset.version,
        strategy=experiment.dataset.split.strategy,
        uri=f"data/datasets/{experiment.dataset.name}",
        structured_labels=experiment.dataset.labels.format == "structured",
    )


def list_configured_datasets() -> list[DatasetCatalogItem]:
    return [dataset_from_experiment_config()]
