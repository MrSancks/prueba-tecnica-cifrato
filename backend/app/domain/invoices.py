from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Iterable
import uuid


@dataclass(slots=True)
class InvoiceLine:
    line_id: str
    description: str
    quantity: Decimal
    unit_price: Decimal
    line_extension_amount: Decimal


@dataclass(slots=True)
class Invoice:
    id: str
    owner_id: str
    external_id: str
    issue_date: date
    supplier_name: str
    supplier_tax_id: str
    customer_name: str
    customer_tax_id: str
    currency: str
    total_amount: Decimal
    tax_amount: Decimal
    lines: tuple[InvoiceLine, ...] = field(default_factory=tuple)
    original_filename: str = ""
    raw_xml: str = ""

    @classmethod
    def create(
        cls,
        *,
        owner_id: str,
        external_id: str,
        issue_date: date,
        supplier_name: str,
        supplier_tax_id: str,
        customer_name: str,
        customer_tax_id: str,
        currency: str,
        total_amount: Decimal,
        tax_amount: Decimal,
        lines: Iterable[InvoiceLine],
        original_filename: str,
        raw_xml: str,
    ) -> "Invoice":
        line_items = tuple(lines)
        return cls(
            id=str(uuid.uuid4()),
            owner_id=owner_id,
            external_id=external_id,
            issue_date=issue_date,
            supplier_name=supplier_name,
            supplier_tax_id=supplier_tax_id,
            customer_name=customer_name,
            customer_tax_id=customer_tax_id,
            currency=currency,
            total_amount=total_amount,
            tax_amount=tax_amount,
            lines=line_items,
            original_filename=original_filename,
            raw_xml=raw_xml,
        )
