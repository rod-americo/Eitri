from eitri.config import EitriConfig
from eitri.sync import git_sync_plan, validate_destructive_sync
from eitri.workers import local_worker_heartbeat, thor_worker_contract


def test_git_sync_plan_preserves_official_flow() -> None:
    plan = git_sync_plan("thor")
    commands = [step.command for step in plan.steps]

    assert commands == ["git status", "git commit", "git push", "ssh thor 'git pull'"]


def test_destructive_sync_requires_listing_and_literal_confirmation() -> None:
    config = EitriConfig()

    missing_listing = validate_destructive_sync("CONFIRMAR EXCLUSÃO", config, [])
    accepted = validate_destructive_sync("CONFIRMAR EXCLUSÃO", config, ["artifacts/old"])

    assert missing_listing.passed is False
    assert accepted.passed is True


def test_worker_contracts_include_required_telemetry() -> None:
    heartbeat = local_worker_heartbeat()
    contract = thor_worker_contract()

    assert heartbeat.status == "online"
    assert heartbeat.metrics
    assert "gpu" in contract["required_telemetry"]
    assert contract["required_transport"] == "git"
