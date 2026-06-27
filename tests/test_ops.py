from typer.testing import CliRunner

from eitri.cli import app
from eitri.ops import thor_probe_commands, tyr_probe_commands


def test_operational_probes_do_not_read_remote_environment() -> None:
    commands = [*tyr_probe_commands(), *thor_probe_commands()]
    command_text = "\n".join(" ".join(command.command) for command in commands)

    assert "env" not in command_text
    assert "POSTGRES" not in command_text
    assert "rm " not in command_text


def test_ops_probe_cli_defaults_to_dry_run() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["ops", "thor-probe"])

    assert result.exit_code == 0
    assert "dry-run" in result.output
    assert "nvidia-smi" in result.output
