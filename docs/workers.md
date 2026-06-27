# Workers

Workers são o ponto de execução futura em Thor e o ponto de telemetria contínua para jobs longos. A fundação atual define `WorkerHeartbeat`, coleta local por `psutil`, contrato esperado para Thor e comandos de inspeção via `eitri hosts heartbeat` e `eitri sync thor-contract`.

O worker real de Thor deverá consumir código exclusivamente após `git pull`, publicar heartbeat, registrar métricas operacionais, atualizar progresso de jobs, reportar checkpoints e persistir eventos no metastore. O contrato já exige telemetria de CPU, RAM, GPU, VRAM, temperatura, progresso, loss, validation loss e checkpoint.

O executor leve atual não treina modelos. Ele simula um ciclo operacional com progresso, loss, validation loss, epochs, steps, checkpoint e eventos JSONL, permitindo testar observabilidade e registry antes do treinamento real:

```bash
eitri jobs simulate --job-id job-dry-run-001 --run-id run-dry-run-001 --event-log logs/worker-events.jsonl
```

Com `--execute`, `--db-run-id` e `EITRI_DATABASE_URL`, o relatório do worker pode persistir métricas, eventos e artefato de checkpoint no PostgreSQL via `PersistentRegistry`.
