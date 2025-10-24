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

    @classmethod
    def from_domain(cls, line: InvoiceLine) -> "InvoiceLineResponse":
        return cls(
            line_id=line.line_id,
            description=line.description,
            quantity=line.quantity,
            unit_price=line.unit_price,
            line_extension_amount=line.line_extension_amount,
        )


class InvoiceResponse(BaseModel):
    id: str
    external_id: str
    issue_date: date
    supplier_name: str
    supplier_tax_id: str
    customer_name: str
    customer_tax_id: str
    currency: str
    total_amount: Decimal
    tax_amount: Decimal
    original_filename: str
    lines: list[InvoiceLineResponse]

    @classmethod
    def from_domain(cls, invoice: Invoice) -> "InvoiceResponse":
        return cls(
            id=invoice.id,
            external_id=invoice.external_id,
            issue_date=invoice.issue_date,
            supplier_name=invoice.supplier_name,
            supplier_tax_id=invoice.supplier_tax_id,
            customer_name=invoice.customer_name,
            customer_tax_id=invoice.customer_tax_id,
            currency=invoice.currency,
            total_amount=invoice.total_amount,
            tax_amount=invoice.tax_amount,
            original_filename=invoice.original_filename,
            lines=[InvoiceLineResponse.from_domain(line) for line in invoice.lines],
        )


class AISuggestionResponse(BaseModel):
    account_code: str
    rationale: str
    confidence: float

    @classmethod
    def from_domain(cls, suggestion: AISuggestion) -> "AISuggestionResponse":
        return cls(
            account_code=suggestion.account_code,
            rationale=suggestion.rationale,
            confidence=suggestion.confidence,
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
