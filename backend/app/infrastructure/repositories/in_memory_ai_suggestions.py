from __future__ import annotations

from app.domain import AISuggestion


class InMemoryAISuggestionRepository:
    def __init__(self) -> None:
        self._storage: dict[str, list[AISuggestion]] = {}

    def list_for_invoice(self, invoice_id: str) -> list[AISuggestion]:
        return list(self._storage.get(invoice_id, ()))

    def replace_for_invoice(self, invoice_id: str, suggestions: list[AISuggestion]) -> None:
        self._storage[invoice_id] = list(suggestions)
