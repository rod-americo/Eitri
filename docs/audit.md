# Auditoria

O comando `eitri audit` compara a fundação atual com os requisitos do bootstrap e separa evidências locais de pendências externas. Ele existe para evitar que o estado do projeto dependa da memória de quem está conduzindo a implementação.

Uso:

```bash
eitri audit
eitri audit --strict
```

`--strict` retorna código de erro enquanto existir qualquer requisito não comprovado. Pendências externas esperadas nesta fase incluem aplicar a migração no PostgreSQL real de Tyr e iniciar um worker real em Thor após o fluxo Git.

Os status possíveis são `passed`, `partial`, `external_pending` e `missing`.
