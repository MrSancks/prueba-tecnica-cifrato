from __future__ import annotations

from app.domain import AISuggestion


class InMemoryAISuggestionRepository:
    def __init__(self) -> None:
        self._storage: dict[str, list[AISuggestion]] = {}

    def list_for_invoice(self, invoice_id: str) -> list[AISuggestion]:
        return list(self._storage.get(invoice_id, ()))

    def replace_for_invoice(self, invoice_id: str, suggestions: list[AISuggestion]) -> None:
        self._storage[invoice_id] = list(suggestions)

    def select_suggestion(self, invoice_id: str, line_number: int, account_code: str) -> None:
        """Marca una sugerencia como seleccionada."""
        suggestions = self._storage.get(invoice_id, [])
        for sug in suggestions:
            # Desmarcar todas de esa línea
            if sug.line_number == line_number:
                sug.is_selected = False
            # Marcar la seleccionada
            if sug.line_number == line_number and sug.account_code == account_code:
                sug.is_selected = True
