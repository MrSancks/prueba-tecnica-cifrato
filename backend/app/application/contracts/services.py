from typing import Protocol


class PasswordHasher(Protocol):
    def hash(self, plain_password: str) -> str:
        ...

    def verify(self, plain_password: str, hashed_password: str) -> bool:
        ...


class TokenService(Protocol):
    def create_access_token(self, subject: str) -> str:
        ...

    def verify_token(self, token: str) -> dict[str, object]:
        ...


class AISuggestionService(Protocol):
    def generate_suggestions(self, invoice_payload: dict[str, object]) -> list[dict[str, object]]:
        ...


class InvoiceParser(Protocol):
    def parse(self, xml_bytes: bytes) -> dict[str, object]:
        ...


class InvoiceWorkbookBuilder(Protocol):
    def build(
        self,
        invoices: list[object],
        suggestions_map: dict[str, list[object]],
    ) -> bytes:
        ...
