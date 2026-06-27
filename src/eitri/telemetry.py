"""Append-only telemetry primitives for observable runs."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4


@dataclass(frozen=True)
class Event:
    event_type: str
    run_id: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)
    event_id: str = field(default_factory=lambda: str(uuid4()))
    observed_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


class JsonlEventSink:
    """Persist structured events as JSON Lines."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def emit(self, event: Event) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(asdict(event), sort_keys=True) + "\n")


def metric_event(
    run_id: str,
    name: str,
    value: int | float | str,
    step: int | None = None,
    context: dict[str, Any] | None = None,
) -> Event:
    payload: dict[str, Any] = {"name": name, "value": value}
    if step is not None:
        payload["step"] = step
    if context:
        payload["context"] = context
    return Event(event_type="metric.recorded", run_id=run_id, payload=payload)
