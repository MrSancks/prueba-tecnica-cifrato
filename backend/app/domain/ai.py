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
    is_selected: bool = False  # Indica si el usuario seleccionó esta sugerencia
    line_number: int | None = None  # Número de línea de la factura asociada
