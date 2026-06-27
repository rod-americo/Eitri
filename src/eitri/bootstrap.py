"""Bootstrap persistente do metastore com entidades iniciais da plataforma."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy.orm import Session

from eitri.config import EitriConfig
from eitri.guardrails import hash_file
from eitri.registry import DatasetVersion, ExperimentSpec, PersistentRegistry
from eitri.schemas import load_experiment_yaml


def seed_initial_metastore(
    session: Session,
    config: EitriConfig,
    experiment_path: Path = Path("configs/experiments/chest_xray_ct_24h.yaml"),
) -> dict[str, object]:
    registry = PersistentRegistry(session=session, owner_user=config.owner_user)
    hosts = [
        registry.register_host(
            name=host.name,
            role=host.role,
            ssh_alias=host.ssh_alias,
            capabilities=list(host.responsibilities),
        )
        for host in config.hosts.values()
    ]
    task = registry.register_task(
        name="paired_imaging_structured_prediction",
        plugin_name="eitri.plugins.tasks.structured_radiology",
        output_mode="structured",
        metadata={"domain": config.domain},
    )
    experiment_yaml = load_experiment_yaml(experiment_path)
    dataset = DatasetVersion(
        name=experiment_yaml.dataset.name,
        version=experiment_yaml.dataset.version,
        content_hash=f"sha256:{hash_file(experiment_path)}",
        uri=str(config.storage.datasets_root / experiment_yaml.dataset.name),
        metadata={"domain": config.domain},
    )
    dataset_record = registry.register_dataset(dataset)
    experiment = registry.register_experiment(
        ExperimentSpec(
            name=experiment_yaml.experiment.name,
            objective=experiment_yaml.experiment.objective,
            dataset=dataset,
            metric_set=(
                experiment_yaml.metrics.primary,
                *tuple(experiment_yaml.metrics.secondary),
            ),
            config_hash=hash_file(experiment_path),
        )
    )
    session.flush()
    registry.register_model(
        name="structured-radiology-baseline",
        framework="plugin-defined",
        task_id=getattr(task, "id", None),
    )
    registry.register_config(
        name=experiment_yaml.experiment.name,
        uri=str(experiment_path),
        config_type="experiment",
        content_hash=hash_file(experiment_path),
        experiment_id=getattr(experiment, "id", None),
    )
    return {
        "hosts": hosts,
        "task": task,
        "dataset": dataset_record,
        "experiment": experiment,
    }
