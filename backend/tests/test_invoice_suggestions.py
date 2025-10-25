from pathlib import Path

import pytest

from app.application.use_cases.invoices import GenerateAccountingSuggestions, InvoiceNotFoundError
from app.config import dependencies
from app.domain import User
from app.presentation.routers import invoices


def setup_function() -> None:
    dependencies.get_invoice_repository.cache_clear()
    dependencies.get_invoice_parser.cache_clear()
    dependencies.get_ai_suggestion_repository.cache_clear()


def read_sample_xml(name: str = "sales-invoice-2.xml") -> bytes:
    root = Path(__file__).resolve().parents[1]
    return (root / "app" / "assessment-files" / name).read_bytes()


class StubAISuggestionService:
    def __init__(self, payload: list[dict[str, object]] | None = None) -> None:
        self.payload = payload or [
            {"account_code": "5305", "rationale": "Flete y transporte complementario", "confidence": 0.7}
        ]
        self.called_with: dict[str, object] | None = None

    def generate_suggestions(self, invoice_payload: dict[str, object]) -> list[dict[str, object]]:
        self.called_with = invoice_payload
        return self.payload


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


def create_invoice_for(owner_id: str, filename: str = "sales-invoice-2.xml"):
    upload_use_case = dependencies.get_upload_invoice_use_case()
    return upload_use_case.execute(
        owner_id=owner_id,
        filename=filename,
        content=read_sample_xml(filename),
    )


def test_generate_suggestions_uses_ai_first() -> None:
    """
    Sistema refactorizado: ahora usa AI como fuente primaria.
    Ya no hay heurísticas hardcodeadas.
    """
    owner_id = "owner-suggestions"
    invoice = create_invoice_for(owner_id)

    use_case = GenerateAccountingSuggestions(
        invoice_repository=dependencies.get_invoice_repository(),
        suggestion_repository=dependencies.get_ai_suggestion_repository(),
        ai_service=StubAISuggestionService(),
    )

    result = use_case.execute(owner_id=owner_id, invoice_id=invoice.id)

    # Verifica que devuelve sugerencias del AI stub
    assert len(result) > 0
    assert result[0].account_code == "5305"
    assert result[0].source == "ai"
    assert "Flete y transporte" in result[0].rationale

    # Verifica que se persisten
    stored = dependencies.get_ai_suggestion_repository().list_for_invoice(invoice.id)
    assert stored == result


def test_generate_suggestions_requires_invoice_owner() -> None:
    invoice = create_invoice_for("different-owner")

    use_case = GenerateAccountingSuggestions(
        invoice_repository=dependencies.get_invoice_repository(),
        suggestion_repository=dependencies.get_ai_suggestion_repository(),
        ai_service=StubAISuggestionService([]),
    )

    with pytest.raises(InvoiceNotFoundError):
        use_case.execute(owner_id="other-user", invoice_id=invoice.id)


@pytest.mark.anyio
async def test_router_returns_serialized_suggestions() -> None:
    """
    Verifica que el router serializa correctamente las sugerencias del AI.
    """
    user = User.create(email="suggestions@example.com", hashed_password="secret")
    invoice = create_invoice_for(user.id)

    use_case = GenerateAccountingSuggestions(
        invoice_repository=dependencies.get_invoice_repository(),
        suggestion_repository=dependencies.get_ai_suggestion_repository(),
        ai_service=StubAISuggestionService(),
    )

    response = await invoices.suggest_accounts(
        invoice_id=invoice.id,
        current_user=user,
        use_case=use_case,
    )

    assert response.invoice_id == invoice.id
    assert response.suggestions
    # Verifica que devuelve el código del AI stub
    assert response.suggestions[0].account_code == "5305"
    assert response.suggestions[0].source == "ai"
