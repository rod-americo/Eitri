# Banco de Dados

O PostgreSQL em Tyr é obrigatório e atua como metastore central do Eitri. SQLite não é permitido como metastore porque o projeto precisa nascer com contratos compatíveis com operação real, múltiplos hosts, auditoria, concorrência e evolução por migrações.

## Entidades

O metastore declara entidades para `hosts`, `workers`, `models`, `tasks`, `datasets`, `dataset_versions`, `dataset_files`, `splits`, `experiments`, `runs`, `jobs`, `metrics`, `events`, `artifacts`, `configs` e `guardrail_reports`. Todas as entidades possuem UUID, versão, hash opcional, usuário responsável, timestamps e trilha de auditoria.

## Colunas de Auditoria Comuns

Todas as tabelas declaradas pelo Eitri, exceto `alembic_version`, compartilham as colunas `id`, `uuid`, `version`, `content_hash`, `owner_user`, `created_at`, `updated_at` e `audit_trail`. `id` é a chave primária operacional interna, `uuid` é o identificador estável para integrações e auditoria, `version` registra a versão do contrato que criou ou alterou o registro, `content_hash` guarda hash de configuração, dataset ou artefato quando aplicável, `owner_user` identifica o responsável, `created_at` e `updated_at` registram ciclo de vida e `audit_trail` armazena histórico estruturado em JSONB.

## Dicionário de Tabelas

### `hosts`

Catálogo dos hosts operacionais conhecidos pela plataforma. Colunas específicas: `name`, `role`, `ssh_alias`, `capabilities`. Relações: é referenciada por `workers.host_id`, `runs.target_host_id` e `jobs.host_id`. Uso inicial: registrar Odin, Thor e Tyr com seus papéis e capacidades.

### `workers`

Registra processos de execução vinculados a hosts, incluindo workers futuros de Thor. Colunas específicas: `host_id`, `name`, `status`, `queues`. Relações: `host_id` referencia `hosts.id`. Uso inicial: suportar heartbeat, filas e disponibilidade de execução pesada.

### `tasks`

Catálogo de tarefas suportadas por plugins. Colunas específicas: `name`, `plugin_name`, `output_mode`, `metadata_json`. Relações: é referenciada por `models.task_id` e `experiments.task_id`. Uso inicial: registrar `paired_imaging_structured_prediction` para radiografia de tórax pareada com TC.

### `models`

Catálogo de modelos planejados, treinados ou importados. Colunas específicas: `task_id`, `name`, `framework`, `artifact_uri`, `metadata_json`. Relações: `task_id` referencia `tasks.id`. O PostgreSQL guarda referência e metadados; checkpoints e pesos ficam no filesystem.

### `datasets`

Catálogo lógico de datasets. Colunas específicas: `name`, `description`, `domain`. Relações: é referenciada por `dataset_versions.dataset_id`. Uso inicial: registrar o dataset conceitual de radiografia de tórax em leito pareada com TC em até 24 horas.

### `dataset_versions`

Versões concretas e auditáveis de datasets. Colunas específicas: `dataset_id`, `uri`, `statistics`. Relações: `dataset_id` referencia `datasets.id`; é referenciada por `dataset_files.dataset_version_id`, `splits.dataset_version_id` e `experiments.dataset_version_id`. Guarda URI e estatísticas, nunca imagens ou DICOM.

### `dataset_files`

Manifesto opcional de arquivos pertencentes a uma versão de dataset. Colunas específicas: `dataset_version_id`, `uri`, `media_type`, `size_bytes`. Relações: `dataset_version_id` referencia `dataset_versions.id`. Uso esperado: registrar caminhos, tipos, tamanhos e hashes sem armazenar o payload no banco.

### `splits`

Definições auditáveis de partições de dataset. Colunas específicas: `dataset_version_id`, `name`, `strategy`, `patient_ids_hash`, `distribution`. Relações: `dataset_version_id` referencia `dataset_versions.id`. Uso esperado: preservar split por paciente, ausência de leakage e distribuição de classes.

### `experiments`

Catálogo de experimentos e objetivos de avaliação. Colunas específicas: `task_id`, `dataset_version_id`, `name`, `objective`, `metric_set`, `config_hash`. Relações: `task_id` referencia `tasks.id`; `dataset_version_id` referencia `dataset_versions.id`; é referenciada por `configs.experiment_id` e `runs.experiment_id`.

### `configs`

Registros de configuração ligados a experimentos. Colunas específicas: `experiment_id`, `name`, `uri`, `config_type`, `payload_ref`. Relações: `experiment_id` referencia `experiments.id`. Uso inicial: persistir referência e hash do YAML de experimento sem depender de memória local.

### `runs`

Execuções planejadas ou realizadas de experimentos. Colunas específicas: `experiment_id`, `target_host_id`, `status`, `dry_run`, `config_hash`, `dataset_hash`, `git_commit`, `git_branch`, `started_at`, `finished_at`, `metadata_json`. Relações: `experiment_id` referencia `experiments.id`; `target_host_id` referencia `hosts.id`; é referenciada por `jobs`, `metrics`, `events`, `artifacts` e `guardrail_reports`. Uso esperado: tornar cada execução reprodutível e vinculada a Git.

### `jobs`

Fila e progresso operacional de trabalhos. Colunas específicas: `run_id`, `host_id`, `status`, `queue`, `command_ref`, `progress`, `eta_seconds`. Relações: `run_id` referencia `runs.id`; `host_id` referencia `hosts.id`. Uso esperado: acompanhar treinamento, benchmark, inferência pesada e simulações de worker.

### `metrics`

Séries de métricas operacionais e de treinamento. Colunas específicas: `run_id`, `name`, `value_float`, `value_text`, `unit`, `step`, `epoch`, `recorded_at`. Relações: `run_id` referencia `runs.id`. Uso esperado: persistir CPU, RAM, GPU, VRAM, throughput, loss, validation loss, learning rate, tempo por batch e demais métricas auditáveis.

### `events`

Eventos estruturados observados durante a vida de runs e workers. Colunas específicas: `run_id`, `event_type`, `payload`, `observed_at`. Relações: `run_id` referencia `runs.id` quando o evento pertence a uma execução específica. Uso esperado: registrar mudanças de estado, alertas, checkpoints, falhas e eventos de observabilidade.

### `artifacts`

Referências a artefatos produzidos por runs. Colunas específicas: `run_id`, `name`, `uri`, `artifact_type`, `size_bytes`, `metadata_json`. Relações: `run_id` referencia `runs.id`. O banco armazena URI, hash, tamanho e metadados; o conteúdo pesado permanece fora do PostgreSQL.

### `guardrail_reports`

Relatórios de guardrails para runs planejadas ou executadas. Colunas específicas: `run_id`, `status`, `results`, `summary`. Relações: `run_id` referencia `runs.id` quando aplicável. Uso esperado: registrar validação de configuração, dataset, ambiente, Git, host e política destrutiva antes de executar treinamento.

### `alembic_version`

Tabela gerenciada pelo Alembic para registrar a revisão aplicada. Coluna principal: `version_num`. Em Tyr, após o bootstrap, o valor verificado é `0001_create_eitri_metastore`.

## O Que Entra no PostgreSQL

O banco armazena catálogo, versões, referências, estatísticas, métricas, eventos, jobs, modelos, configurações, guardrails, hashes, metadados e histórico. O objetivo é permitir auditoria objetiva sem depender da memória de quem executou o experimento.

## O Que Não Entra no PostgreSQL

Imagens, DICOM, PNG, checkpoints, artefatos pesados e logs extensos permanecem no filesystem. O PostgreSQL guarda URI, hashes, tamanhos, estatísticas e metadados suficientes para rastreabilidade.

## Alembic

As migrações vivem em `migrations/`. A migração inicial `0001_create_eitri_metastore` cria o schema a partir da metadata SQLAlchemy. Quando `EITRI_DATABASE_URL` apontar para Tyr, aplique:

```bash
alembic upgrade head
```

Para auditar o contrato sem abrir conexão:

```bash
eitri metastore tables
eitri metastore ddl
```
