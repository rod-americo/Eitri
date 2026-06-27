# Verificação Operacional

Foram feitas checagens não destrutivas em Tyr e Thor para validar as premissas operacionais sem ler segredos, criar bancos, alterar containers ou aplicar migrações.

## Tyr

`ssh tyr` respondeu como host `tyr`, macOS/Darwin, com Docker disponível. O Docker mostrou containers PostgreSQL em execução, incluindo `ginnungagap-postgres` com imagem `postgres:16` e porta `5432` publicada, além de outros serviços de pesquisa. Credenciais e variáveis `POSTGRES*` não foram lidas por segurança.

Em 2026-06-27, o banco `eitri` e a role dedicada `eitri` foram criados no container `ginnungagap-postgres`, a migração `0001_create_eitri_metastore` foi aplicada e o seed inicial foi persistido. A evidência operacional sem segredos está em `docs/evidence/tyr-metastore-bootstrap-2026-06-27.md`.

Para validar ou reaplicar em ambiente novo, defina explicitamente `EITRI_DATABASE_URL` com uma URL PostgreSQL válida para o metastore Eitri e execute:

```bash
eitri metastore check-url
alembic upgrade head
eitri metastore seed-initial --execute
```

## Thor

`ssh thor` respondeu como host Linux e `nvidia-smi` detectou uma NVIDIA GeForce RTX 3090 com 24576 MiB de VRAM. O repositório `/home/rodrigo/Eitri` existe e aponta para `git@github.com:rod-americo/Eitri.git`.

Em 2026-06-27, o fluxo Odin -> Git -> Thor foi executado pela branch `codex/bootstrap-eitri-foundation`: commit `ff37d3b`, push para `origin`, `git fetch`, checkout e `git pull --ff-only` em Thor. Em seguida, foi criado o `.venv` remoto, instaladas as dependências por `requirements.txt`, instalado o pacote local com `pip install -e .`, executados `ruff` e `pytest` no Thor, e validado um worker mínimo com `eitri jobs simulate --worker-name thor-gpu --steps 3 --event-log /tmp/eitri-thor-worker-events.jsonl --execute`. A evidência reduzida e sem PHI/PII está em `docs/evidence/thor-worker-smoke-2026-06-27.jsonl`.

## Probes Seguros

Os comandos abaixo mostram ou executam probes que evitam leitura de segredos e não alteram estado remoto:

```bash
eitri ops tyr-probe
eitri ops thor-probe
eitri ops tyr-probe --execute
eitri ops thor-probe --execute
```
