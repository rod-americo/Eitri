# Arquitetura

Eitri separa plano de controle, plano de metadados e plano de artefatos pesados para manter rastreabilidade sem transformar o banco de dados em armazenamento bruto de imagens ou checkpoints.

## Superfícies de Controle

- CLI: automação, dry-runs, checagem de guardrails e planejamento de experimentos.
- TUI: visão operacional local em Odin para status, hosts e inspeção inicial de execuções.
- Control Plane Web: API HTTP para planejamento de runs, checagem de guardrails, consulta de eventos e evolução futura para WebSocket e Server-Sent Events.

## Plano de Metadados

Tyr hospeda o PostgreSQL e atua como metastore central. Ele armazena referências, hashes, estatísticas, métricas, eventos, jobs, metadados de modelos, hashes de configuração e registros de auditoria.

O metastore não deve armazenar payloads pesados como DICOM, imagens, PNGs exportados, checkpoints, artefatos completos ou logs extensos.

## Plano de Artefatos

Arquivos pesados permanecem no filesystem: datasets em `data/datasets`, artefatos gerados em `artifacts`, checkpoints em `checkpoints`, logs de execução em `logs` e caches em `cache`. Esses caminhos são ignorados pelo Git de forma intencional.

## Fluxo de Execução

```text
Odin: editar, testar, executar dry-run, commitar
Git: transporte oficial e fonte de verdade do código
Thor: fazer pull, executar jobs com GPU, persistir métricas e eventos
Tyr: manter metadados centrais e registry
```

Sincronização manual de código fica fora do modelo operacional.

## Pontos de Extensão

Plugins serão usados para adaptadores de domínio, leitores de dataset, trainers, avaliadores, suítes de benchmark, exportadores de artefatos e sinks de telemetria. O primeiro contrato de plugin vive em `eitri.plugins`.

## Modularidade

A CLI, a TUI e o Control Plane são superfícies, não donos das regras de domínio. Listagens de datasets, experimentos, modelos, jobs e frames de observabilidade vivem em módulos próprios em `src/eitri/`, o que mantém baixo acoplamento e facilita trocar mock por dados reais do PostgreSQL.
