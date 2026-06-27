from eitri.metrics import REQUIRED_METRICS
from eitri.mock import mock_control_plane_state


def test_mock_state_contains_operational_surfaces() -> None:
    state = mock_control_plane_state(seed=1)
    metric_names = {item["name"] for item in state["metrics"]}

    assert state["hosts"]
    assert state["experiments"]
    assert state["jobs"]
    assert state["events"]
    assert {"cpu_percent", "ram_percent", "loss", "validation_loss"}.issubset(metric_names)
    assert set(REQUIRED_METRICS) - metric_names == set()
