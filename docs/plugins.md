# Plugins

Eitri deve crescer por plugins. Novas tarefas não devem exigir reescrita da infraestrutura de CLI, TUI, Control Plane, registry, guardrails e telemetria.

Os tipos iniciais de plugin são Dataset, Model, Task, Metrics, Evaluation e Exporter. Um plugin deve declarar nome, versão, descrição e contratos suficientes para que a plataforma descubra capacidades, valide configuração, planeje execução, persista metadados e exponha métricas nas superfícies operacionais. O módulo `src/eitri/plugins.py` define protocolos formais para cada tipo e valida se um plugin cobre todas as capacidades obrigatórias.

A descoberta suporta plugins embutidos, entrypoints Python no grupo `eitri.plugins` e manifestos `plugin.toml` em diretórios configurados. O manifesto de referência vive em `plugins/radiology_chest_xray_ct_24h/plugin.toml` e cobre o dataset inicial de radiografia de tórax pareada com tomografia em até 24 horas, saída estruturada e sem geração de texto.

Validação:

```bash
eitri plugins list
eitri plugins validate
eitri validate --experiment configs/experiments/chest_xray_ct_24h.yaml
```

Um manifesto deve declarar capacidades no formato:

```toml
[[capabilities]]
kind = "dataset"
name = "bedside-chest-xray-ct-24h"
contract = "paired_imaging_dataset"
description = "Pareamento CR -> CT em janela de 24 horas com split por paciente."
```
