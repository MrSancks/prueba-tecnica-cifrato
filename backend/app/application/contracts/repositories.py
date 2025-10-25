from typing import Protocol


class UserRepository(Protocol):
    def get_by_id(self, user_id: str) -> object | None:
        ...

    def get_by_email(self, email: str) -> object | None:
        ...

    def add(self, user: object) -> None:
        ...


class InvoiceRepository(Protocol):
    def get_by_id(self, invoice_id: str) -> object | None:
        ...

    def list_for_user(self, user_id: str) -> list[object]:
        ...

    def add(self, invoice: object) -> None:
        ...

    def find_by_owner_and_external_id(self, owner_id: str, external_id: str) -> object | None:
        ...


class AISuggestionRepository(Protocol):
    def list_for_invoice(self, invoice_id: str) -> list[object]:
        ...

    def replace_for_invoice(self, invoice_id: str, suggestions: list[object]) -> None:
        ...

    def select_suggestion(self, invoice_id: str, line_number: int, account_code: str) -> None:
        ...
