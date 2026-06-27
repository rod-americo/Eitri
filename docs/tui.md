# TUI

A TUI é componente principal, não uma ferramenta auxiliar. Ela é inspirada em btop, lazygit e k9s: informação densa, atualização contínua, navegação por teclado e foco em estado operacional.

A implementação inicial usa Textual e atualiza dados simulados a cada 2 segundos. Ela mostra hosts, jobs, métricas, eventos, uso de CPU, RAM, GPU simulada, VRAM simulada, throughput, ETA, progresso, epoch, step, loss, validation loss, learning rate, checkpoints, alertas e logs recentes em formato de tabelas operacionais.

Com o registry persistente conectado ao Tyr, a mesma superfície deve passar a consumir dados reais sem mudar o contrato visual principal.
