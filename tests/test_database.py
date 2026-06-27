import pytest

from eitri.database import DatabaseSettings, create_postgres_engine, render_postgres_ddl
from eitri.db import METASTORE_TABLES


def test_metastore_declares_required_tables() -> None:
    required = {
        "hosts",
        "workers",
        "models",
        "tasks",
        "datasets",
        "dataset_versions",
        "dataset_files",
        "splits",
        "experiments",
        "runs",
        "jobs",
        "metrics",
        "events",
        "artifacts",
        "configs",
        "guardrail_reports",
    }

    assert required.issubset(set(METASTORE_TABLES))


def test_sqlite_is_rejected_for_metastore() -> None:
    with pytest.raises(ValueError, match="PostgreSQL"):
        create_postgres_engine(DatabaseSettings(url="sqlite:///eitri.db"))


def test_postgres_ddl_mentions_required_tables() -> None:
    ddl = render_postgres_ddl()

    assert "CREATE TABLE hosts" in ddl
    assert "CREATE TABLE guardrail_reports" in ddl
    assert "JSONB" in ddl
    assert "UUID" in ddl
