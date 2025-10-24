from __future__ import annotations

from dataclasses import dataclass

from app.application.contracts.repositories import InvoiceRepository
from app.application.contracts.services import InvoiceParser
from app.domain import Invoice


class InvoiceAlreadyExistsError(RuntimeError):
    pass


class InvalidInvoicePayloadError(RuntimeError):
    pass


@dataclass(slots=True)
class UploadInvoice:
    invoice_repository: InvoiceRepository
    invoice_parser: InvoiceParser

    def execute(self, *, owner_id: str, filename: str, content: bytes) -> Invoice:
        if not content.strip():
            raise InvalidInvoicePayloadError("El archivo está vacío")

        try:
            parsed = self.invoice_parser.parse(content)
        except ValueError as exc:
            raise InvalidInvoicePayloadError("El XML de la factura no es válido") from exc

        external_id = str(parsed.get("external_id", "")).strip()
        if not external_id:
            raise InvalidInvoicePayloadError("No se pudo leer el identificador externo")

        existing = self.invoice_repository.find_by_owner_and_external_id(owner_id, external_id)
        if existing is not None:
            raise InvoiceAlreadyExistsError("La factura ya fue cargada previamente")

        invoice = Invoice.create(
            owner_id=owner_id,
            external_id=external_id,
            issue_date=parsed["issue_date"],
            supplier_name=parsed["supplier"]["name"],
            supplier_tax_id=parsed["supplier"]["tax_id"],
            customer_name=parsed["customer"]["name"],
            customer_tax_id=parsed["customer"]["tax_id"],
            currency=parsed["currency"],
            total_amount=parsed["total_amount"],
            tax_amount=parsed["tax_amount"],
            lines=parsed["lines"],
            original_filename=filename,
            raw_xml=parsed["raw_xml"],
        )

        self.invoice_repository.add(invoice)
        return invoice
