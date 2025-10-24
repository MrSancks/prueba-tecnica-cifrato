from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config.dependencies import get_token_service, get_user_repository
from app.domain import User

bearer_scheme = HTTPBearer(auto_error=False)


def resolve_user_from_token(token: str) -> User | None:
    token_service = get_token_service()
    try:
        payload = token_service.verify_token(token)
    except ValueError:
        return None

    subject = payload.get("sub")
    if subject is None:
        return None

    user_repository = get_user_repository()
    return user_repository.get_by_id(subject)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)]
) -> User:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    user = resolve_user_from_token(credentials.credentials)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
