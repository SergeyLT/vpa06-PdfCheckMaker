"""Общая логика загрузки данных и генерации PDF."""

from __future__ import annotations

from pathlib import Path

from pdfcheckmaker.core.exceptions import DataSourceError
from pdfcheckmaker.core.generator import InvoiceGenerator
from pdfcheckmaker.core.models import Invoice
from pdfcheckmaker.datasources.registry import DataSourceRegistry, default_registry


def load_invoices(
    data_file: Path, registry: DataSourceRegistry | None = None
) -> list[Invoice]:
    """Загрузить и провалидировать чеки из CSV/JSON-файла."""
    source_registry = registry or default_registry()
    return source_registry.create(data_file).load()


def find_invoice(invoices: list[Invoice], invoice_id: str) -> Invoice:
    """Найти чек по invoice_id."""
    for invoice in invoices:
        if invoice.invoice_id == invoice_id:
            return invoice
    raise DataSourceError(f"Чек с invoice_id {invoice_id!r} не найден")


def generate_invoice_pdfs(
    invoices: list[Invoice],
    template_dir: Path,
    output_dir: Path,
    invoice_id: str | None = None,
    generator: InvoiceGenerator | None = None,
) -> list[Path]:
    """Сгенерировать PDF для одного чека или всего списка."""
    pdf_generator = generator or InvoiceGenerator()
    if invoice_id is None:
        return pdf_generator.generate_many(invoices, template_dir, output_dir)

    invoice = find_invoice(invoices, invoice_id)
    return [pdf_generator.generate_one(invoice, template_dir, output_dir)]


def generate_pdfs_from_data_file(
    data_file: Path,
    template_dir: Path,
    output_dir: Path,
    invoice_id: str | None = None,
    registry: DataSourceRegistry | None = None,
    generator: InvoiceGenerator | None = None,
) -> list[Path]:
    """Загрузить данные из файла и сгенерировать PDF."""
    invoices = load_invoices(data_file, registry=registry)
    return generate_invoice_pdfs(
        invoices,
        template_dir,
        output_dir,
        invoice_id=invoice_id,
        generator=generator,
    )
