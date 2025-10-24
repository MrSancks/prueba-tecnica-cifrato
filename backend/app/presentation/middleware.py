from __future__ import annotations

from typing import Awaitable, Callable

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.config.security import resolve_user_from_token


class AuthenticationMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        authorization = request.headers.get("Authorization", "")
        if authorization.startswith("Bearer "):
            token = authorization[len("Bearer ") :].strip()
            if token:
                user = resolve_user_from_token(token)
                if user is not None:
                    request.state.user = user

        return await call_next(request)


__all__ = ["AuthenticationMiddleware"]
