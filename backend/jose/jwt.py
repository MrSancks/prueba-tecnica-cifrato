from __future__ import annotations

import base64
import hashlib
import hmac
import json
from datetime import datetime, timezone
from typing import Any, Iterable

from .exceptions import JWTError


def encode(payload: dict[str, Any], key: str, algorithm: str = "HS256") -> str:
    header = {"alg": algorithm, "typ": "JWT"}
    segments = [
        _b64encode(json.dumps(header, separators=(",", ":"), sort_keys=True).encode("utf-8")),
        _b64encode(json.dumps(payload, separators=(",", ":"), default=_serialize, sort_keys=True).encode("utf-8")),
    ]
    signing_input = ".".join(segments).encode("utf-8")
    signature = _sign(signing_input, key, algorithm)
    segments.append(_b64encode(signature))
    return ".".join(segments)


def decode(token: str, key: str, algorithms: Iterable[str]) -> dict[str, Any]:
    try:
        header_b64, payload_b64, signature_b64 = token.split(".")
    except ValueError as exc:  # pragma: no cover - defensive
        raise JWTError("Token malformado") from exc

    header = json.loads(_b64decode(header_b64))
    if header.get("alg") not in algorithms:
        raise JWTError("Algoritmo no soportado")

    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
    expected_signature = _sign(signing_input, key, header["alg"])
    signature = _b64decode(signature_b64)
    if not hmac.compare_digest(signature, expected_signature):
        raise JWTError("Firma inválida")

    payload = json.loads(_b64decode(payload_b64))
    exp = payload.get("exp")
    if exp is not None:
        exp_dt = _parse_datetime(exp)
        if exp_dt < datetime.now(timezone.utc):
            raise JWTError("Token expirado")

    return payload


def _serialize(value: Any) -> Any:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.isoformat()
    raise TypeError(f"No se puede serializar el tipo {type(value)!r}")


def _parse_datetime(value: Any) -> datetime:
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, tz=timezone.utc)
    if isinstance(value, str):
        return datetime.fromisoformat(value)
    raise JWTError("Formato de expiración inválido")


def _sign(message: bytes, key: str, algorithm: str) -> bytes:
    if algorithm != "HS256":  # pragma: no cover - simplified implementation
        raise JWTError("Solo se soporta HS256")
    return hmac.new(key.encode("utf-8"), message, hashlib.sha256).digest()


def _b64encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)
