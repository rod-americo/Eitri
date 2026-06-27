from typer.testing import CliRunner

from eitri.cli import app


def test_cli_exposes_required_commands() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    for command in [
        "doctor",
        "validate",
        "run",
        "experiments",
        "datasets",
        "models",
        "metrics",
        "hosts",
        "jobs",
        "web",
        "tui",
        "sync",
        "metastore",
    ]:
        assert command in result.output


def test_metastore_tables_command_lists_contract_tables() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["metastore", "tables"])

    assert result.exit_code == 0
    assert "guardrail_reports" in result.output
    assert "dataset_versions" in result.output
