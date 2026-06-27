# Migrações Alembic

Este diretório está reservado para migrações do metastore PostgreSQL.

As declarações iniciais de modelo vivem em `src/eitri/db.py`. Gere a primeira migração depois que a URL de banco do Tyr estiver definida:

```bash
alembic revision --autogenerate -m "create eitri metastore"
alembic upgrade head
```
