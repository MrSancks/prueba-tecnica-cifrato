"""Basic integration test for the health endpoint."""

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_endpoint_returns_ok_status() -> None:
    """The health endpoint should respond with a successful status payload."""

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
