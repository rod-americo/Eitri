# Mockups de Interface

Estes mockups descrevem as superfícies iniciais do Control Plane e da TUI sem fixar detalhes finais de frontend.

## Dashboard do Control Plane

```text
+------------------------------------------------------------------+
| Eitri Control Plane                           Odin | Tyr | Thor   |
+------------------------------------------------------------------+
| Runs: planejadas 4 | rodando 1 | bloqueadas 2 | concluídas 18     |
| Guardrails: 87% ok | última falha: dataset_hash                   |
+------------------------------------------------------------------+
| Runs Ativas                                                       |
| run_id   experimento       host   status    última_métrica        |
| 8f12     cxr-baseline      thor   running   auroc=0.91            |
| a443     ct-triage-dryrun  odin   planned   pending               |
+------------------------------------------------------------------+
| Eventos                                                          |
| 12:01 run.started 8f12                                            |
| 12:02 metric.recorded auroc=0.91                                  |
| 12:03 guardrail.failed dataset_hash                               |
+------------------------------------------------------------------+
```

## Detalhe do Experimento

```text
+------------------------------------------------------------------+
| Experimento: cxr-baseline                                         |
+------------------------------------------------------------------+
| Objetivo: classificador basal para radiografia de tórax           |
| Dataset: cxr:v1 sha256:...                                        |
| Config: sha256:...                                                |
| Commit: abc1234                                                   |
+------------------------------------------------------------------+
| Métricas                                                          |
| auroc     0.91                                                    |
| f1        0.84                                                    |
| recall    0.88                                                    |
+------------------------------------------------------------------+
| Artefatos                                                         |
| checkpoint latest -> checkpoints/cxr-baseline/latest.ckpt         |
| relatório -> artifacts/cxr-baseline/report.html                   |
+------------------------------------------------------------------+
```

## Primeira Tela da TUI

```text
+------------------------------------------------------------------+
| Eitri | domain=radiology | dry_run=True                           |
+------------------------------------------------------------------+
| Host   Papel                SSH     Responsabilidades             |
| odin   desenvolvimento      -       código, testes, dry-runs, tui |
| thor   execução_gpu         thor    treinamento, benchmarks       |
| tyr    metastore            tyr     PostgreSQL                    |
+------------------------------------------------------------------+
| q sair                                                           |
+------------------------------------------------------------------+
```
