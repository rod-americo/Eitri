"""create eitri metastore

Revision ID: 0001_create_eitri_metastore
Revises:
Create Date: 2026-06-27
"""

from __future__ import annotations

from alembic import op

from eitri.db import Base

revision = "0001_create_eitri_metastore"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    Base.metadata.drop_all(bind=op.get_bind())
