# Guardrails

Nenhuma execução longa deve começar sem passar pelos guardrails. A arquitetura inicial avalia configuração válida, hash da configuração, hash do dataset, existência do dataset, integridade de arquivos, integridade de labels, split por paciente, ausência de patient leakage, distribuição mínima de classes, espaço em disco, memória disponível, GPU disponível ou simulada, compatibilidade host-experimento, commit Git, branch Git, árvore Git limpa para execução em Thor e bloqueio de treinamento pesado em Odin.

Alguns guardrails aceitam estado `warning` durante planejamento seco, especialmente quando dependem de dados reais ainda não conectados. Esses avisos existem para manter o contrato visível sem fingir validação que ainda não ocorreu.

Operações destrutivas exigem a frase literal `CONFIRMAR EXCLUSÃO`, listagem explícita de remoções e registro de tentativa. Sem isso, a operação deve ser abortada.
