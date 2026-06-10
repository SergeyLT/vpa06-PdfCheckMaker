from pathlib import Path

import pytest

from pdfcheckmaker.core.exceptions import DataSourceError
from pdfcheckmaker.core.generator import InvoiceGenerator
from pdfcheckmaker.datasources.registry import default_registry
from pdfcheckmaker.services.generation import (
    find_invoice,
    generate_invoice_pdfs,
    generate_pdfs_from_data_file,
    load_invoices,
)


ROOT = Path(__file__).resolve().parents[1]


class FakeRenderer:
    def render_pdf(
        self, html: str, output_path: Path, base_url: Path | None = None
    ) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(html, encoding="utf-8")
        return output_path


def test_load_invoices_uses_registry() -> None:
    invoices = load_invoices(
        ROOT / "data" / "invoices_sample.json", registry=default_registry()
    )

    assert [invoice.invoice_id for invoice in invoices] == [
        "INV-2024-001",
        "INV-2024-002",
    ]


def test_find_invoice_reports_missing_id() -> None:
    invoices = load_invoices(ROOT / "data" / "invoices_sample.json")

    with pytest.raises(DataSourceError, match="NOT-FOUND"):
        find_invoice(invoices, "NOT-FOUND")


def test_generate_invoice_pdfs_can_generate_one_invoice(tmp_path: Path) -> None:
    invoices = load_invoices(ROOT / "data" / "invoices_sample.json")
    generator = InvoiceGenerator(renderer=FakeRenderer())

    paths = generate_invoice_pdfs(
        invoices,
        ROOT / "templates" / "invoice_standard",
        tmp_path,
        invoice_id="INV-2024-002",
        generator=generator,
    )

    assert [path.name for path in paths] == ["invoice_INV-2024-002.pdf"]
    assert paths[0].read_text(encoding="utf-8")


def test_generate_pdfs_from_data_file_can_generate_all(tmp_path: Path) -> None:
    generator = InvoiceGenerator(renderer=FakeRenderer())

    paths = generate_pdfs_from_data_file(
        ROOT / "data" / "invoices_sample.csv",
        ROOT / "templates" / "invoice_standard",
        tmp_path,
        generator=generator,
    )

    assert [path.name for path in paths] == [
        "invoice_INV-2024-001.pdf",
        "invoice_INV-2024-002.pdf",
    ]
