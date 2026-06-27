# Operação

## Padrão Não Destrutivo

Eitri começa em modo dry-run. Execução remota e operações destrutivas precisam passar por guardrails antes de qualquer ação real.

## Política para Operações Destrutivas

Nenhuma sincronização pode apagar arquivos automaticamente. Qualquer operação destrutiva deve listar exatamente o que será removido, registrar a tentativa em log, pedir confirmação explícita e exigir que o usuário digite literalmente:

```text
CONFIRMAR EXCLUSÃO
```

Sem essa frase, a operação deve ser abortada.

## Fluxo por Git

O fluxo oficial é:

```text
Odin -> Git -> Thor
```

A sequência esperada para mudanças de código é commitar em Odin, fazer push e então fazer pull em Thor. Datasets, ambientes virtuais, checkpoints, artefatos gerados, caches, logs grandes e segredos locais nunca pertencem ao Git.

## Observabilidade

Execuções longas precisam emitir eventos e métricas estruturadas. No mínimo, uma run deve registrar identidade da execução, versão e hash do dataset, hash da configuração, commit Git, host de destino, resultados dos guardrails, valores de métricas, transições de status e referências com hashes dos artefatos.
