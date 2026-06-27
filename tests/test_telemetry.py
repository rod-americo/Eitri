import json

from eitri.telemetry import Event, JsonlEventSink, metric_event


def test_jsonl_event_sink_appends_structured_event(tmp_path) -> None:
    path = tmp_path / "events.jsonl"
    sink = JsonlEventSink(path)

    sink.emit(Event(event_type="run.started", run_id="run-1", payload={"host": "odin"}))
    sink.emit(metric_event("run-1", "auroc", 0.91, step=1))

    events = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    assert events[0]["event_type"] == "run.started"
    assert events[1]["payload"]["name"] == "auroc"
