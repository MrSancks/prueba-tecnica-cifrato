from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass(slots=True)
class AISuggestion:
    account_code: str
    rationale: str
    confidence: float
    source: str = "unknown"  # "heuristic" | "lookup" | "ai" | "hybrid" | "ml"
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    line_number: int | None = None  # Número de línea de la factura asociada
    puc_account_id: str | None = None  # ID de la cuenta PUC en Firestore
    account_name: str | None = None  # Nombre de la cuenta PUC
