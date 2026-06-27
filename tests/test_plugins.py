from pathlib import Path

from typer.testing import CliRunner

from eitri.cli import app
from eitri.plugins import (
    REQUIRED_PLUGIN_KINDS,
    discover_builtin_plugins,
    discover_filesystem_plugins,
    load_plugin_manifest,
    validate_experiment_with_builtin_plugins,
    validate_plugin_descriptor,
)
from eitri.schemas import load_experiment_yaml


def test_builtin_plugin_declares_all_required_capabilities() -> None:
    descriptor = discover_builtin_plugins()[0]
    validation = validate_plugin_descriptor(descriptor)

    assert validation.passed is True
    assert set(descriptor.kinds) == set(REQUIRED_PLUGIN_KINDS)


def test_filesystem_plugin_manifest_is_parseable() -> None:
    descriptor = load_plugin_manifest("plugins/radiology_chest_xray_ct_24h/plugin.toml")

    assert descriptor.name == "radiology-chest-xray-ct-24h"
    assert validate_plugin_descriptor(descriptor).passed is True


def test_filesystem_discovery_finds_reference_plugin() -> None:
    descriptors = discover_filesystem_plugins((Path("plugins"),))

    assert any(item.name == "radiology-chest-xray-ct-24h" for item in descriptors)


def test_initial_experiment_satisfies_builtin_plugin_contracts() -> None:
    experiment = load_experiment_yaml("configs/experiments/chest_xray_ct_24h.yaml")

    assert validate_experiment_with_builtin_plugins(experiment).passed is True


def test_plugins_validate_cli_passes() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["plugins", "validate"])

    assert result.exit_code == 0
    assert "radiology-chest-xray-ct-24h" in result.output
