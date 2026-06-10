"""Pydantic models for invoices."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from pdfcheckmaker.core.exceptions import InvoiceValidationError


Money = Decimal
TWOPLACES = Decimal("0.01")


def quantize_money(value: Decimal) -> Decimal:
    """Round money values to two decimal places."""
    return value.quantize(TWOPLACES, rounding=ROUND_HALF_UP)


class Party(BaseModel):
    """Seller or buyer details."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(..., min_length=1)
    inn: str | None = None
    address: str | None = None


class LineItem(BaseModel):
    """One invoice line item."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(..., min_length=1)
    quantity: Decimal = Field(..., gt=0)
    price: Money = Field(..., ge=0)
    sum: Money | None = None

    @model_validator(mode="after")
    def calculate_sum(self) -> "LineItem":
        """Calculate line amount in code, never in the template."""
        self.sum = quantize_money(self.quantity * self.price)
        return self


class Invoice(BaseModel):
    """Invoice with calculated totals."""

    model_config = ConfigDict(str_strip_whitespace=True)

    invoice_id: str = Field(..., min_length=1)
    issue_date: date
    seller: Party
    buyer: Party
    items: list[LineItem] = Field(..., min_length=1)
    discount_percent: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    tax_percent: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    notes: str | None = None
    payment_qr: str | None = None
    subtotal: Money = Decimal("0")
    discount_amount: Money = Decimal("0")
    tax_amount: Money = Decimal("0")
    total: Money = Decimal("0")

    @field_validator("issue_date", mode="before")
    @classmethod
    def parse_issue_date(cls, value: Any) -> date:
        """Accept ISO dates and Russian-style dates from the examples."""
        if isinstance(value, date):
            return value
        if isinstance(value, str):
            for fmt in ("%Y-%m-%d", "%d.%m.%Y"):
                try:
                    return datetime.strptime(value, fmt).date()
                except ValueError:
                    continue
        raise ValueError("issue_date must be YYYY-MM-DD or DD.MM.YYYY")

    @model_validator(mode="after")
    def calculate_totals(self) -> "Invoice":
        """Calculate subtotal, discount, tax and grand total."""
        subtotal = sum((item.sum or Decimal("0")) for item in self.items)
        discount = subtotal * self.discount_percent / Decimal("100")
        taxable = subtotal - discount
        tax = taxable * self.tax_percent / Decimal("100")

        self.subtotal = quantize_money(subtotal)
        self.discount_amount = quantize_money(discount)
        self.tax_amount = quantize_money(tax)
        self.total = quantize_money(taxable + tax)
        return self

    def template_context(self) -> dict[str, Any]:
        """Return a Jinja2-friendly context."""
        data = self.model_dump(mode="json")
        data["issue_date"] = self.issue_date.strftime("%d.%m.%Y")
        return data


def build_invoice(data: dict[str, Any]) -> Invoice:
    """Build an invoice and convert Pydantic errors to application errors."""
    try:
        return Invoice.model_validate(data)
    except Exception as exc:
        invoice_id = data.get("invoice_id", "<unknown>")
        raise InvoiceValidationError(f"Invalid invoice {invoice_id}: {exc}") from exc
