# Evidência do Bootstrap do Metastore em Tyr

Em 2026-06-27, foi criado em `ginnungagap-postgres` o banco PostgreSQL `eitri` com role dedicada `eitri`. A credencial foi rotacionada durante o procedimento, gravada apenas em `.env` local e em `/home/rodrigo/Eitri/.env` no Thor, ambos com permissão `600`, e os arquivos temporários usados em Tyr foram removidos. Este arquivo não contém segredos.

Foram executados `eitri metastore check-url`, `alembic upgrade head` e `eitri metastore seed-initial --execute` usando `EITRI_DATABASE_URL`. A versão Alembic aplicada é `0001_create_eitri_metastore`.

Contagens verificadas após o seed: `alembic_version=1`, `hosts=3`, `tasks=1`, `datasets=1`, `dataset_versions=1`, `experiments=1`, `models=1`, `configs=1`, `workers=0`, `dataset_files=0`, `splits=0`, `runs=0`, `jobs=0`, `metrics=0`, `events=0`, `artifacts=0`, `guardrail_reports=0`.
