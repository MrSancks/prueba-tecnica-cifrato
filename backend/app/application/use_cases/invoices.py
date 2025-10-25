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

        # Prioridad 1: Intentar generar con IA
        ai_payload = self.ai_service.generate_suggestions(self._serialize_invoice(invoice))
        ai_suggestions = self._coerce_ai_suggestions(ai_payload)
        
        # Si IA generó sugerencias, usarlas
        if ai_suggestions:
            self.suggestion_repository.replace_for_invoice(invoice.id, ai_suggestions)
            return ai_suggestions
        
        # Prioridad 2: Fallback genérico si IA no está disponible
        fallback_suggestions = self._build_generic_fallback(invoice)
        self.suggestion_repository.replace_for_invoice(invoice.id, fallback_suggestions)
        return fallback_suggestions

    def _build_generic_fallback(self, invoice: Invoice) -> list[AISuggestion]:
        """
        Fallback genérico cuando la IA no está disponible.
        NO asume tipo de negocio específico - solo proporciona sugerencia básica
        para que el contador pueda clasificar manualmente.
        """
        # Sugerencia genérica que funciona para cualquier tipo de factura
        return [
            AISuggestion(
                account_code="",  # Vacío - el usuario debe completar
                rationale=(
                    "Servicio de IA no disponible. Por favor, clasifique manualmente esta factura según su plan contable. "
                    f"Proveedor: {invoice.supplier_name}. "
                    f"Descripción de líneas: {', '.join(line.description for line in invoice.lines[:3])}."
                ),
                confidence=0.0,  # Confianza 0 indica que requiere revisión obligatoria
                source="fallback",
            )
        ]

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
        """
        Convierte la respuesta raw de la IA en objetos AISuggestion.
        Soporta tanto formato agregado como por línea.
        """
        suggestions: list[AISuggestion] = []
        for item in raw:
            code = str(item.get("account_code", "")).strip()
            if not code:
                continue
            
            # Construir rationale incluyendo número de línea si está presente
            line_number = item.get("line_number")
            rationale_base = str(item.get("rationale", "Sugerencia generada por el modelo de IA")).strip()
            
            if line_number:
                rationale = f"Línea {line_number}: {rationale_base}"
            else:
                rationale = rationale_base
            
            try:
                confidence = float(item.get("confidence", 0.5))
            except (TypeError, ValueError):
                confidence = 0.5
            
            suggestions.append(
                AISuggestion(
                    account_code=code,
                    rationale=rationale,
                    confidence=confidence,
                    source="ai",
                    line_number=int(line_number) if line_number else None,
                    is_selected=False,
                )
            )
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
            invoice.id: self._get_or_auto_select_suggestion(invoice.id)
            for invoice in ordered
        }
        return self.workbook_builder.build(ordered, suggestions_map)
    
    def _get_or_auto_select_suggestion(self, invoice_id: str) -> list[AISuggestion]:
        """
        Para cada factura:
        1. Si tiene sugerencia seleccionada, usar esa
        2. Si no, auto-seleccionar la de mayor confianza
        3. En caso de empate en confianza, elegir la más clara (rationale más corto)
        """
        suggestions = self.suggestion_repository.list_for_invoice(invoice_id)
        
        if not suggestions:
            return []
        
        # Verificar si ya hay una seleccionada
        selected = [s for s in suggestions if s.is_selected]
        if selected:
            return selected
        
        # Auto-seleccionar: mayor confianza
        max_confidence = max(s.confidence for s in suggestions)
        top_candidates = [s for s in suggestions if s.confidence == max_confidence]
        
        if len(top_candidates) == 1:
            # Una ganadora clara
            winner = top_candidates[0]
        else:
            # Empate en confianza: elegir la más clara (rationale más corto y específico)
            top_candidates.sort(key=lambda s: len(s.rationale))
            winner = top_candidates[0]
        
        # Marcar como seleccionada (para la próxima exportación)
        # Nota: Esto es opcional - podríamos solo usarla sin persistir la selección
        return [winner]


@dataclass(slots=True)
class InvoiceListItem:
    invoice: Invoice
    status: str


@dataclass(slots=True)
class InvoiceDetailItem:
    invoice: Invoice
    status: str


@dataclass(slots=True)
class ListInvoices:
    invoice_repository: InvoiceRepository
    suggestion_repository: AISuggestionRepository

    def execute(self, *, owner_id: str) -> list[InvoiceListItem]:
        invoices = self.invoice_repository.list_for_user(owner_id)
        ordered = sorted(invoices, key=lambda item: item.issue_date, reverse=True)
        result: list[InvoiceListItem] = []
        for invoice in ordered:
            suggestions = self.suggestion_repository.list_for_invoice(invoice.id)
            status = "procesada" if suggestions else "pendiente"
            result.append(InvoiceListItem(invoice=invoice, status=status))
        return result


@dataclass(slots=True)
class GetInvoiceDetail:
    invoice_repository: InvoiceRepository
    suggestion_repository: AISuggestionRepository

    def execute(self, *, owner_id: str, invoice_id: str) -> InvoiceDetailItem:
        invoice = self.invoice_repository.get_by_id(invoice_id)
        if invoice is None or invoice.owner_id != owner_id:
            raise InvoiceNotFoundError("La factura no existe para el usuario indicado")

        suggestions = self.suggestion_repository.list_for_invoice(invoice.id)
        status = "procesada" if suggestions else "pendiente"
        return InvoiceDetailItem(invoice=invoice, status=status)

