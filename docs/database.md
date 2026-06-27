# Banco de Dados

O PostgreSQL em Tyr é obrigatório e atua como metastore central do Eitri. SQLite não é permitido como metastore porque o projeto precisa nascer com contratos compatíveis com operação real, múltiplos hosts, auditoria, concorrência e evolução por migrações.

## Entidades

O metastore declara entidades para `hosts`, `workers`, `models`, `tasks`, `datasets`, `dataset_versions`, `dataset_files`, `splits`, `experiments`, `runs`, `jobs`, `metrics`, `events`, `artifacts`, `configs` e `guardrail_reports`. Todas as entidades possuem UUID, versão, hash opcional, usuário responsável, timestamps e trilha de auditoria.

## O Que Entra no PostgreSQL

O banco armazena catálogo, versões, referências, estatísticas, métricas, eventos, jobs, modelos, configurações, guardrails, hashes, metadados e histórico. O objetivo é permitir auditoria objetiva sem depender da memória de quem executou o experimento.

## O Que Não Entra no PostgreSQL

Imagens, DICOM, PNG, checkpoints, artefatos pesados e logs extensos permanecem no filesystem. O PostgreSQL guarda URI, hashes, tamanhos, estatísticas e metadados suficientes para rastreabilidade.

## Alembic

As migrações vivem em `migrations/`. A migração inicial `0001_create_eitri_metastore` cria o schema a partir da metadata SQLAlchemy. Quando `EITRI_DATABASE_URL` apontar para Tyr, aplique:

```bash
alembic upgrade head
```

Para auditar o contrato sem abrir conexão:

```bash
eitri metastore tables
eitri metastore ddl
```
