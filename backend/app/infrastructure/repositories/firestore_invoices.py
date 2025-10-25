from __future__ import annotations

import logging
from typing import List, Optional
from datetime import date
from decimal import Decimal

from firebase_admin import firestore

from app.domain.invoices import Invoice, InvoiceLine
from app.application.contracts.repositories import InvoiceRepository
from app.infrastructure.services.firebase_admin import initialize_firebase_app

logger = logging.getLogger(__name__)

class FirestoreInvoiceRepository(InvoiceRepository):
    def __init__(self) -> None:
        try:
            app = initialize_firebase_app()
            self.db = firestore.client(app)
            self.invoices_collection = self.db.collection('invoices')
            logger.info("Successfully connected to Firestore - Invoices Collection")
        except Exception as e:
            logger.error(f"Error connecting to Firestore: {e}")
            raise

    def get_by_id(self, invoice_id: str) -> Optional[Invoice]:
        doc = self.invoices_collection.document(invoice_id).get()
        if not doc.exists:
            return None
        data = doc.to_dict()
        
        # Deserialize lines
        lines = []
        for line_data in data.get("lines", []):
            lines.append(InvoiceLine(
                line_id=line_data["line_id"],
                description=line_data["description"],
                quantity=Decimal(str(line_data["quantity"])),
                unit_price=Decimal(str(line_data["unit_price"])),
                line_extension_amount=Decimal(str(line_data["line_extension_amount"])),
            ))
        
        return Invoice(
            id=doc.id,
            owner_id=data["owner_id"],
            external_id=data["external_id"],
            issue_date=date.fromisoformat(data["issue_date"]),
            supplier_name=data["supplier_name"],
            supplier_tax_id=data["supplier_tax_id"],
            customer_name=data["customer_name"],
            customer_tax_id=data["customer_tax_id"],
            currency=data["currency"],
            total_amount=Decimal(str(data["total_amount"])),
            tax_amount=Decimal(str(data["tax_amount"])),
            lines=tuple(lines),
            original_filename=data.get("original_filename", ""),
            raw_xml=data.get("raw_xml", ""),
        )

    def add(self, invoice: Invoice) -> None:
        # Serialize lines
        lines_data = [
            {
                "line_id": line.line_id,
                "description": line.description,
                "quantity": str(line.quantity),
                "unit_price": str(line.unit_price),
                "line_extension_amount": str(line.line_extension_amount),
            }
            for line in invoice.lines
        ]
        
        self.invoices_collection.document(invoice.id).set({
            "owner_id": invoice.owner_id,
            "external_id": invoice.external_id,
            "issue_date": invoice.issue_date.isoformat(),
            "supplier_name": invoice.supplier_name,
            "supplier_tax_id": invoice.supplier_tax_id,
            "customer_name": invoice.customer_name,
            "customer_tax_id": invoice.customer_tax_id,
            "currency": invoice.currency,
            "total_amount": str(invoice.total_amount),
            "tax_amount": str(invoice.tax_amount),
            "lines": lines_data,
            "original_filename": invoice.original_filename,
            "raw_xml": invoice.raw_xml,
        })

    def list_for_user(self, user_id: str) -> List[Invoice]:
        query = self.invoices_collection.where("owner_id", "==", user_id).get()
        invoices = []
        
        for doc in query:
            data = doc.to_dict()
            
            # Deserialize lines
            lines = []
            for line_data in data.get("lines", []):
                lines.append(InvoiceLine(
                    line_id=line_data["line_id"],
                    description=line_data["description"],
                    quantity=Decimal(str(line_data["quantity"])),
                    unit_price=Decimal(str(line_data["unit_price"])),
                    line_extension_amount=Decimal(str(line_data["line_extension_amount"])),
                ))
            
            invoices.append(Invoice(
                id=doc.id,
                owner_id=data["owner_id"],
                external_id=data["external_id"],
                issue_date=date.fromisoformat(data["issue_date"]),
                supplier_name=data["supplier_name"],
                supplier_tax_id=data["supplier_tax_id"],
                customer_name=data["customer_name"],
                customer_tax_id=data["customer_tax_id"],
                currency=data["currency"],
                total_amount=Decimal(str(data["total_amount"])),
                tax_amount=Decimal(str(data["tax_amount"])),
                lines=tuple(lines),
                original_filename=data.get("original_filename", ""),
                raw_xml=data.get("raw_xml", ""),
            ))
        
        return invoices

    def find_by_owner_and_external_id(self, owner_id: str, external_id: str) -> Optional[Invoice]:
        query = self.invoices_collection.where("owner_id", "==", owner_id).where("external_id", "==", external_id).limit(1).get()
        docs = list(query)
        if not docs:
            return None
        
        doc = docs[0]
        data = doc.to_dict()
        
        # Deserialize lines
        lines = []
        for line_data in data.get("lines", []):
            lines.append(InvoiceLine(
                line_id=line_data["line_id"],
                description=line_data["description"],
                quantity=Decimal(str(line_data["quantity"])),
                unit_price=Decimal(str(line_data["unit_price"])),
                line_extension_amount=Decimal(str(line_data["line_extension_amount"])),
            ))
        
        return Invoice(
            id=doc.id,
            owner_id=data["owner_id"],
            external_id=data["external_id"],
            issue_date=date.fromisoformat(data["issue_date"]),
            supplier_name=data["supplier_name"],
            supplier_tax_id=data["supplier_tax_id"],
            customer_name=data["customer_name"],
            customer_tax_id=data["customer_tax_id"],
            currency=data["currency"],
            total_amount=Decimal(str(data["total_amount"])),
            tax_amount=Decimal(str(data["tax_amount"])),
            lines=tuple(lines),
            original_filename=data.get("original_filename", ""),
            raw_xml=data.get("raw_xml", ""),
        )