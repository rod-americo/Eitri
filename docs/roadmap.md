# Roadmap

## Fase 1: Fundação

Criar pacote Python, configuração YAML, CLI, TUI, Control Plane, entidades SQLAlchemy, Alembic, guardrails, telemetria, registry persistente preparado, mock navegável, documentação e testes.

## Fase 2: Tyr Real

Conectar `EITRI_DATABASE_URL`, aplicar a migração Alembic inicial em Tyr, persistir hosts, datasets, experimentos, runs, jobs, métricas, eventos, artefatos e relatórios de guardrails.

O comando `eitri audit --strict` deve continuar falhando até essa prova operacional existir.

## Fase 3: Thor Real

Criar worker em Thor, fila de jobs, heartbeat, coleta de GPU/VRAM/temperatura, persistência contínua de métricas e execução de dry-runs remotos por Git.

O contrato inicial de worker já existe em `src/eitri/workers.py` e deve ser usado como base para o serviço real em Thor.

## Fase 4: Plugins de Radiologia

Implementar plugin do dataset inicial de radiografia de tórax pareada com tomografia em até 24 horas, validação de labels estruturados, split por paciente e avaliação sem geração de texto.

## Fase 5: Treinamento Real

Introduzir trainers reais, benchmarks, checkpoints, avaliação objetiva, comparação auditável de modelos e promoção de artefatos para registry de modelos.
