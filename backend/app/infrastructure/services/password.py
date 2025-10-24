"""Password hashing services."""

from passlib.context import CryptContext


class BcryptPasswordHasher:
    """Password hashing using Passlib's bcrypt context."""

    def __init__(self) -> None:
        self._context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def hash(self, plain_password: str) -> str:
        return self._context.hash(plain_password)

    def verify(self, plain_password: str, hashed_password: str) -> bool:
        return self._context.verify(plain_password, hashed_password)


__all__ = ["BcryptPasswordHasher"]
