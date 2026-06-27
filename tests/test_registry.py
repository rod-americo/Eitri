from pathlib import Path

from eitri.bootstrap import seed_initial_metastore
from eitri.config import load_config
from eitri.registry import PersistentRegistry


class FakeSession:
    def __init__(self) -> None:
        self.added = []
        self.flush_count = 0

    def add(self, value) -> None:
        self.added.append(value)

    def flush(self) -> None:
        self.flush_count += 1


def test_persistent_registry_records_operational_entities() -> None:
    session = FakeSession()
    registry = PersistentRegistry(session=session, owner_user="rodrigo")

    run = registry.create_run(
        experiment_id=1,
        config_hash="sha256:config",
        dataset_hash="sha256:dataset",
        git_commit="abc123",
        git_branch="main",
    )
    metric = registry.record_metric(run_id=1, name="loss", value=0.2, step=10, epoch=1)
    event = registry.record_event(run_id=1, event_type="run.heartbeat", payload={"ok": True})
    report = registry.record_guardrail_report(
        run_id=1,
        status="passed",
        results=[{"name": "config_hash", "passed": True}],
        summary="ok",
    )

    assert len(session.added) == 4
    assert run.owner_user == "rodrigo"
    assert metric.value_float == 0.2
    assert event.payload == {"ok": True}
    assert report.status == "passed"


def test_seed_initial_metastore_adds_bootstrap_entities() -> None:
    session = FakeSession()
    config = load_config("configs/eitri.example.yaml")

    result = seed_initial_metastore(
        session,
        config,
        experiment_path=Path("configs/experiments/chest_xray_ct_24h.yaml"),
    )

    assert {"hosts", "task", "dataset", "experiment"}.issubset(result)
    assert len(session.added) >= 8
    assert session.flush_count >= 2
