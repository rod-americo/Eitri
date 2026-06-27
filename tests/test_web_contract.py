from eitri.web import app


def test_control_plane_exposes_polling_sse_and_websocket_routes() -> None:
    paths = {route.path for route in app.routes}

    assert "/api/mock/state" in paths
    assert "/api/events/stream" in paths
    assert "/ws/mock" in paths
