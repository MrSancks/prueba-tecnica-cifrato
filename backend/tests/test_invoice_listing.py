from pathlib import Path

import pytest

from app.config import dependencies
from app.domain import AISuggestion, User
from app.presentation.routers import invoices


def setup_function() -> None:
    dependencies.get_invoice_repository.cache_clear()
    dependencies.get_invoice_parser.cache_clear()
    dependencies.get_ai_suggestion_repository.cache_clear()


def read_sample_xml() -> bytes:
    root = Path(__file__).resolve().parents[1]
    xml_path = root / "app" / "assessment-files" / "sales-invoice-2.xml"
    return xml_path.read_bytes()


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.mark.anyio
async def test_list_invoices_reflects_suggestion_status() -> None:
    user = User.create(email="list@example.com", hashed_password="secret")
    upload_use_case = dependencies.get_upload_invoice_use_case()
    list_use_case = dependencies.get_list_invoices_use_case()

    invoice = upload_use_case.execute(
        owner_id=user.id,
        filename="sales-invoice-2.xml",
        content=read_sample_xml(),
    )

    first_response = await invoices.list_invoices(current_user=user, use_case=list_use_case)
    assert len(first_response) == 1
    assert first_response[0].status == "pendiente"

    suggestion_repo = dependencies.get_ai_suggestion_repository()
    suggestion_repo.replace_for_invoice(
        invoice.id,
        [
            AISuggestion(
                account_code="6135",
                rationale="Compra de alimentos registrada a partir del XML base",
                confidence=0.9,
            )
        ],
    )

    second_response = await invoices.list_invoices(current_user=user, use_case=list_use_case)
    assert second_response[0].status == "procesada"


@pytest.mark.anyio
async def test_get_invoice_detail_includes_lines_and_status() -> None:
    user = User.create(email="detail@example.com", hashed_password="secret")
    upload_use_case = dependencies.get_upload_invoice_use_case()
    detail_use_case = dependencies.get_invoice_detail_use_case()

    invoice = upload_use_case.execute(
        owner_id=user.id,
        filename="sales-invoice-2.xml",
        content=read_sample_xml(),
    )

    suggestion_repo = dependencies.get_ai_suggestion_repository()
    suggestion_repo.replace_for_invoice(
        invoice.id,
        [
            AISuggestion(
                account_code="6135",
                rationale="Compra de proteínas basada en el XML de evaluación",
                confidence=0.88,
            )
        ],
    )

    response = await invoices.get_invoice(
        invoice_id=invoice.id,
        current_user=user,
        use_case=detail_use_case,
    )

    assert response.external_id == invoice.external_id
    assert response.status == "procesada"
    assert response.lines
    assert isinstance(response.taxes, list)
