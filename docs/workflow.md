# Workflow Odin → Git → Thor

O fluxo oficial de desenvolvimento é `Odin -> Git -> Thor`. Odin é o local de edição, testes, dry-runs, TUI, Control Plane e experimentos leves. Thor recebe código exclusivamente por Git e executa treinamento, fine-tuning, benchmark, inferência pesada, checkpoints e jobs longos.

Código não deve ser sincronizado manualmente. A sequência esperada é commitar em Odin, fazer push, acessar Thor e fazer pull. Datasets, ambientes virtuais, runtime, checkpoints, artefatos, caches e logs grandes permanecem fora do Git.

Qualquer tentativa de sincronização destrutiva deve ser bloqueada por padrão. Se uma operação destrutiva existir no futuro, ela precisará listar exatamente o que será removido, registrar a tentativa, pedir confirmação explícita e exigir a frase literal `CONFIRMAR EXCLUSÃO`.

Os comandos `eitri sync plan`, `eitri sync destructive-check` e `eitri sync thor-contract` formalizam esse contrato. Eles não sincronizam arquivos diretamente; apenas tornam o fluxo oficial e as barreiras de segurança verificáveis.
