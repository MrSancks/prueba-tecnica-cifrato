from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.application.use_cases.invoices import (
    InvoiceAlreadyExistsError,
    InvalidInvoicePayloadError,
)
from app.config.dependencies import get_upload_invoice_use_case
from app.config.security import CurrentUser
from app.presentation.schemas.invoices import InvoiceResponse

router = APIRouter(prefix="/invoices", tags=["invoices"])


@router.post("/upload", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
async def upload_invoice(
    current_user: CurrentUser,
    file: UploadFile = File(...),
    use_case=Depends(get_upload_invoice_use_case),
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

    return InvoiceResponse.from_domain(invoice)
