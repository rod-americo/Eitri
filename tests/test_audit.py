from typer.testing import CliRunner

from eitri.audit import audit_bootstrap
from eitri.cli import app


def test_bootstrap_audit_separates_passes_from_tyr_external_pending() -> None:
    report = audit_bootstrap()
    statuses = {item.key: item.status for item in report.requirements}

    assert statuses["cli"] == "passed"
    assert statuses["postgres_contract"] == "passed"
    assert statuses["plugins"] == "passed"
    assert statuses["tyr_applied_migration"] == "external_pending"
    assert statuses["thor_real_worker"] == "passed"
    assert report.complete is False


def test_audit_cli_reports_summary_and_strict_fails_until_tyr_migration() -> None:
    runner = CliRunner()

    normal = runner.invoke(app, ["audit"])
    strict = runner.invoke(app, ["audit", "--strict"])

    assert normal.exit_code == 0
    assert "external_pending" in normal.output
    assert strict.exit_code == 2
