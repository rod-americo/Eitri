from pathlib import Path


def test_initial_alembic_migration_exists() -> None:
    migration = Path("migrations/versions/0001_create_eitri_metastore.py")
    content = migration.read_text(encoding="utf-8")

    assert migration.exists()
    assert "revision = \"0001_create_eitri_metastore\"" in content
    assert "Base.metadata.create_all" in content
