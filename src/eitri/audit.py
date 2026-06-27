"""Auditoria de completude do bootstrap Eitri contra o objetivo declarado."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

AuditStatus = Literal["passed", "partial", "external_pending", "missing"]


@dataclass(frozen=True)
class AuditRequirement:
    key: str
    description: str
    evidence: tuple[str, ...]
    status: AuditStatus
    note: str = ""


@dataclass(frozen=True)
class AuditReport:
    requirements: tuple[AuditRequirement, ...]

    @property
    def complete(self) -> bool:
        return all(item.status == "passed" for item in self.requirements)

    @property
    def counts(self) -> dict[str, int]:
        return {
            status: sum(1 for item in self.requirements if item.status == status)
            for status in ("passed", "partial", "external_pending", "missing")
        }


def audit_bootstrap(root: str | Path = ".") -> AuditReport:
    base = Path(root)
    requirements = (
        _require(
            key="name_and_license",
            description="README explica Eitri e LICENSE.md contém Apache 2.0 + CC BY 4.0.",
            evidence=("README.md", "LICENSE.md"),
            root=base,
        ),
        _require(
            key="python_runtime",
            description="Runtime Python com requirements.txt, pyproject.toml e pytest.",
            evidence=("requirements.txt", "pyproject.toml", "tests"),
            root=base,
        ),
        _require(
            key="cli",
            description="CLI Typer com comandos principais e subcomandos operacionais.",
            evidence=("src/eitri/cli.py", "tests/test_cli.py"),
            root=base,
        ),
        _require(
            key="tui",
            description="TUI Textual como componente principal com atualização contínua mockada.",
            evidence=("src/eitri/tui.py", "docs/tui.md"),
            root=base,
        ),
        _require(
            key="control_plane",
            description="Control Plane FastAPI navegável com polling, SSE e WebSocket.",
            evidence=("src/eitri/web.py", "src/eitri/templates/control_plane.html"),
            root=base,
        ),
        _require(
            key="postgres_contract",
            description="PostgreSQL obrigatório com SQLAlchemy, Alembic e migração inicial.",
            evidence=(
                "src/eitri/db.py",
                "src/eitri/database.py",
                "migrations/versions/0001_create_eitri_metastore.py",
            ),
            root=base,
        ),
        _require(
            key="tyr_applied_migration",
            description="Migração aplicada no PostgreSQL real em Tyr.",
            evidence=("docs/evidence/tyr-metastore-bootstrap-2026-06-27.md",),
            root=base,
        ),
        _require(
            key="metrics_and_telemetry",
            description="Métricas e telemetria disponíveis para CLI, TUI, Web e registry.",
            evidence=(
                "src/eitri/metrics.py",
                "src/eitri/telemetry.py",
                "src/eitri/observability.py",
            ),
            root=base,
        ),
        _require(
            key="guardrails",
            description="Guardrails extensíveis com relatório detalhado e política destrutiva.",
            evidence=("src/eitri/guardrails.py", "docs/guardrails.md", "tests/test_guardrails.py"),
            root=base,
        ),
        _require(
            key="registry",
            description=(
                "Registry persistente preparado para datasets, runs, jobs, métricas e artefatos."
            ),
            evidence=("src/eitri/registry.py", "tests/test_registry.py"),
            root=base,
        ),
        _require(
            key="yaml_experiment",
            description="Experimento inicial definido por YAML e validado por Pydantic.",
            evidence=("configs/experiments/chest_xray_ct_24h.yaml", "src/eitri/schemas.py"),
            root=base,
        ),
        _require(
            key="plugins",
            description="Contratos formais de plugins e plugin inicial de Radiologia.",
            evidence=("src/eitri/plugins.py", "plugins/radiology_chest_xray_ct_24h/plugin.toml"),
            root=base,
        ),
        _require(
            key="workers",
            description="Contrato de worker, heartbeat e executor dry-run observável.",
            evidence=("src/eitri/workers.py", "tests/test_worker_executor.py", "docs/workers.md"),
            root=base,
        ),
        _require(
            key="thor_real_worker",
            description="Worker real executando em Thor após fluxo Git.",
            evidence=(
                "docs/operational-verification.md",
                "docs/evidence/thor-worker-smoke-2026-06-27.jsonl",
            ),
            root=base,
        ),
        _require(
            key="safe_sync",
            description="Fluxo Odin -> Git -> Thor e bloqueio de sincronização destrutiva.",
            evidence=("src/eitri/sync.py", "docs/workflow.md", "tests/test_sync_workers.py"),
            root=base,
        ),
        _require(
            key="docs",
            description=(
                "Documentação de arquitetura, banco, Tyr, Control Plane, TUI, "
                "plugins, métricas, guardrails e roadmap."
            ),
            evidence=(
                "docs/architecture.md",
                "docs/database.md",
                "docs/tyr-integration.md",
                "docs/control-plane.md",
                "docs/tui.md",
                "docs/plugins.md",
                "docs/metrics.md",
                "docs/guardrails.md",
                "docs/roadmap.md",
            ),
            root=base,
        ),
        _require(
            key="quality_gates",
            description="Testes e lint configurados para validar a fundação.",
            evidence=("tests", "pyproject.toml"),
            root=base,
        ),
    )
    return AuditReport(requirements=requirements)


def _require(
    key: str,
    description: str,
    evidence: tuple[str, ...],
    root: Path,
) -> AuditRequirement:
    missing = tuple(path for path in evidence if not (root / path).exists())
    if missing:
        return AuditRequirement(
            key=key,
            description=description,
            evidence=evidence,
            status="missing",
            note=f"Evidência ausente: {', '.join(missing)}",
        )
    return AuditRequirement(
        key=key,
        description=description,
        evidence=evidence,
        status="passed",
    )
