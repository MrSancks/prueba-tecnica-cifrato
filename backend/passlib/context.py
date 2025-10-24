from __future__ import annotations

import hashlib
import hmac
import os


class CryptContext:
    def __init__(self, schemes: list[str] | None = None, deprecated: str | None = None) -> None:
        self._schemes = schemes or []
        self._deprecated = deprecated

    def hash(self, plain_password: str) -> str:
        salt = os.urandom(16)
        digest = hashlib.sha256(salt + plain_password.encode("utf-8")).hexdigest()
        return f"stub${salt.hex()}${digest}"

    def verify(self, plain_password: str, hashed_password: str) -> bool:
        try:
            _, salt_hex, digest = hashed_password.split("$")
        except ValueError:
            return False
        expected = hashlib.sha256(bytes.fromhex(salt_hex) + plain_password.encode("utf-8")).hexdigest()
        return hmac.compare_digest(expected, digest)
