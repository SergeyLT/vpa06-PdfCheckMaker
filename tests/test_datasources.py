from pathlib import Path

from pdfcheckmaker.datasources.csv_source import CsvSource
from pdfcheckmaker.datasources.json_source import JsonSource
from pdfcheckmaker.datasources.registry import default_registry


ROOT = Path(__file__).resolve().parents[1]


def test_csv_source_groups_rows_by_invoice() -> None:
    invoices = CsvSource(ROOT / "data" / "invoices_sample.csv").load()

    assert [invoice.invoice_id for invoice in invoices] == ["INV-2024-001", "INV-2024-002"]
    assert len(invoices[0].items) == 3
    assert invoices[0].total > 0


def test_json_source_loads_invoices() -> None:
    invoices = JsonSource(ROOT / "data" / "invoices_sample.json").load()

    assert len(invoices) == 2
    assert invoices[1].buyer.name == "ООО «ТехноТехно»"


def test_registry_creates_source_by_extension() -> None:
    registry = default_registry()
    source = registry.create(ROOT / "data" / "invoices_sample.json")

    assert isinstance(source, JsonSource)
