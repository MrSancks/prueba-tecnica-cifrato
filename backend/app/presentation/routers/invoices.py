from io import BytesIO

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse

from app.application.use_cases.invoices import (
    GenerateAccountingSuggestions,
    InvoiceAlreadyExistsError,
    InvoiceNotFoundError,
    InvalidInvoicePayloadError,
    ListInvoices,
    NoInvoicesToExportError,
)
from app.config.dependencies import (
    get_invoice_detail_use_case,
    get_list_invoices_use_case,
    get_generate_accounting_suggestions_use_case,
    get_export_invoices_use_case,
    get_upload_invoice_use_case,
)
from app.presentation.schemas.invoices import (
    AccountingSuggestionsResponse,
    InvoiceDetailResponse,
    InvoiceSummaryResponse,
)
from app.presentation.dependencies.security import AuthenticatedUser

router = APIRouter(prefix="/invoices", tags=["invoices"])


@router.get("", response_model=list[InvoiceSummaryResponse])
async def list_invoices(
    current_user: AuthenticatedUser,
    use_case: ListInvoices = Depends(get_list_invoices_use_case),
) -> list[InvoiceSummaryResponse]:
    items = use_case.execute(owner_id=current_user.id)
    return [InvoiceSummaryResponse.from_domain(item.invoice, status=item.status) for item in items]


@router.post("/upload", response_model=InvoiceDetailResponse, status_code=status.HTTP_201_CREATED)
async def upload_invoice(
    current_user: AuthenticatedUser,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    use_case=Depends(get_upload_invoice_use_case),
    generate_suggestions_use_case: GenerateAccountingSuggestions = Depends(get_generate_accounting_suggestions_use_case),
):
    if file.content_type not in {"application/xml", "text/xml"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Solo se permiten archivos XML")

    content = await file.read()

    try:
        invoice = use_case.execute(
            owner_id=current_user.id,
            filename=file.filename or "factura.xml",
            content=content,
        )
    except InvalidInvoicePayloadError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except InvoiceAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    # Disparar generación de sugerencias en segundo plano
    background_tasks.add_task(
        generate_suggestions_use_case.execute,
        owner_id=current_user.id,
        invoice_id=invoice.id,
    )

    return InvoiceDetailResponse.from_domain(invoice, status="pendiente")


@router.get("/export")
async def export_invoices(
    current_user: AuthenticatedUser,
    use_case=Depends(get_export_invoices_use_case),
):
    try:
        payload = use_case.execute(owner_id=current_user.id)
    except NoInvoicesToExportError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    stream = BytesIO(payload)
    headers = {"Content-Disposition": 'attachment; filename="facturas.xlsx"'}
    return StreamingResponse(
        stream,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers,
    )


@router.get("/{invoice_id}/suggest", response_model=AccountingSuggestionsResponse)
async def get_suggestions(
    invoice_id: str,
    current_user: AuthenticatedUser,
    detail_use_case=Depends(get_invoice_detail_use_case),
) -> AccountingSuggestionsResponse:
    """
    Obtiene las sugerencias existentes SIN regenerarlas.
    Si no hay sugerencias, retorna lista vacía.
    """
    try:
        detail = detail_use_case.execute(owner_id=current_user.id, invoice_id=invoice_id)
    except InvoiceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    
    # GetInvoiceDetail ya carga las sugerencias del repositorio
    from app.config.dependencies import get_ai_suggestion_repository
    suggestion_repo = get_ai_suggestion_repository()
    suggestions = suggestion_repo.list_for_invoice(invoice_id)
    
    return AccountingSuggestionsResponse.from_domain(invoice_id=invoice_id, suggestions=suggestions)


@router.post("/{invoice_id}/suggest", response_model=AccountingSuggestionsResponse)
async def regenerate_suggestions(
    invoice_id: str,
    current_user: AuthenticatedUser,
    use_case: GenerateAccountingSuggestions = Depends(get_generate_accounting_suggestions_use_case),
) -> AccountingSuggestionsResponse:
    """
    REGENERA las sugerencias contables usando IA.
    Usar este endpoint cuando el usuario haga clic en "Recalcular".
    """
    try:
        suggestions = use_case.execute(owner_id=current_user.id, invoice_id=invoice_id)
    except InvoiceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return AccountingSuggestionsResponse.from_domain(invoice_id=invoice_id, suggestions=suggestions)


@router.get("/{invoice_id}", response_model=InvoiceDetailResponse)
async def get_invoice(
    invoice_id: str,
    current_user: AuthenticatedUser,
    use_case=Depends(get_invoice_detail_use_case),
):
    try:
        detail = use_case.execute(owner_id=current_user.id, invoice_id=invoice_id)
    except InvoiceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return InvoiceDetailResponse.from_domain(detail.invoice, status=detail.status)
