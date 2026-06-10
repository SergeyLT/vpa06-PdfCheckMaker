"""CSV invoice source."""

from __future__ import annotations

import csv
from collections import OrderedDict
from decimal import Decimal
from pathlib import Path
from typing import Any

from pdfcheckmaker.core.exceptions import DataSourceError
from pdfcheckmaker.core.models import Invoice, build_invoice
from pdfcheckmaker.datasources.base import DataSource


class CsvSource(DataSource):
    """Load invoices from CSV where each row is one line item."""

    def load(self) -> list[Invoice]:
        try:
            with self.path.open("r", encoding="utf-8-sig", newline="") as file:
                rows = list(csv.DictReader(file))
        except OSError as exc:
            raise DataSourceError(f"Cannot read CSV file {self.path}: {exc}") from exc

        grouped: OrderedDict[str, dict[str, Any]] = OrderedDict()
        for row_number, row in enumerate(rows, start=2):
            invoice_id = (row.get("invoice_id") or "").strip()
            if not invoice_id:
                raise DataSourceError(f"CSV row {row_number}: missing invoice_id")

            invoice = grouped.setdefault(
                invoice_id,
                {
                    "invoice_id": invoice_id,
                    "issue_date": row.get("issue_date"),
                    "seller": {
                        "name": row.get("seller_name"),
                        "inn": row.get("seller_inn") or None,
                        "address": row.get("seller_address") or None,
                    },
                    "buyer": {
                        "name": row.get("buyer_name"),
                        "inn": row.get("buyer_inn") or None,
                        "address": row.get("buyer_address") or None,
                    },
                    "discount_percent": self._decimal_or_zero(row.get("discount_percent")),
                    "tax_percent": self._decimal_or_zero(row.get("tax_percent")),
                    "notes": row.get("notes") or None,
                    "payment_qr": row.get("payment_qr") or None,
                    "items": [],
                },
            )
            invoice["items"].append(
                {
                    "name": row.get("item_name"),
                    "quantity": self._required_decimal(row, "item_quantity", row_number),
                    "price": self._required_decimal(row, "item_price", row_number),
                }
            )

        return [build_invoice(invoice) for invoice in grouped.values()]

    @staticmethod
    def _decimal_or_zero(value: str | None) -> Decimal:
        return Decimal(value) if value not in (None, "") else Decimal("0")

    @staticmethod
    def _required_decimal(row: dict[str, str | None], field: str, row_number: int) -> Decimal:
        value = row.get(field)
        if value in (None, ""):
            raise DataSourceError(f"CSV row {row_number}: missing {field}")
        return Decimal(value)
