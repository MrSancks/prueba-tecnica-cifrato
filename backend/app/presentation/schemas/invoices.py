from datetime import date
from decimal import Decimal

from pydantic import BaseModel

from app.domain import AISuggestion, Invoice, InvoiceLine


class InvoiceLineResponse(BaseModel):
    line_id: str
    description: str
    quantity: Decimal
    unit_price: Decimal
    line_extension_amount: Decimal
    tax_amount: Decimal

    @classmethod
    def from_domain(cls, line: InvoiceLine) -> "InvoiceLineResponse":
        base_amount = line.unit_price * line.quantity
        tax_amount = line.line_extension_amount - base_amount
        if tax_amount < Decimal("0"):
            tax_amount = Decimal("0")
        return cls(
            line_id=line.line_id,
            description=line.description,
            quantity=line.quantity,
            unit_price=line.unit_price,
            line_extension_amount=line.line_extension_amount,
            tax_amount=tax_amount,
        )


class InvoiceSummaryResponse(BaseModel):
    id: str
    external_id: str
    issue_date: date
    supplier_name: str
    currency: str
    total_amount: Decimal
    status: str

    @classmethod
    def from_domain(cls, invoice: Invoice, *, status: str) -> "InvoiceSummaryResponse":
        return cls(
            id=invoice.id,
            external_id=invoice.external_id,
            issue_date=invoice.issue_date,
            supplier_name=invoice.supplier_name,
            currency=invoice.currency,
            total_amount=invoice.total_amount,
            status=status,
        )


class InvoiceTaxResponse(BaseModel):
    type: str
    amount: Decimal


class InvoiceDetailResponse(InvoiceSummaryResponse):
    supplier_tax_id: str
    customer_name: str
    customer_tax_id: str
    tax_amount: Decimal
    original_filename: str
    lines: list[InvoiceLineResponse]
    taxes: list[InvoiceTaxResponse]

    @classmethod
    def from_domain(cls, invoice: Invoice, *, status: str) -> "InvoiceDetailResponse":
        taxes: list[InvoiceTaxResponse] = []
        if invoice.tax_amount > Decimal("0"):
            taxes.append(InvoiceTaxResponse(type="IVA", amount=invoice.tax_amount))
        return cls(
            id=invoice.id,
            external_id=invoice.external_id,
            issue_date=invoice.issue_date,
            supplier_name=invoice.supplier_name,
            currency=invoice.currency,
            total_amount=invoice.total_amount,
            status=status,
            supplier_tax_id=invoice.supplier_tax_id,
            customer_name=invoice.customer_name,
            customer_tax_id=invoice.customer_tax_id,
            tax_amount=invoice.tax_amount,
            original_filename=invoice.original_filename,
            lines=[InvoiceLineResponse.from_domain(line) for line in invoice.lines],
            taxes=taxes,
        )


class AISuggestionResponse(BaseModel):
    account_code: str
    rationale: str
    confidence: float
    source: str
    generated_at: str  # ISO 8601 string
    line_number: int | None
    puc_account_id: str | None = None  # ID de la cuenta PUC en Firestore
    account_name: str | None = None  # Nombre de la cuenta PUC

    @classmethod
    def from_domain(cls, suggestion: AISuggestion) -> "AISuggestionResponse":
        return cls(
            account_code=suggestion.account_code,
            rationale=suggestion.rationale,
            confidence=suggestion.confidence,
            source=suggestion.source,
            generated_at=suggestion.generated_at.isoformat() if suggestion.generated_at else "",
            line_number=suggestion.line_number,
            puc_account_id=suggestion.puc_account_id,
            account_name=suggestion.account_name,
        )


class AccountingSuggestionsResponse(BaseModel):
    invoice_id: str
    suggestions: list[AISuggestionResponse]

    @classmethod
    def from_domain(
        cls,
        *,
        invoice_id: str,
        suggestions: list[AISuggestion],
    ) -> "AccountingSuggestionsResponse":
        return cls(
            invoice_id=invoice_id,
            suggestions=[AISuggestionResponse.from_domain(item) for item in suggestions],
        )
