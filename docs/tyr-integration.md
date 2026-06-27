# Integração com Tyr

Tyr é o host PostgreSQL em Docker e deve ser tratado como metastore central. A URL de conexão deve ser fornecida por `EITRI_DATABASE_URL`, nunca hardcoded em código ou documentação operacional sensível.

O Eitri já declara `src/eitri/database.py` para criação de engine PostgreSQL e rejeição explícita de SQLite. O registry persistente em `src/eitri/registry.py` recebe uma sessão SQLAlchemy e grava entidades auditáveis, preparando a plataforma para trocar dados simulados por dados reais do metastore.

Use `.env.example` como forma do valor esperado e prefira o driver `postgresql+psycopg://`. URLs `postgresql://` são normalizadas internamente para `postgresql+psycopg://`.

O bootstrap real do metastore foi aplicado em Tyr em 2026-06-27 no container `ginnungagap-postgres`, usando banco `eitri` e role dedicada `eitri`. A evidência operacional sem credenciais está em `docs/evidence/tyr-metastore-bootstrap-2026-06-27.md`.

O comando `eitri metastore seed-initial --dry-run` mostra as entidades iniciais que seriam persistidas. Com `--execute` e `EITRI_DATABASE_URL` definido, o seed grava hosts, task inicial, dataset, experimento, modelo e config no PostgreSQL.

As credenciais do container PostgreSQL não devem ser persistidas como credenciais de aplicação. O Eitri usa uma role dedicada no `.env` local e no `.env` do Thor; novas rotações devem atualizar ambos os arquivos fora do Git e validar com `eitri metastore check-url`.
