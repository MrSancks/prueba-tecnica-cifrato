"""Integration tests for authentication endpoints."""

from fastapi.testclient import TestClient

from app.main import create_app


def get_client() -> TestClient:
    return TestClient(create_app())


def test_register_and_login_flow() -> None:
    client = get_client()

    response = client.post(
        "/auth/register",
        json={"email": "user@example.com", "password": "StrongPass123"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "user@example.com"
    assert "id" in data

    login_response = client.post(
        "/auth/login",
        json={"email": "user@example.com", "password": "StrongPass123"},
    )
    assert login_response.status_code == 200
    login_data = login_response.json()
    assert "access_token" in login_data
    token = login_data["access_token"]

    me_response = client.get(
        "/auth/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert me_response.status_code == 200
    me_data = me_response.json()
    assert me_data["email"] == "user@example.com"


def test_register_duplicate_email_returns_400() -> None:
    client = get_client()

    payload = {"email": "duplicate@example.com", "password": "Password1"}
    first = client.post("/auth/register", json=payload)
    assert first.status_code == 201

    second = client.post("/auth/register", json=payload)
    assert second.status_code == 400
    assert second.json()["detail"] == "Email already registered"


def test_login_with_invalid_credentials_returns_401() -> None:
    client = get_client()

    client.post("/auth/register", json={"email": "valid@example.com", "password": "Secret1"})

    response = client.post(
        "/auth/login",
        json={"email": "valid@example.com", "password": "Wrong"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"

    missing_user_response = client.post(
        "/auth/login",
        json={"email": "missing@example.com", "password": "Secret1"},
    )
    assert missing_user_response.status_code == 401
    assert missing_user_response.json()["detail"] == "Invalid email or password"
