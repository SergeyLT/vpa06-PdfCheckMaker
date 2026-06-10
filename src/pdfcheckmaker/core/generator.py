"""Facade used by all interfaces."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

from pdfcheckmaker.core.models import Invoice
from pdfcheckmaker.core.pdf_renderer import PdfRenderer
from pdfcheckmaker.core.qr import make_qr_data_uri
from pdfcheckmaker.templates_engine.loader import TemplateBundle, TemplateLoader

logger = logging.getLogger(__name__)


class InvoiceGenerator:
    """High-level facade for rendering invoice PDFs."""

    def __init__(self, template_loader: TemplateLoader | None = None, renderer: PdfRenderer | None = None) -> None:
        self.template_loader = template_loader or TemplateLoader()
        self.renderer = renderer or PdfRenderer()

    def generate_one(self, invoice: Invoice, template_dir: Path, output_dir: Path) -> Path:
        """Generate a single PDF invoice."""
        bundle = self.template_loader.load(template_dir)
        html = self._render_html(invoice, bundle)
        filename = f"invoice_{self._safe_filename(invoice.invoice_id)}.pdf"
        output_path = output_dir / filename
        logger.info("Generating invoice %s to %s", invoice.invoice_id, output_path)
        return self.renderer.render_pdf(html, output_path, base_url=bundle.directory)

    def generate_many(self, invoices: list[Invoice], template_dir: Path, output_dir: Path) -> list[Path]:
        """Generate several invoices with the same template."""
        return [self.generate_one(invoice, template_dir, output_dir) for invoice in invoices]

    def _render_html(self, invoice: Invoice, bundle: TemplateBundle) -> str:
        bundle.manifest.validate_invoice(invoice)
        context = invoice.template_context()
        context["generated_at"] = datetime.now().strftime("%d.%m.%Y %H:%M")
        context["locale"] = bundle.manifest.locale
        context["font_css"] = self._font_css()
        context["pdf_title"] = f"Invoice {invoice.invoice_id}"
        context["pdf_created"] = datetime.now().isoformat(timespec="seconds")

        qr_settings = bundle.manifest.qr or {}
        source_field = qr_settings.get("source_field", "payment_qr")
        qr_payload = getattr(invoice, source_field, None)
        context["qr_image_base64"] = make_qr_data_uri(qr_payload) if qr_payload else ""
        return bundle.template.render(**context)

    @staticmethod
    def _safe_filename(value: str) -> str:
        return "".join(char if char.isalnum() or char in ("-", "_") else "_" for char in value)

    @staticmethod
    def _font_css() -> str:
        return """
@font-face {
    font-family: 'DejaVu Sans';
    src: local('DejaVu Sans'), local('Roboto');
}
body { font-family: 'DejaVu Sans', 'Roboto', sans-serif; }
"""
