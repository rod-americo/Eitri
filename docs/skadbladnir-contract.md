# Contrato Skadbladnir

Este repositório segue um contrato de bootstrap inspirado no protocolo Skadbladnir.

## Fronteira

Eitri é uma plataforma para treinamento, fine-tuning, avaliação, benchmark, gerenciamento de experimentos e registry de modelos. Ele não representa um modelo específico e não é proprietário de dados clínicos brutos.

## Runtime

O runtime declarado usa Python 3.11 ou superior, dependências em `requirements.txt`, ambiente local opcional em `.venv` fora do Git e PostgreSQL como metastore autoritativo.

## Contratos

Todo contrato de experimento deve declarar objetivo, referência do dataset, hash do dataset, hash da configuração, conjunto de métricas, host de destino, status de dry-run, commit Git e sink de telemetria.

## Operação

Eitri começa em Odin. Execução com GPU acontece em Thor depois que o código chega lá por Git. Metadados persistem em Tyr. Arquivos pesados permanecem no filesystem e são referenciados por URI e hash.

## Auditabilidade

A plataforma prioriza evidência registrada em vez de memória operacional. Guardrails, eventos, métricas, hashes e mudanças de status são registros de primeira classe.
