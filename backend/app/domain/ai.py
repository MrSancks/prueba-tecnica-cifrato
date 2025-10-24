from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class AISuggestion:
    account_code: str
    rationale: str
    confidence: float
