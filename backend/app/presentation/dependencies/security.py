from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, Request, status

from app.config.security import resolve_user_from_token
from app.domain import User


def _get_user_from_state(request: Request) -> User | None:
    user = getattr(request.state, "user", None)
    if isinstance(user, User):
        return user
    return None


def _resolve_user_from_request(request: Request) -> User | None:
    user = _get_user_from_state(request)
    if user is not None:
        return user

    authorization = request.headers.get("Authorization", "")
    if authorization.startswith("Bearer "):
        token = authorization[len("Bearer ") :].strip()
        if token:
            user = resolve_user_from_token(token)
            if user is not None:
                request.state.user = user
                return user
    return None


def require_authenticated_user(request: Request) -> User:
    user = _resolve_user_from_request(request)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No autenticado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def get_optional_user(request: Request) -> User | None:
    return _resolve_user_from_request(request)


AuthenticatedUser = Annotated[User, Depends(require_authenticated_user)]
OptionalUser = Annotated[User | None, Depends(get_optional_user)]


__all__ = [
    "AuthenticatedUser",
    "OptionalUser",
    "get_optional_user",
    "require_authenticated_user",
]
