from __future__ import annotations

from collections import defaultdict

from app.domain import Invoice


class InMemoryInvoiceRepository:
    def __init__(self) -> None:
        self._by_id: dict[str, Invoice] = {}
        self._by_owner: defaultdict[str, dict[str, Invoice]] = defaultdict(dict)

    def get_by_id(self, invoice_id: str) -> Invoice | None:
        return self._by_id.get(invoice_id)

    def list_for_user(self, user_id: str) -> list[Invoice]:
        return list(self._by_owner[user_id].values())

    def add(self, invoice: Invoice) -> None:
        self._by_id[invoice.id] = invoice
        self._by_owner[invoice.owner_id][invoice.external_id] = invoice

    def find_by_owner_and_external_id(self, owner_id: str, external_id: str) -> Invoice | None:
        return self._by_owner[owner_id].get(external_id)
