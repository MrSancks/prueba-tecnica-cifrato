from __future__ import annotations

import json
import os
from functools import lru_cache
from typing import Any

try:  # pragma: no cover - la dependencia real es opcional en pruebas
    import firebase_admin
    from firebase_admin import credentials
except ModuleNotFoundError:  # pragma: no cover - entornos sin firebase_admin
    firebase_admin = None  # type: ignore[assignment]
    credentials = None  # type: ignore[assignment]


class FirebaseAdminUnavailable(RuntimeError):
    pass


def _load_service_account() -> dict[str, Any]:
    credentials_path = os.getenv("FIREBASE_CREDENTIALS_PATH")
    credentials_json = os.getenv("FIREBASE_CREDENTIALS_JSON")

    if credentials_path:
        with open(credentials_path, "r", encoding="utf-8") as handle:
            return json.load(handle)

    if credentials_json:
        return json.loads(credentials_json)

    raise FirebaseAdminUnavailable(
        "Configura FIREBASE_CREDENTIALS_PATH o FIREBASE_CREDENTIALS_JSON para inicializar Firebase Admin.",
    )


@lru_cache
def initialize_firebase_app() -> "firebase_admin.App":
    if firebase_admin is None or credentials is None:
        raise FirebaseAdminUnavailable(
            "Instala firebase-admin e inyecta las credenciales del servicio para habilitar Firebase en el backend.",
        )

    try:
        return firebase_admin.get_app()
    except ValueError:
        service_account_info = _load_service_account()
        project_id = service_account_info.get("project_id")
        cert = credentials.Certificate(service_account_info)
        return firebase_admin.initialize_app(cert, {"projectId": project_id} if project_id else None)


def firebase_project_id() -> str:
    data = _load_service_account()
    project_id = data.get("project_id")
    if not project_id:
        raise FirebaseAdminUnavailable(
            "Las credenciales de Firebase no incluyen project_id; verifica el JSON del servicio.",
        )
    return str(project_id)
