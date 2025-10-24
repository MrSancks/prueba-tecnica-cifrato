from __future__ import annotations

from dataclasses import dataclass

from app.application.contracts.repositories import (
    AISuggestionRepository,
    InvoiceRepository,
)
from app.application.contracts.services import (
    AISuggestionService,
    InvoiceParser,
    InvoiceWorkbookBuilder,
)
from app.domain import AISuggestion, Invoice


class InvoiceAlreadyExistsError(RuntimeError):
    pass


class InvalidInvoicePayloadError(RuntimeError):
    pass


class InvoiceNotFoundError(RuntimeError):
    pass


class NoInvoicesToExportError(RuntimeError):
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


@dataclass(slots=True)
class GenerateAccountingSuggestions:
    invoice_repository: InvoiceRepository
    suggestion_repository: AISuggestionRepository
    ai_service: AISuggestionService

    def execute(self, *, owner_id: str, invoice_id: str) -> list[AISuggestion]:
        invoice = self.invoice_repository.get_by_id(invoice_id)
        if invoice is None or invoice.owner_id != owner_id:
            raise InvoiceNotFoundError("La factura no existe para el usuario indicado")

        heuristics = self._build_deterministic_suggestions(invoice)
        ai_payload = self.ai_service.generate_suggestions(self._serialize_invoice(invoice))
        model_suggestions = self._coerce_ai_suggestions(ai_payload)
        merged = self._merge_suggestions(heuristics, model_suggestions)
        self.suggestion_repository.replace_for_invoice(invoice.id, merged)
        return merged

    def _build_deterministic_suggestions(self, invoice: Invoice) -> list[AISuggestion]:
        collected: list[AISuggestion] = []
        supplier = invoice.supplier_name.upper()
        keywords = {line.description.upper() for line in invoice.lines}
        text_blob = " ".join(keywords)

        if "BURGER" in supplier or "BURGER" in text_blob or "COMBO" in text_blob:
            collected.append(
                AISuggestion(
                    account_code="6135",
                    rationale="Costo de ventas de comidas preparadas proveniente de un proveedor de hamburguesas",
                    confidence=0.85,
                )
            )

        meat_keywords = {"CARNE", "RES", "PALETERO", "MATAMBRE", "LOMO"}
        if meat_keywords & {word for word in text_blob.split()} or "CARNES" in supplier:
            collected.append(
                AISuggestion(
                    account_code="6135",
                    rationale="Adquisición de proteínas y cortes para la operación del restaurante",
                    confidence=0.82,
                )
            )

        cleaning_tokens = {"LIMPIA", "ASEO", "DESINF"}
        if cleaning_tokens & {word for word in text_blob.split()}:
            collected.append(
                AISuggestion(
                    account_code="5165",
                    rationale="Compra de insumos de aseo y limpieza necesarios para el punto de venta",
                    confidence=0.8,
                )
            )

        if not collected:
            collected.append(
                AISuggestion(
                    account_code="5199",
                    rationale="Gasto operativo sin clasificación específica en la factura analizada",
                    confidence=0.6,
                )
            )
        return collected

    def _serialize_invoice(self, invoice: Invoice) -> dict[str, object]:
        return {
            "external_id": invoice.external_id,
            "supplier": {"name": invoice.supplier_name, "tax_id": invoice.supplier_tax_id},
            "customer": {"name": invoice.customer_name, "tax_id": invoice.customer_tax_id},
            "currency": invoice.currency,
            "total_amount": float(invoice.total_amount),
            "tax_amount": float(invoice.tax_amount),
            "lines": [
                {
                    "description": line.description,
                    "amount": float(line.line_extension_amount),
                    "quantity": float(line.quantity),
                }
                for line in invoice.lines
            ],
        }

    def _coerce_ai_suggestions(self, raw: list[dict[str, object]]) -> list[AISuggestion]:
        suggestions: list[AISuggestion] = []
        for item in raw:
            code = str(item.get("account_code", "")).strip()
            if not code:
                continue
            rationale = str(item.get("rationale", "Sugerencia generada por el modelo")).strip()
            try:
                confidence = float(item.get("confidence", 0.5))
            except (TypeError, ValueError):
                confidence = 0.5
            suggestions.append(AISuggestion(account_code=code, rationale=rationale, confidence=confidence))
        return suggestions

    def _merge_suggestions(
        self,
        deterministic: list[AISuggestion],
        generated: list[AISuggestion],
    ) -> list[AISuggestion]:
        combined: list[AISuggestion] = []
        seen: set[tuple[str, str]] = set()

        for suggestion in (*deterministic, *generated):
            key = (suggestion.account_code, suggestion.rationale)
            if key in seen:
                continue
            seen.add(key)
            combined.append(suggestion)
        return combined


@dataclass(slots=True)
class ExportInvoicesToExcel:
    invoice_repository: InvoiceRepository
    suggestion_repository: AISuggestionRepository
    workbook_builder: InvoiceWorkbookBuilder

    def execute(self, *, owner_id: str) -> bytes:
        invoices = self.invoice_repository.list_for_user(owner_id)
        if not invoices:
            raise NoInvoicesToExportError("No hay facturas para exportar")

        ordered = sorted(invoices, key=lambda item: item.issue_date)
        suggestions_map = {
            invoice.id: self.suggestion_repository.list_for_invoice(invoice.id)
            for invoice in ordered
        }
        return self.workbook_builder.build(ordered, suggestions_map)

