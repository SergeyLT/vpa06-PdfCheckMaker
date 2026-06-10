"""JSON invoice source."""

from __future__ import annotations

import json

from pdfcheckmaker.core.exceptions import DataSourceError
from pdfcheckmaker.core.models import Invoice, build_invoice
from pdfcheckmaker.datasources.base import DataSource


class JsonSource(DataSource):
    """Load invoices from a JSON file."""

    def load(self) -> list[Invoice]:
        try:
            text = self.path.read_text(encoding="utf-8-sig")
            data = json.loads(self._strip_comment_lines(text))
        except (OSError, json.JSONDecodeError) as exc:
            raise DataSourceError(f"Cannot read JSON file {self.path}: {exc}") from exc

        raw_invoices = data.get("invoices") if isinstance(data, dict) else data
        if not isinstance(raw_invoices, list):
            raise DataSourceError(
                "JSON source must contain a list or an object with an 'invoices' list"
            )
        return [build_invoice(item) for item in raw_invoices]

    @staticmethod
    def _strip_comment_lines(text: str) -> str:
        return "\n".join(
            line for line in text.splitlines() if not line.lstrip().startswith("//")
        )
