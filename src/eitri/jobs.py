"""Serviços de fila e jobs para mock operacional e futuro worker real."""

from __future__ import annotations

from dataclasses import dataclass

from eitri.mock import mock_control_plane_state


@dataclass(frozen=True)
class JobCatalogItem:
    job_id: str
    host: str
    queue: str
    status: str
    progress: int


def list_mock_jobs() -> list[JobCatalogItem]:
    state = mock_control_plane_state()
    return [
        JobCatalogItem(
            job_id=item["id"],
            host=item["host"],
            queue=item["queue"],
            status=item["status"],
            progress=item["progress"],
        )
        for item in state["jobs"]
    ]
