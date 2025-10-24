from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation

from lxml import etree

from app.domain import InvoiceLine


class UBLInvoiceParser:
    _namespaces = {
        "cbc": "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
        "cac": "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
    }

    def parse(self, xml_bytes: bytes) -> dict[str, object]:
        """Convierte un XML UBL en los campos clave utilizados por el dominio."""

        try:
            root = etree.fromstring(xml_bytes)
        except etree.XMLSyntaxError as exc:
            raise ValueError("No fue posible leer el XML proporcionado") from exc

        raw_xml = xml_bytes.decode("utf-8", errors="ignore")
        get_text = lambda path: self._read_text(root, path)

        external_id = get_text("cbc:ID")
        issue_date_text = get_text("cbc:IssueDate")
        if not issue_date_text:
            raise ValueError("El XML no contiene la fecha de emisión")

        try:
            issue_date = date.fromisoformat(issue_date_text)
        except ValueError as exc:
            raise ValueError("La fecha de emisión no tiene el formato esperado") from exc

        supplier_name = self._first_non_empty(
            get_text("cac:AccountingSupplierParty/cac:Party/cac:PartyName/cbc:Name"),
            get_text("cac:AccountingSupplierParty/cac:Party/cac:PartyLegalEntity/cbc:RegistrationName"),
        )
        supplier_tax_id = self._first_non_empty(
            get_text("cac:AccountingSupplierParty/cac:Party/cac:PartyTaxScheme/cbc:CompanyID"),
            get_text("cac:AccountingSupplierParty/cac:Party/cac:PartyLegalEntity/cbc:CompanyID"),
        )
        customer_name = self._first_non_empty(
            get_text("cac:AccountingCustomerParty/cac:Party/cac:PartyName/cbc:Name"),
            get_text("cac:AccountingCustomerParty/cac:Party/cac:PartyLegalEntity/cbc:RegistrationName"),
        )
        customer_tax_id = self._first_non_empty(
            get_text("cac:AccountingCustomerParty/cac:Party/cac:PartyTaxScheme/cbc:CompanyID"),
            get_text("cac:AccountingCustomerParty/cac:Party/cac:PartyLegalEntity/cbc:CompanyID"),
        )

        totals_element = root.find("cac:LegalMonetaryTotal/cbc:PayableAmount", namespaces=self._namespaces)
        if totals_element is None or totals_element.text is None:
            raise ValueError("No se encontró el total de la factura")

        currency = totals_element.get("currencyID") or get_text("cbc:DocumentCurrencyCode")
        total_amount = self._to_decimal(totals_element.text)

        tax_element = root.find("cac:TaxTotal/cbc:TaxAmount", namespaces=self._namespaces)
        tax_amount = self._to_decimal(tax_element.text) if tax_element is not None and tax_element.text else Decimal("0")

        lines: list[InvoiceLine] = []
        for line in root.findall("cac:InvoiceLine", namespaces=self._namespaces):
            line_id = self._read_text(line, "cbc:ID") or str(len(lines) + 1)
            description = self._first_non_empty(
                self._read_text(line, "cac:Item/cbc:Description"),
                self._read_text(line, "cac:Item/cac:ItemIdentification/cbc:ID"),
            )
            quantity = self._to_decimal(self._read_text(line, "cbc:InvoicedQuantity"))
            unit_price = self._to_decimal(self._read_text(line, "cac:Price/cbc:PriceAmount"))
            line_total = self._to_decimal(self._read_text(line, "cbc:LineExtensionAmount"))
            lines.append(
                InvoiceLine(
                    line_id=line_id,
                    description=description,
                    quantity=quantity,
                    unit_price=unit_price,
                    line_extension_amount=line_total,
                )
            )

        if not lines:
            raise ValueError("No se encontraron líneas de producto en la factura")

        return {
            "external_id": external_id,
            "issue_date": issue_date,
            "supplier": {"name": supplier_name, "tax_id": supplier_tax_id},
            "customer": {"name": customer_name, "tax_id": customer_tax_id},
            "currency": currency,
            "total_amount": total_amount,
            "tax_amount": tax_amount,
            "lines": lines,
            "raw_xml": raw_xml,
        }

    def _read_text(self, element: etree._Element, path: str) -> str:
        node = element.find(path, namespaces=self._namespaces)
        if node is not None and node.text is not None:
            return node.text.strip()
        return ""

    def _first_non_empty(self, *values: str) -> str:
        for value in values:
            if value:
                return value
        return ""

    def _to_decimal(self, value: str) -> Decimal:
        try:
            return Decimal(value.strip()) if value else Decimal("0")
        except (InvalidOperation, AttributeError) as exc:
            raise ValueError("No fue posible interpretar un valor numérico") from exc
