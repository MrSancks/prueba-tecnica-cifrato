import asyncio

import pytest
from fastapi import HTTPException

from app.config import dependencies
from app.presentation.routers import auth
from app.presentation.schemas.auth import LoginRequest, RegisterRequest


def setup_function() -> None:
    dependencies.get_user_repository.cache_clear()
    dependencies.get_password_hasher.cache_clear()
    dependencies.get_token_service.cache_clear()


def test_register_and_login_flow() -> None:
    register_use_case = dependencies.get_register_user_use_case()
    authenticate_use_case = dependencies.get_authenticate_user_use_case()

    payload = RegisterRequest(email="user@example.com", password="StrongPass123")
    user_response = auth.register_user(payload=payload, use_case=register_use_case)
    assert user_response.email == payload.email

    login_payload = LoginRequest(email=payload.email, password=payload.password)
    token_response = auth.login(payload=login_payload, use_case=authenticate_use_case)
    token_data = dependencies.get_token_service().verify_token(token_response.access_token)
    assert token_data["sub"] == user_response.id

    user = dependencies.get_user_repository().get_by_email(payload.email)
    assert user is not None
    me_response = asyncio.run(auth.get_me(current_user=user))
    assert me_response.email == payload.email


def test_register_duplicate_email_returns_400() -> None:
    register_use_case = dependencies.get_register_user_use_case()
    payload = RegisterRequest(email="duplicate@example.com", password="Password1")
    auth.register_user(payload=payload, use_case=register_use_case)

    with pytest.raises(HTTPException) as exc:
        auth.register_user(payload=payload, use_case=register_use_case)

    assert exc.value.status_code == 400
    assert exc.value.detail == "Email already registered"


def test_login_with_invalid_credentials_returns_401() -> None:
    register_use_case = dependencies.get_register_user_use_case()
    authenticate_use_case = dependencies.get_authenticate_user_use_case()

    payload = RegisterRequest(email="valid@example.com", password="Secret1")
    auth.register_user(payload=payload, use_case=register_use_case)

    with pytest.raises(HTTPException) as exc:
        auth.login(
            payload=LoginRequest(email=payload.email, password="Wrong"),
            use_case=authenticate_use_case,
        )
    assert exc.value.status_code == 401
    assert exc.value.detail == "Invalid email or password"

    with pytest.raises(HTTPException) as missing_exc:
        auth.login(
            payload=LoginRequest(email="missing@example.com", password="Secret1"),
            use_case=authenticate_use_case,
        )
    assert missing_exc.value.status_code == 401
    assert missing_exc.value.detail == "Invalid email or password"
