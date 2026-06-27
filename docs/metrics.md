# Métricas

Observabilidade é requisito funcional. As métricas devem estar simultaneamente disponíveis na CLI, TUI, Control Plane e PostgreSQL.

O conjunto inicial inclui CPU, RAM, GPU, VRAM, disco, rede, IOPS, leitura, escrita, temperatura quando disponível, throughput, ETA, velocidade, epoch, step, learning rate, loss, validation loss, tempo por batch, tempo por epoch, tempo restante, checkpoint atual e melhor checkpoint.

Enquanto Thor e os workers reais não estiverem integrados, métricas de GPU, VRAM e treinamento são simuladas por `src/eitri/mock.py` e `src/eitri/metrics.py`. Métricas do sistema local usam `psutil` quando disponíveis.

O serviço `src/eitri/observability.py` reúne métricas, eventos e artefatos em um frame compartilhado. O comando `eitri metrics export-mock --run-id 1 --dry-run` mostra o que seria enviado ao registry; com `--execute` e `EITRI_DATABASE_URL`, a amostra é persistida via PostgreSQL.
