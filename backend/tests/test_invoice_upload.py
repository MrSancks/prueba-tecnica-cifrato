from io import BytesIO
from pathlib import Path

import pytest
from fastapi import HTTPException
from starlette.datastructures import Headers, UploadFile

from app.application.use_cases.invoices import (
    InvoiceAlreadyExistsError,
    InvalidInvoicePayloadError,
)
from app.config import dependencies
from app.domain import User
from app.presentation.routers import invoices


def setup_function() -> None:
    dependencies.get_invoice_repository.cache_clear()
    dependencies.get_invoice_parser.cache_clear()
    dependencies.get_ai_suggestion_repository.cache_clear()


def read_sample_xml() -> bytes:
    root = Path(__file__).resolve().parents[1]
    xml_path = root / "app" / "assessment-files" / "sales-invoice-1.xml"
    return xml_path.read_bytes()


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


def test_upload_invoice_use_case_persists_data() -> None:
    use_case = dependencies.get_upload_invoice_use_case()
    owner_id = "user-1"

    invoice = use_case.execute(
        owner_id=owner_id,
        filename="sales-invoice-1.xml",
        content=read_sample_xml(),
    )

    stored = dependencies.get_invoice_repository().list_for_user(owner_id)
    assert len(stored) == 1
    assert stored[0].external_id == invoice.external_id
    assert stored[0].lines


def test_upload_invoice_use_case_prevents_duplicates() -> None:
    use_case = dependencies.get_upload_invoice_use_case()
    owner_id = "user-dup"
    payload = dict(owner_id=owner_id, filename="sales-invoice-1.xml", content=read_sample_xml())

    use_case.execute(**payload)
    with pytest.raises(InvoiceAlreadyExistsError):
        use_case.execute(**payload)


def test_upload_invoice_use_case_rejects_invalid_xml() -> None:
    use_case = dependencies.get_upload_invoice_use_case()
    with pytest.raises(InvalidInvoicePayloadError):
        use_case.execute(owner_id="user-invalid", filename="bad.xml", content=b"<Invoice></Invoice>")


@pytest.mark.anyio
async def test_upload_invoice_router_validates_content_type() -> None:
    user = User.create(email="router@example.com", hashed_password="secret")
    use_case = dependencies.get_upload_invoice_use_case()

    file = UploadFile(
        BytesIO(b"hola"),
        filename="invoice.txt",
        headers=Headers({"content-type": "text/plain"}),
    )
    with pytest.raises(HTTPException) as exc:
        await invoices.upload_invoice(file=file, current_user=user, use_case=use_case)
    assert exc.value.status_code == 400
    assert exc.value.detail == "Solo se permiten archivos XML"


@pytest.mark.anyio
async def test_upload_invoice_router_returns_invoice_response() -> None:
    user = User.create(email="router2@example.com", hashed_password="secret")
    use_case = dependencies.get_upload_invoice_use_case()

    file = UploadFile(
        BytesIO(read_sample_xml()),
        filename="sales-invoice-1.xml",
        headers=Headers({"content-type": "application/xml"}),
    )

    response = await invoices.upload_invoice(file=file, current_user=user, use_case=use_case)
    assert response.external_id
    assert response.lines
    assert response.currency == "COP"
    assert response.status == "pendiente"
    assert isinstance(response.taxes, list)
