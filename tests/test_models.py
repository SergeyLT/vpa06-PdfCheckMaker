from decimal import Decimal

import pytest

from pdfcheckmaker.core.models import Invoice, LineItem


def test_line_item_sum_is_calculated() -> None:
    item = LineItem(name="Keyboard", quantity=2, price=Decimal("4500.00"))

    assert item.sum == Decimal("9000.00")


def test_invoice_totals_are_calculated() -> None:
    invoice = Invoice(
        invoice_id="INV-1",
        issue_date="15.06.2024",
        seller={"name": "Seller", "inn": "123", "address": "Address"},
        buyer={"name": "Buyer"},
        items=[
            {"name": "A", "quantity": 2, "price": "100.00"},
            {"name": "B", "quantity": 1, "price": "50.00"},
        ],
        discount_percent=10,
        tax_percent=20,
    )

    assert invoice.subtotal == Decimal("250.00")
    assert invoice.discount_amount == Decimal("25.00")
    assert invoice.tax_amount == Decimal("45.00")
    assert invoice.total == Decimal("270.00")


def test_invoice_requires_items() -> None:
    with pytest.raises(Exception):
        Invoice(
            invoice_id="INV-1",
            issue_date="2024-06-15",
            seller={"name": "Seller"},
            buyer={"name": "Buyer"},
            items=[],
        )
