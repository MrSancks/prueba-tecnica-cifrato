from typing import Any, Protocol


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


class PUCMapper(Protocol):
    def map_to_specific_account(
        self,
        generic_code: str,
        description: str,
        rationale: str,
    ) -> dict[str, Any]:
        """
        Mapea un código PUC genérico (4 dígitos) a código específico de la empresa (8 dígitos).
        
        Returns:
            {
                "specific_code": "11050501",
                "account_name": "Efectivo CL 72",
                "confidence": 0.85,
                "explanation": "..."
            }
        """
        ...
