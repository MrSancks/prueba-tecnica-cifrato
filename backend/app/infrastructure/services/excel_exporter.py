from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from io import BytesIO
from typing import Any, Iterable
from xml.sax.saxutils import escape
from zipfile import ZIP_DEFLATED, ZipFile

from app.domain import AISuggestion, Invoice

try:  # pragma: no cover - dependencia opcional
    import pandas as pd  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - degradación controlada
    pd = None  # type: ignore[assignment]


@dataclass(slots=True)
class SpreadsheetInvoiceWorkbookBuilder:
    engine: str = "openpyxl"
    puc_catalog_generator: Any = None  # PUCCatalogGenerator opcional

    def build(
        self,
        invoices: list[Invoice],
        suggestions_map: dict[str, list[AISuggestion]],
    ) -> bytes:
        if pd is not None:
            return self._build_with_pandas(invoices, suggestions_map)
        return self._build_with_minimal_writer(invoices, suggestions_map)

    def _build_with_pandas(
        self,
        invoices: list[Invoice],
        suggestions_map: dict[str, list[AISuggestion]],
    ) -> bytes:
        buffer = BytesIO()

        # Hoja 1: Resumen con factura + sugerencias PUC
        resumen_rows = list(self._build_resumen_rows(invoices, suggestions_map))
        
        # Hoja 2: Productos (líneas de detalle)
        productos_rows = list(self._build_lines_rows(invoices))

        with pd.ExcelWriter(buffer, engine=self.engine) as writer:  # type: ignore[arg-type]
            pd.DataFrame(resumen_rows).to_excel(writer, sheet_name="Resumen", index=False)  # type: ignore[call-arg]
            pd.DataFrame(productos_rows).to_excel(writer, sheet_name="Productos", index=False)  # type: ignore[call-arg]

        return buffer.getvalue()

    def _build_with_minimal_writer(
        self,
        invoices: list[Invoice],
        suggestions_map: dict[str, list[AISuggestion]],
    ) -> bytes:
        # Hoja 1: Resumen
        resumen_sheet = [
            [
                "Factura interna",
                "Consecutivo externo",
                "Fecha",
                "Proveedor",
                "NIT proveedor",
                "Cliente",
                "NIT cliente",
                "Moneda",
                "Subtotal",
                "Impuestos",
                "Total",
                "Código PUC",
                "Justificación",
                "Confianza",
            ]
        ]
        for row in self._build_resumen_rows(invoices, suggestions_map):
            resumen_sheet.append(
                [
                    row["Factura interna"],
                    row["Consecutivo externo"],
                    row["Fecha"],
                    row["Proveedor"],
                    row["NIT proveedor"],
                    row["Cliente"],
                    row["NIT cliente"],
                    row["Moneda"],
                    row["Subtotal"],
                    row["Impuestos"],
                    row["Total"],
                    row["Código PUC"],
                    row["Justificación"],
                    row["Confianza"],
                ]
            )

        # Hoja 2: Productos
        productos_sheet = [
            [
                "Factura interna",
                "Consecutivo externo",
                "ID producto",
                "Descripción",
                "Cantidad",
                "Precio unitario",
                "Subtotal",
            ]
        ]
        for row in self._build_lines_rows(invoices):
            productos_sheet.append(
                [
                    row["Factura interna"],
                    row["Consecutivo externo"],
                    row["ID producto"],
                    row["Descripción"],
                    row["Cantidad"],
                    row["Precio unitario"],
                    row["Subtotal"],
                ]
            )

        timestamp = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        buffer = BytesIO()
        with ZipFile(buffer, "w", ZIP_DEFLATED) as archive:
            archive.writestr("[Content_Types].xml", self._content_types_xml())
            archive.writestr("_rels/.rels", self._rels_xml())
            archive.writestr("docProps/core.xml", self._core_xml(timestamp))
            archive.writestr("docProps/app.xml", self._app_xml())
            archive.writestr("xl/_rels/workbook.xml.rels", self._workbook_rels_xml())
            archive.writestr("xl/workbook.xml", self._workbook_xml())
            archive.writestr("xl/styles.xml", self._styles_xml())
            archive.writestr("xl/worksheets/sheet1.xml", self._sheet_xml(resumen_sheet))
            archive.writestr("xl/worksheets/sheet2.xml", self._sheet_xml(productos_sheet))

        return buffer.getvalue()

    def _build_resumen_rows(
        self,
        invoices: Iterable[Invoice],
        suggestions_map: dict[str, list[AISuggestion]],
    ) -> Iterable[dict[str, object]]:
        """
        Combina datos de factura con sugerencias PUC seleccionadas.
        Una fila por factura con su código PUC.
        """
        for invoice in invoices:
            subtotal = invoice.total_amount - invoice.tax_amount
            
            # Buscar la sugerencia seleccionada para esta factura
            suggestions = suggestions_map.get(invoice.id, [])
            selected = next((s for s in suggestions if s.is_selected), None)
            
            yield {
                "Factura interna": invoice.id,
                "Consecutivo externo": invoice.external_id,
                "Fecha": invoice.issue_date.isoformat(),
                "Proveedor": invoice.supplier_name,
                "NIT proveedor": invoice.supplier_tax_id,
                "Cliente": invoice.customer_name,
                "NIT cliente": invoice.customer_tax_id,
                "Moneda": invoice.currency,
                "Subtotal": float(subtotal),
                "Impuestos": float(invoice.tax_amount),
                "Total": float(invoice.total_amount),
                "Código PUC": selected.account_code if selected else "",
                "Justificación": selected.rationale if selected else "",
                "Confianza": float(selected.confidence) if selected else 0.0,
            }

    def _build_lines_rows(self, invoices: Iterable[Invoice]) -> Iterable[dict[str, object]]:
        for invoice in invoices:
            for line in invoice.lines:
                yield {
                    "Factura interna": invoice.id,
                    "Consecutivo externo": invoice.external_id,
                    "ID producto": line.line_id,
                    "Descripción": line.description,
                    "Cantidad": float(line.quantity),
                    "Precio unitario": float(line.unit_price),
                    "Subtotal": float(line.line_extension_amount),
                }

    def _sheet_xml(self, rows: list[list[object]]) -> str:
        body: list[str] = []
        for row_index, row in enumerate(rows, start=1):
            cells: list[str] = []
            for column_index, value in enumerate(row, start=1):
                cell_ref = f"{self._column_letter(column_index)}{row_index}"
                if self._is_number(value):
                    cells.append(f'<c r="{cell_ref}"><v>{value}</v></c>')
                else:
                    text = "" if value is None else escape(str(value))
                    cells.append(
                        f'<c r="{cell_ref}" t="inlineStr"><is><t>{text}</t></is></c>'
                    )
            body.append(f"<row r=\"{row_index}\">{''.join(cells)}</row>")

        return (
            "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
            "<worksheet xmlns=\"http://schemas.openxmlformats.org/spreadsheetml/2006/main\">"
            f"<sheetData>{''.join(body)}</sheetData>"
            "</worksheet>"
        )

    def _content_types_xml(self) -> str:
        return (
            "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
            "<Types xmlns=\"http://schemas.openxmlformats.org/package/2006/content-types\">"
            "<Default Extension=\"rels\" ContentType=\"application/vnd.openxmlformats-package.relationships+xml\"/>"
            "<Default Extension=\"xml\" ContentType=\"application/xml\"/>"
            "<Override PartName=\"/xl/workbook.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml\"/>"
            "<Override PartName=\"/xl/worksheets/sheet1.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml\"/>"
            "<Override PartName=\"/xl/worksheets/sheet2.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml\"/>"
            "<Override PartName=\"/xl/styles.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml\"/>"
            "<Override PartName=\"/docProps/core.xml\" ContentType=\"application/vnd.openxmlformats-package.core-properties+xml\"/>"
            "<Override PartName=\"/docProps/app.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.extended-properties+xml\"/>"
            "</Types>"
        )

    def _rels_xml(self) -> str:
        return (
            "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
            "<Relationships xmlns=\"http://schemas.openxmlformats.org/package/2006/relationships\">"
            "<Relationship Id=\"rId1\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument\" Target=\"xl/workbook.xml\"/>"
            "</Relationships>"
        )

    def _workbook_xml(self) -> str:
        return (
            "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
            "<workbook xmlns=\"http://schemas.openxmlformats.org/spreadsheetml/2006/main\" xmlns:r=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships\">"
            "<sheets>"
            "<sheet name=\"Resumen\" sheetId=\"1\" r:id=\"rId1\"/>"
            "<sheet name=\"Productos\" sheetId=\"2\" r:id=\"rId2\"/>"
            "</sheets>"
            "</workbook>"
        )

    def _workbook_rels_xml(self) -> str:
        return (
            "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
            "<Relationships xmlns=\"http://schemas.openxmlformats.org/package/2006/relationships\">"
            "<Relationship Id=\"rId1\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet\" Target=\"worksheets/sheet1.xml\"/>"
            "<Relationship Id=\"rId2\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet\" Target=\"worksheets/sheet2.xml\"/>"
            "<Relationship Id=\"rId3\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles\" Target=\"styles.xml\"/>"
            "</Relationships>"
        )

    def _styles_xml(self) -> str:
        return (
            "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
            "<styleSheet xmlns=\"http://schemas.openxmlformats.org/spreadsheetml/2006/main\">"
            "<fonts count=\"1\"><font><sz val=\"11\"/><color theme=\"1\"/><name val=\"Calibri\"/></font></fonts>"
            "<fills count=\"1\"><fill><patternFill patternType=\"none\"/></fill></fills>"
            "<borders count=\"1\"><border><left/><right/><top/><bottom/><diagonal/></border></borders>"
            "<cellStyleXfs count=\"1\"><xf numFmtId=\"0\" fontId=\"0\" fillId=\"0\" borderId=\"0\"/></cellStyleXfs>"
            "<cellXfs count=\"1\"><xf numFmtId=\"0\" fontId=\"0\" fillId=\"0\" borderId=\"0\" xfId=\"0\"/></cellXfs>"
            "</styleSheet>"
        )

    def _core_xml(self, timestamp: str) -> str:
        return (
            "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
            "<cp:coreProperties xmlns:cp=\"http://schemas.openxmlformats.org/package/2006/metadata/core-properties\" xmlns:dc=\"http://purl.org/dc/elements/1.1/\" xmlns:dcterms=\"http://purl.org/dc/terms/\" xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\">"
            "<dc:creator>Cifrato Backend</dc:creator>"
            "<cp:lastModifiedBy>Cifrato Backend</cp:lastModifiedBy>"
            f"<dcterms:created xsi:type=\"dcterms:W3CDTF\">{timestamp}</dcterms:created>"
            f"<dcterms:modified xsi:type=\"dcterms:W3CDTF\">{timestamp}</dcterms:modified>"
            "</cp:coreProperties>"
        )

    def _app_xml(self) -> str:
        return (
            "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
            "<Properties xmlns=\"http://schemas.openxmlformats.org/officeDocument/2006/extended-properties\" xmlns:vt=\"http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes\">"
            "<Application>Python</Application>"
            "</Properties>"
        )

    def _column_letter(self, index: int) -> str:
        result = ""
        while index:
            index, remainder = divmod(index - 1, 26)
            result = chr(65 + remainder) + result
        return result or "A"

    def _is_number(self, value: object) -> bool:
        if isinstance(value, (int, float)):
            return True
        if isinstance(value, Decimal):
            return True
        return False
