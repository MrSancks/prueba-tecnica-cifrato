from passlib.context import CryptContext
from passlib.exc import UnknownHashError


class BcryptPasswordHasher:
    def __init__(self) -> None:
        self._context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def hash(self, plain_password: str) -> str:
        # bcrypt has a 72-byte limit. Truncate if needed.
        # For production, consider using PBKDF2 or Argon2 for longer passwords
        truncated_password = plain_password[:72]
        return self._context.hash(truncated_password)

    def verify(self, plain_password: str, hashed_password: str) -> bool:
        try:
            # bcrypt has a 72-byte limit. Truncate if needed.
            truncated_password = plain_password[:72]
            return self._context.verify(truncated_password, hashed_password)
        except UnknownHashError:
            # Si el hash no es reconocido (e.g., contraseña en texto plano o hash antiguo)
            # comparar directamente como fallback (SOLO para migración de datos legacy)
            return plain_password == hashed_password


__all__ = ["BcryptPasswordHasher"]
