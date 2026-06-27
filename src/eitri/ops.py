"""Probes operacionais seguros para Odin, Tyr e Thor."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass


@dataclass(frozen=True)
class ProbeCommand:
    name: str
    command: tuple[str, ...]
    description: str


@dataclass(frozen=True)
class ProbeResult:
    name: str
    command: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str

    @property
    def passed(self) -> bool:
        return self.returncode == 0


def tyr_probe_commands() -> tuple[ProbeCommand, ...]:
    return (
        ProbeCommand(
            name="tyr-host",
            command=(
                "ssh",
                "-o",
                "BatchMode=yes",
                "-o",
                "ConnectTimeout=8",
                "tyr",
                "hostname; uname -a",
            ),
            description="Identifica host e kernel de Tyr.",
        ),
        ProbeCommand(
            name="tyr-postgres-containers",
            command=(
                "ssh",
                "-o",
                "BatchMode=yes",
                "-o",
                "ConnectTimeout=8",
                "tyr",
                "docker ps --format "
                "'{{.Names}} {{.Image}} {{.Status}} {{.Ports}}' | grep -i postgres",
            ),
            description="Lista containers PostgreSQL visíveis em Tyr sem acessar credenciais.",
        ),
    )


def thor_probe_commands() -> tuple[ProbeCommand, ...]:
    return (
        ProbeCommand(
            name="thor-host",
            command=(
                "ssh",
                "-o",
                "BatchMode=yes",
                "-o",
                "ConnectTimeout=8",
                "thor",
                "hostname; uname -a",
            ),
            description="Identifica host e kernel de Thor.",
        ),
        ProbeCommand(
            name="thor-gpu",
            command=(
                "ssh",
                "-o",
                "BatchMode=yes",
                "-o",
                "ConnectTimeout=8",
                "thor",
                "nvidia-smi --query-gpu=name,memory.total,memory.used,"
                "utilization.gpu,temperature.gpu --format=csv,noheader",
            ),
            description="Coleta GPU, VRAM, utilização e temperatura de Thor.",
        ),
        ProbeCommand(
            name="thor-repo",
            command=(
                "ssh",
                "-o",
                "BatchMode=yes",
                "-o",
                "ConnectTimeout=8",
                "thor",
                "if [ -d ~/Eitri/.git ]; then git -C ~/Eitri status --short --branch; fi",
            ),
            description="Verifica se o repositório Eitri existe em Thor e está ligado ao Git.",
        ),
    )


def run_probe(command: ProbeCommand) -> ProbeResult:
    completed = subprocess.run(command.command, check=False, capture_output=True, text=True)
    return ProbeResult(
        name=command.name,
        command=command.command,
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )
