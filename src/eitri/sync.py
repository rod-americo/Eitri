"""Planejamento de sincronização segura Odin -> Git -> Thor."""

from __future__ import annotations

from dataclasses import dataclass

from eitri.config import EitriConfig
from eitri.guardrails import GuardrailResult, validate_destructive_confirmation


@dataclass(frozen=True)
class SyncStep:
    order: int
    description: str
    command: str


@dataclass(frozen=True)
class SyncPlan:
    target_host: str
    destructive: bool
    steps: tuple[SyncStep, ...]


def git_sync_plan(target_host: str = "thor", destructive: bool = False) -> SyncPlan:
    return SyncPlan(
        target_host=target_host,
        destructive=destructive,
        steps=(
            SyncStep(1, "Inspecionar árvore local", "git status"),
            SyncStep(2, "Criar commit auditável", "git commit"),
            SyncStep(3, "Enviar código para o remoto", "git push"),
            SyncStep(4, "Atualizar código em Thor", f"ssh {target_host} 'git pull'"),
        ),
    )


def validate_destructive_sync(
    confirmation: str,
    config: EitriConfig,
    listed_paths: list[str],
) -> GuardrailResult:
    if not listed_paths:
        return GuardrailResult(
            "destructive_sync_listing",
            False,
            "Operações destrutivas devem listar exatamente o que será removido.",
        )
    return validate_destructive_confirmation(confirmation, config)
