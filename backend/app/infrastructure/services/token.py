from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt


class JWTTokenService:
    def __init__(self, secret_key: str, algorithm: str = "HS256", expires_minutes: int = 60) -> None:
        self._secret_key = secret_key
        self._algorithm = algorithm
        self._expires_minutes = expires_minutes

    def create_access_token(self, subject: str) -> str:
        expire = datetime.now(timezone.utc) + timedelta(minutes=self._expires_minutes)
        payload = {"sub": subject, "exp": expire}
        return jwt.encode(payload, self._secret_key, algorithm=self._algorithm)

    def verify_token(self, token: str) -> dict[str, Any]:
        try:
            return jwt.decode(token, self._secret_key, algorithms=[self._algorithm])
        except JWTError as exc:  # pragma: no cover - defensive programming
            raise ValueError("Invalid token") from exc


__all__ = ["JWTTokenService"]
