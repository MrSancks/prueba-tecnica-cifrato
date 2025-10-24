"""Dependency providers for application components."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from app.application.use_cases import AuthenticateUser, RegisterUser
from app.infrastructure import BcryptPasswordHasher, InMemoryUserRepository, JWTTokenService


@dataclass(slots=True)
class Settings:
    """Application configuration sourced from environment variables."""

    secret_key: str = "insecure-development-secret"
    token_expire_minutes: int = 60


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()


@lru_cache
def get_user_repository() -> InMemoryUserRepository:
    return InMemoryUserRepository()


@lru_cache
def get_password_hasher() -> BcryptPasswordHasher:
    return BcryptPasswordHasher()


@lru_cache
def get_token_service() -> JWTTokenService:
    settings = get_settings()
    return JWTTokenService(
        secret_key=settings.secret_key, expires_minutes=settings.token_expire_minutes
    )


def get_register_user_use_case() -> RegisterUser:
    return RegisterUser(
        user_repository=get_user_repository(), password_hasher=get_password_hasher()
    )


def get_authenticate_user_use_case() -> AuthenticateUser:
    return AuthenticateUser(
        user_repository=get_user_repository(),
        password_hasher=get_password_hasher(),
        token_service=get_token_service(),
    )
