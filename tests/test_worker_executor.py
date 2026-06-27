import json

from typer.testing import CliRunner

from eitri.cli import app
from eitri.telemetry import JsonlEventSink
from eitri.workers import WorkerJob, report_to_registry, simulate_worker_job


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


def test_worker_simulation_emits_steps_and_jsonl_events(tmp_path) -> None:
    event_log = tmp_path / "worker-events.jsonl"
    report = simulate_worker_job(
        WorkerJob(
            job_id="job-1",
            run_id="run-1",
            queue="dry-run",
            target_host="odin",
            command_ref="test",
        ),
        step_count=3,
        sink=JsonlEventSink(event_log),
    )

    events = [json.loads(line) for line in event_log.read_text(encoding="utf-8").splitlines()]
    assert report.final_progress == 100
    assert report.status == "completed"
    assert len(events) == 3
    assert events[-1]["event_type"] == "worker.job.completed"


def test_worker_report_persists_through_registry_contract() -> None:
    report = simulate_worker_job(
        WorkerJob(
            job_id="job-1",
            run_id="run-1",
            queue="dry-run",
            target_host="odin",
            command_ref="test",
        ),
        step_count=2,
    )
    registry = FakeRegistry()

    counts = report_to_registry(registry, report, db_run_id=1)

    assert counts == {"metrics": 4, "events": 2, "artifacts": 1}
    assert registry.artifacts[0]["artifact_type"] == "checkpoint"


def test_jobs_simulate_cli_writes_event_log(tmp_path) -> None:
    event_log = tmp_path / "events.jsonl"
    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "jobs",
            "simulate",
            "--job-id",
            "job-cli",
            "--run-id",
            "run-cli",
            "--steps",
            "2",
            "--event-log",
            str(event_log),
        ],
    )

    assert result.exit_code == 0
    assert "completed" in result.output
    assert event_log.exists()
