# Módulos

Eitri separa regras de domínio das superfícies de interação. A CLI, TUI e Control Plane devem consumir serviços de domínio em vez de manter listas e regras hardcoded.

Os módulos principais são `datasets`, `experiments`, `models`, `jobs`, `metrics`, `observability`, `guardrails`, `registry`, `workers`, `sync`, `plugins`, `database`, `web` e `tui`. Essa divisão permite que o mock atual seja substituído por dados persistidos em Tyr sem reescrever comandos ou telas.

`src/eitri/observability.py` centraliza o frame de métricas, eventos e artefatos. A mesma estrutura pode ser exibida na CLI, TUI e Web ou persistida no registry PostgreSQL por `PersistentRegistry`.
