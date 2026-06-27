from pathlib import Path

from eitri.config import DEFAULT_CONFIRMATION_PHRASE, load_config


def test_load_example_config() -> None:
    config = load_config(Path("configs/eitri.example.yaml"))

    assert config.project_name == "Eitri"
    assert config.domain == "radiology"
    assert config.default_dry_run is True
    assert config.owner_user == "rodrigo"
    assert config.hosts["thor"].ssh_alias == "thor"
    assert config.metastore.dialect == "postgresql"
    assert config.metastore.store_heavy_artifacts is False
    assert config.registry.persistent is True
    assert config.control_plane.host == "127.0.0.1"
    assert config.control_plane.polling_seconds == 2
    assert config.guardrails.destructive_confirmation_phrase == DEFAULT_CONFIRMATION_PHRASE
