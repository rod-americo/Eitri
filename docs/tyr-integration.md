# Integração com Tyr

Tyr é o host PostgreSQL em Docker e deve ser tratado como metastore central. A URL de conexão deve ser fornecida por `EITRI_DATABASE_URL`, nunca hardcoded em código ou documentação operacional sensível.

O Eitri já declara `src/eitri/database.py` para criação de engine PostgreSQL e rejeição explícita de SQLite. O registry persistente em `src/eitri/registry.py` recebe uma sessão SQLAlchemy e grava entidades auditáveis, preparando a plataforma para trocar dados simulados por dados reais do metastore.

Use `.env.example` como forma do valor esperado e prefira o driver `postgresql+psycopg://`. URLs `postgresql://` são normalizadas internamente para `postgresql+psycopg://`.

Enquanto a integração real com Tyr não estiver conectada neste repositório, as superfícies de UI usam dados simulados para permitir desenvolvimento completo da experiência operacional.

O comando `eitri metastore seed-initial --dry-run` mostra as entidades iniciais que seriam persistidas. Com `--execute` e `EITRI_DATABASE_URL` definido, o seed grava hosts, task inicial, dataset, experimento, modelo e config no PostgreSQL.

As credenciais do container PostgreSQL não devem ser descobertas por inspeção de variáveis remotas. Use uma URL explícita em `EITRI_DATABASE_URL` e valide com `eitri metastore check-url`.
