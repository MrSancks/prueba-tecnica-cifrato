from app.presentation.routers.health import read_health


def test_health_endpoint_returns_ok_status() -> None:
    assert read_health() == {"status": "ok"}
