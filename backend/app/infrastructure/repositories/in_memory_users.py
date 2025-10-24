"""In-memory implementation of the user repository."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Dict

from app.domain import User


class InMemoryUserRepository:
    """Simple in-memory storage for user entities."""

    def __init__(self) -> None:
        self._users_by_id: Dict[str, User] = {}
        self._users_by_email: Dict[str, User] = {}

    def get_by_id(self, user_id: str) -> User | None:
        return self._users_by_id.get(user_id)

    def get_by_email(self, email: str) -> User | None:
        return self._users_by_email.get(email.lower())

    def add(self, user: User) -> None:
        normalized_email = user.email.lower()
        self._users_by_id[user.id] = user
        self._users_by_email[normalized_email] = user

    def list_all(self) -> Iterable[User]:
        """Return all stored users (primarily for testing)."""
        return self._users_by_id.values()


__all__ = ["InMemoryUserRepository"]
