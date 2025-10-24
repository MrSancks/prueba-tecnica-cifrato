from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import pytest

from app.application.use_cases.invoices import NoInvoicesToExportError
from app.config import dependencies
from app.domain import User
from app.presentation.routers import invoices


def setup_function() -> None:
    dependencies.get_invoice_repository.cache_clear()
    dependencies.get_ai_suggestion_repository.cache_clear()
    dependencies.get_invoice_parser.cache_clear()
    dependencies.get_ai_suggestion_service.cache_clear()
    dependencies.get_invoice_workbook_builder.cache_clear()


def read_sample_xml() -> bytes:
    root = Path(__file__).resolve().parents[1]
    xml_path = root / "app" / "assessment-files" / "sales-invoice-1.xml"
    return xml_path.read_bytes()


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


def test_export_invoices_use_case_requires_data() -> None:
    use_case = dependencies.get_export_invoices_use_case()
    with pytest.raises(NoInvoicesToExportError):
        use_case.execute(owner_id="user-empty")


def test_export_invoices_use_case_generates_workbook() -> None:
    uploader = dependencies.get_upload_invoice_use_case()
    suggestions = dependencies.get_generate_accounting_suggestions_use_case()
    exporter = dependencies.get_export_invoices_use_case()
    owner_id = "user-export"

    invoice = uploader.execute(
        owner_id=owner_id,
        filename="sales-invoice-1.xml",
        content=read_sample_xml(),
    )
    suggestions.execute(owner_id=owner_id, invoice_id=invoice.id)

    payload = exporter.execute(owner_id=owner_id)
    assert payload

    with ZipFile(BytesIO(payload)) as archive:
        sheet = archive.read("xl/worksheets/sheet1.xml")
    assert invoice.external_id.encode() in sheet
    assert invoice.supplier_name.encode() in sheet


@pytest.mark.anyio
async def test_export_invoices_router_streams_file() -> None:
    uploader = dependencies.get_upload_invoice_use_case()
    suggestions = dependencies.get_generate_accounting_suggestions_use_case()
    exporter = dependencies.get_export_invoices_use_case()
    user = User.create(email="router-export@example.com", hashed_password="secret")

    invoice = uploader.execute(
        owner_id=user.id,
        filename="sales-invoice-1.xml",
        content=read_sample_xml(),
    )
    suggestions.execute(owner_id=user.id, invoice_id=invoice.id)

    response = await invoices.export_invoices(current_user=user, use_case=exporter)
    assert response.headers["content-disposition"].startswith("attachment;")

    chunks = bytearray()
    async for data in response.body_iterator:
        chunks.extend(data)

    assert chunks
    with ZipFile(BytesIO(chunks)) as archive:
        assert "xl/workbook.xml" in archive.namelist()
