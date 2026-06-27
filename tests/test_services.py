from pathlib import Path

from eitri.datasets import list_configured_datasets
from eitri.experiments import build_experiment_plan, list_mock_experiments
from eitri.jobs import list_mock_jobs
from eitri.models import list_planned_models
from eitri.observability import collect_observability_frame, persist_observability_frame


class FakeRegistry:
    def __init__(self) -> None:
        self.metrics = []
        self.events = []
        self.artifacts = []

    def record_metric(self, **kwargs) -> None:
        self.metrics.append(kwargs)

    def record_event(self, **kwargs) -> None:
        self.events.append(kwargs)

    def register_artifact(self, **kwargs) -> None:
        self.artifacts.append(kwargs)


def test_domain_services_return_bootstrap_catalogs() -> None:
    datasets = list_configured_datasets()
    experiments = list_mock_experiments()
    models = list_planned_models()
    jobs = list_mock_jobs()

    assert datasets[0].name == "bedside-chest-xray-ct-24h"
    assert experiments[0].name == "chest-xray-ct-24h-structured"
    assert models[0].name == "structured-radiology-baseline"
    assert jobs[0].host == "thor"


def test_build_experiment_plan_hashes_effective_config() -> None:
    plan = build_experiment_plan(
        name="smoke",
        config_path=Path("configs/eitri.example.yaml"),
        experiment_path=Path("configs/experiments/chest_xray_ct_24h.yaml"),
        dataset_hash="sha256:test",
        target_host="odin",
        dry_run=True,
        heavy=False,
    )

    assert plan.intent.config_hash == plan.config_hash
    assert plan.intent.dataset_hash == "sha256:test"


def test_observability_frame_can_be_persisted_through_registry_contract() -> None:
    frame = collect_observability_frame(seed=1)
    registry = FakeRegistry()

    counts = persist_observability_frame(registry, run_id=1, frame=frame)

    assert counts["metrics"] == len(frame.metrics)
    assert counts["events"] == len(frame.events)
    assert counts["artifacts"] == len(frame.artifacts)
    assert registry.metrics
