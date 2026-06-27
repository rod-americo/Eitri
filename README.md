# Eitri

Eitri é a fundação de uma plataforma de experimentos de Machine Learning reprodutível, observável e extensível. O foco inicial é visão computacional médica em Radiologia, mas a arquitetura é agnóstica ao domínio desde o início.

O nome é intencional. Na mitologia nórdica, Eitri é o mestre ferreiro responsável por forjar grandes artefatos dos deuses, incluindo Mjölnir, Draupnir e Gullinbursti. Neste ecossistema, Nidavellir representa a infraestrutura geral, Skadbladnir define protocolos operacionais para repositórios com fronteiras explícitas e Eitri é a forja onde modelos serão treinados, comparados, avaliados e evoluídos.

## Escopo

Esta primeira fundação não implementa treinamento profundo real. Ela estabelece os contratos e esqueletos executáveis necessários antes do início dos treinamentos: CLI com dry-run e guardrails, TUI local para Odin, Control Plane Web em FastAPI, modelos SQLAlchemy orientados ao metastore PostgreSQL, configuração YAML, telemetria estruturada, registry persistente preparado para Tyr, contratos de plugins, documentação operacional e mock navegável de interface.

## Princípios

- Todo experimento deve ser reprodutível.
- Toda decisão importante deve ser registrada.
- Toda métrica deve ser persistida.
- Nenhum resultado deve depender da memória do pesquisador.
- Nenhum treinamento deve iniciar sem passar pelos guardrails.
- Toda execução longa deve ser completamente observável.
- Toda comparação entre modelos deve ser objetiva e auditável.
- Rastreabilidade é mais importante do que conveniência.
- Modularidade é obrigatória.
- Simplicidade de uso é um objetivo permanente.

Observabilidade é requisito funcional, não recurso opcional.

## Hosts

Eitri assume três hosts. Odin é o ambiente local para desenvolvimento, testes, dry-runs, TUI, Control Plane, experimentos leves e interface. Thor é o servidor com GPU para treinamento, fine-tuning, benchmarks, inferência pesada, checkpoints e jobs demorados. Tyr é o host PostgreSQL em Docker e atua como metastore central, armazenando metadados, referências, hashes, métricas, eventos, jobs, modelos, configurações e histórico.

O fluxo oficial de código é:

```text
Odin -> Git -> Thor
```

Código trafega por commit, push e pull. Datasets, runtimes, ambientes virtuais, checkpoints, artefatos, caches e logs grandes permanecem fora do Git.

## Início Rápido

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
pytest
```

Executar a CLI:

```bash
eitri status --config configs/eitri.example.yaml
eitri guardrails check --config configs/eitri.example.yaml
eitri experiments plan --config configs/eitri.example.yaml --name baseline-radiograph --dry-run
```

Executar o Control Plane:

```bash
eitri web --config configs/eitri.example.yaml
```

Por padrão, o serviço escuta em `127.0.0.1:8081` para evitar conflito com serviços locais que usem `8080`.

Executar a TUI:

```bash
eitri tui --config configs/eitri.example.yaml
```

Inspecionar o contrato PostgreSQL do metastore:

```bash
eitri metastore tables
eitri metastore ddl
eitri metastore seed-initial --dry-run
EITRI_DATABASE_URL=postgresql+psycopg://eitri:senha@tyr:5432/eitri eitri metastore check-url
```

Inspecionar workers e sincronização:

```bash
eitri hosts heartbeat
eitri sync plan --target-host thor
eitri sync thor-contract
```

Executar probes operacionais seguros:

```bash
eitri ops tyr-probe
eitri ops thor-probe
```

Simular ciclo de worker sem treinamento profundo:

```bash
eitri jobs simulate --job-id job-dry-run-001 --run-id run-dry-run-001 --event-log logs/worker-events.jsonl
```

Validar plugins:

```bash
eitri plugins list
eitri plugins validate
```

Auditar a fundação contra o objetivo:

```bash
eitri audit
eitri audit --strict
```

## Mapa do Repositório

- `src/eitri/`: pacote principal da plataforma.
- `src/eitri/workers.py`: contrato de heartbeat e telemetria de workers.
- `src/eitri/sync.py`: plano seguro Odin → Git → Thor e política destrutiva.
- `src/eitri/bootstrap.py`: seed inicial persistente do metastore.
- `src/eitri/observability.py`: frame compartilhado de métricas, eventos e artefatos.
- `plugins/`: manifestos de plugins de referência.
- `configs/`: configuração de runtime de exemplo.
- `docs/`: arquitetura, operação, contratos e mockups.
- `docs/database.md`: entidades do metastore e política PostgreSQL.
- `docs/control-plane.md`: Control Plane Web, polling e localhost por padrão.
- `docs/tui.md`: TUI como componente principal.
- `docs/metrics.md`: métricas operacionais e de treinamento.
- `docs/guardrails.md`: guardrails iniciais e política de bloqueio.
- `docs/modules.md`: separação dos módulos de domínio e superfícies.
- `docs/audit.md`: auditoria dos requisitos do bootstrap e pendências externas.
- `docs/operational-verification.md`: evidência operacional não destrutiva de Tyr e Thor.
- `tests/`: testes focados nos contratos centrais de reprodutibilidade e segurança.
- `migrations/`: base do Alembic para evolução do metastore.
- `.env.example`: exemplo de variável para conexão com Tyr.

## Licenciamento

Veja `LICENSE.md`.

- Código: Apache 2.0.
- Documentação: CC BY 4.0.
