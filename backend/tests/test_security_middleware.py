from __future__ import annotations

import pytest
from fastapi import HTTPException
from starlette.requests import Request
from starlette.responses import Response

from app.config import dependencies
from app.config.security import resolve_user_from_token
from app.presentation.dependencies.security import require_authenticated_user
from app.presentation.middleware import AuthenticationMiddleware


async def _empty_receive() -> dict[str, object]:
    return {"type": "http.request"}


def _build_request(headers: dict[str, str] | None = None) -> Request:
    raw_headers = []
    if headers:
        raw_headers = [
            (key.lower().encode("latin-1"), value.encode("latin-1")) for key, value in headers.items()
        ]
    scope = {"type": "http", "headers": raw_headers}
    return Request(scope, _empty_receive)


def _register_user(email: str, password: str) -> str:
    register_use_case = dependencies.get_register_user_use_case()
    authenticate_use_case = dependencies.get_authenticate_user_use_case()
    register_use_case.execute(email=email, password=password)
    _, token = authenticate_use_case.execute(email=email, password=password)
    return token


def setup_function() -> None:
    dependencies.get_user_repository.cache_clear()
    dependencies.get_password_hasher.cache_clear()
    dependencies.get_token_service.cache_clear()
    dependencies.get_invoice_repository.cache_clear()
    dependencies.get_ai_suggestion_repository.cache_clear()


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


def test_require_authenticated_user_without_header_raises() -> None:
    request = _build_request()
    with pytest.raises(HTTPException) as exc:
        require_authenticated_user(request)
    assert exc.value.status_code == 401
    assert exc.value.detail == "No autenticado"


def test_require_authenticated_user_with_invalid_token_raises() -> None:
    request = _build_request({"Authorization": "Bearer invalid-token"})
    with pytest.raises(HTTPException) as exc:
        require_authenticated_user(request)
    assert exc.value.status_code == 401
    assert exc.value.detail == "No autenticado"


def test_require_authenticated_user_with_valid_token_returns_user() -> None:
    token = _register_user(email="secure@example.com", password="ClaveSegura1")
    request = _build_request({"Authorization": f"Bearer {token}"})
    user = require_authenticated_user(request)
    assert user.email == "secure@example.com"
    assert resolve_user_from_token(token) == user


@pytest.mark.anyio
async def test_authentication_middleware_populates_request_state() -> None:
    token = _register_user(email="middleware@example.com", password="ClaveFirme2")
    middleware = AuthenticationMiddleware(lambda scope: None)

    request = _build_request({"Authorization": f"Bearer {token}"})

    async def call_next(received_request: Request) -> Response:
        user = getattr(received_request.state, "user", None)
        assert user is not None
        return Response("ok")

    response = await middleware.dispatch(request, call_next)
    assert response.body == b"ok"
