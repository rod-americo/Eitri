# Control Plane

O Control Plane existe desde o bootstrap e usa FastAPI. Ele escuta em `127.0.0.1:8081` por padrão, evitando conflito com serviços locais em `8080`, e não deve abrir automaticamente para toda a rede. O comando `eitri web` respeita a configuração `control_plane.allow_public_bind` antes de aceitar outro bind.

A primeira implementação usa polling a cada 2 segundos por meio de `/api/mock/state`. A mesma fonte simulada também está disponível em `/api/events/stream` via Server-Sent Events e em `/ws/mock` via WebSocket, deixando a fronteira de migração pronta quando os workers reais passarem a emitir eventos.

As páginas navegáveis atuais são dashboard, experimentos, jobs e métricas. Elas exibem hosts, fila, ETA, progresso, loss, validation loss, CPU, RAM, GPU simulada, VRAM simulada, temperatura simulada, eventos, alertas, checkpoints e artefatos.
