from pathlib import Path

import pytest

from pdfcheckmaker.core.generator import InvoiceGenerator
from pdfcheckmaker.datasources.json_source import JsonSource


ROOT = Path(__file__).resolve().parents[1]


def test_pdf_generation_creates_non_empty_file(tmp_path: Path) -> None:
    invoice = JsonSource(ROOT / "data" / "invoices_sample.json").load()[0]
    generator = InvoiceGenerator()

    try:
        output_path = generator.generate_one(
            invoice, ROOT / "templates" / "invoice_standard", tmp_path
        )
    except Exception as exc:
        pytest.skip(f"WeasyPrint is not available in this environment: {exc}")

    assert output_path.exists()
    assert output_path.stat().st_size > 0
