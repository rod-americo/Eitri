"""Criação de engine e sessões para o metastore PostgreSQL."""

from __future__ import annotations

import os
from dataclasses import dataclass

from sqlalchemy import create_engine
from sqlalchemy.dialects import postgresql
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.schema import CreateTable

from eitri.db import Base


@dataclass(frozen=True)
class DatabaseSettings:
    url: str

    @classmethod
    def from_env(cls, env_name: str = "EITRI_DATABASE_URL") -> DatabaseSettings:
        value = os.environ.get(env_name)
        if not value:
            raise RuntimeError(
                f"Defina {env_name} com uma URL PostgreSQL antes de usar o metastore."
            )
        return cls(url=value)


def create_postgres_engine(settings: DatabaseSettings) -> Engine:
    if settings.url.startswith("sqlite"):
        raise ValueError("Eitri exige PostgreSQL; SQLite não é permitido para o metastore.")
    if not settings.url.startswith(("postgresql://", "postgresql+psycopg://")):
        raise ValueError("A URL do metastore deve usar PostgreSQL.")
    url = settings.url
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    return create_engine(url, pool_pre_ping=True)


def session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, expire_on_commit=False)


def render_postgres_ddl() -> str:
    """Renderiza DDL PostgreSQL para auditoria sem abrir conexão com Tyr."""

    dialect = postgresql.dialect()
    statements = [
        str(CreateTable(table).compile(dialect=dialect)).strip()
        for table in Base.metadata.sorted_tables
    ]
    return ";\n\n".join(statements) + ";"
