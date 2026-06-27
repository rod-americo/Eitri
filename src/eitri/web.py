"""Control Plane Web em FastAPI com mock navegável e polling."""

from __future__ import annotations

import asyncio
import json
from dataclasses import asdict
from pathlib import Path

from fastapi import FastAPI, Request, WebSocket
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from eitri.config import load_config
from eitri.guardrails import RunIntent, evaluate_guardrails, guardrails_pass, hash_file
from eitri.mock import mock_control_plane_state
from eitri.telemetry import Event, JsonlEventSink

CONFIG_PATH = Path("configs/eitri.example.yaml")
TEMPLATE_DIR = Path(__file__).with_name("templates")

app = FastAPI(title="Eitri Control Plane", version="0.1.0")
templates = Jinja2Templates(directory=str(TEMPLATE_DIR))


class RunPlanRequest(BaseModel):
    name: str
    dataset_hash: str | None = None
    target_host: str = "odin"
    dry_run: bool = True
    heavy: bool = False


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "eitri-control-plane"}


@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request) -> HTMLResponse:
    config = load_config(CONFIG_PATH)
    return templates.TemplateResponse(
        request,
        "control_plane.html",
        {
            "request": request,
            "page": "dashboard",
            "title": "Dashboard",
            "config": config,
            "state": mock_control_plane_state(),
        },
    )


@app.get("/experiments", response_class=HTMLResponse)
def experiments_page(request: Request) -> HTMLResponse:
    config = load_config(CONFIG_PATH)
    return templates.TemplateResponse(
        request,
        "control_plane.html",
        {
            "request": request,
            "page": "experiments",
            "title": "Experimentos",
            "config": config,
            "state": mock_control_plane_state(),
        },
    )


@app.get("/jobs", response_class=HTMLResponse)
def jobs_page(request: Request) -> HTMLResponse:
    config = load_config(CONFIG_PATH)
    return templates.TemplateResponse(
        request,
        "control_plane.html",
        {
            "request": request,
            "page": "jobs",
            "title": "Jobs",
            "config": config,
            "state": mock_control_plane_state(),
        },
    )


@app.get("/metrics", response_class=HTMLResponse)
def metrics_page(request: Request) -> HTMLResponse:
    config = load_config(CONFIG_PATH)
    return templates.TemplateResponse(
        request,
        "control_plane.html",
        {
            "request": request,
            "page": "metrics",
            "title": "Métricas",
            "config": config,
            "state": mock_control_plane_state(),
        },
    )


@app.get("/config")
def config_summary() -> dict[str, object]:
    config = load_config(CONFIG_PATH)
    return {
        "project": config.project_name,
        "domain": config.domain,
        "owner_user": config.owner_user,
        "hosts": {name: asdict(host) for name, host in config.hosts.items()},
        "telemetry": {"event_log_path": str(config.telemetry.event_log_path)},
        "metastore": asdict(config.metastore),
        "control_plane": asdict(config.control_plane),
    }


@app.get("/api/mock/state")
def api_mock_state() -> dict[str, object]:
    return mock_control_plane_state()


@app.get("/api/events/stream")
async def api_events_stream() -> StreamingResponse:
    config = load_config(CONFIG_PATH)

    async def event_generator():
        while True:
            payload = json.dumps(mock_control_plane_state(), ensure_ascii=False)
            yield f"event: eitri.state\ndata: {payload}\n\n"
            await asyncio.sleep(config.control_plane.polling_seconds)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.websocket("/ws/mock")
async def websocket_mock(websocket: WebSocket) -> None:
    config = load_config(CONFIG_PATH)
    await websocket.accept()
    try:
        while True:
            await websocket.send_json(mock_control_plane_state())
            await asyncio.sleep(config.control_plane.polling_seconds)
    except Exception:
        await websocket.close()


@app.post("/guardrails/check")
def guardrails_check(request: RunPlanRequest) -> dict[str, object]:
    config = load_config(CONFIG_PATH)
    intent = RunIntent(
        name=request.name,
        dataset_hash=request.dataset_hash,
        config_path=CONFIG_PATH,
        config_hash=hash_file(CONFIG_PATH),
        target_host=request.target_host,
        dry_run=request.dry_run,
        heavy=request.heavy,
    )
    results = evaluate_guardrails(intent, config)
    return {
        "passed": guardrails_pass(results),
        "results": [asdict(result) for result in results],
    }


@app.post("/runs/plan")
def plan_run(request: RunPlanRequest) -> dict[str, object]:
    config = load_config(CONFIG_PATH)
    intent = RunIntent(
        name=request.name,
        dataset_hash=request.dataset_hash,
        config_path=CONFIG_PATH,
        config_hash=hash_file(CONFIG_PATH),
        target_host=request.target_host,
        dry_run=request.dry_run,
        heavy=request.heavy,
    )
    results = evaluate_guardrails(intent, config)
    passed = guardrails_pass(results)
    JsonlEventSink(config.telemetry.event_log_path).emit(
        Event(
            event_type="run.plan_requested",
            payload={
                "name": request.name,
                "target_host": request.target_host,
                "dry_run": request.dry_run,
                "heavy": request.heavy,
                "guardrails_passed": passed,
            },
        )
    )
    return {"accepted": passed, "guardrails": [asdict(result) for result in results]}


@app.get("/events/recent")
def recent_events(limit: int = 50) -> dict[str, object]:
    config = load_config(CONFIG_PATH)
    path = config.telemetry.event_log_path
    if not path.exists():
        return {"events": []}
    lines = path.read_text(encoding="utf-8").splitlines()
    return {"events": lines[-limit:]}
