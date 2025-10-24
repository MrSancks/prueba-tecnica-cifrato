from __future__ import annotations

from dataclasses import dataclass

from app.application.contracts.repositories import UserRepository
from app.application.contracts.services import PasswordHasher, TokenService
from app.domain import User


class UserAlreadyExistsError(RuntimeError):
    pass


class InvalidCredentialsError(RuntimeError):
    pass


@dataclass(slots=True)
class RegisterUser:
    user_repository: UserRepository
    password_hasher: PasswordHasher

    def execute(self, email: str, password: str) -> User:
        if self.user_repository.get_by_email(email) is not None:
            raise UserAlreadyExistsError("Email is already registered")

        hashed_password = self.password_hasher.hash(password)
        user = User.create(email=email, hashed_password=hashed_password)
        self.user_repository.add(user)
        return user


@dataclass(slots=True)
class AuthenticateUser:
    user_repository: UserRepository
    password_hasher: PasswordHasher
    token_service: TokenService

    def execute(self, email: str, password: str) -> tuple[User, str]:
        user = self.user_repository.get_by_email(email)
        if user is None:
            raise InvalidCredentialsError("Invalid email or password")

        if not self.password_hasher.verify(password, user.hashed_password):
            raise InvalidCredentialsError("Invalid email or password")

        token = self.token_service.create_access_token(subject=user.id)
        return user, token
