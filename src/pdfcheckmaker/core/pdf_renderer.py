"""HTML-to-PDF rendering."""

from __future__ import annotations

import logging
from pathlib import Path

from pdfcheckmaker.core.exceptions import RenderError

logger = logging.getLogger(__name__)


class PdfRenderer:
    """Render HTML documents to PDF files with WeasyPrint."""

    def render_pdf(
        self, html: str, output_path: Path, base_url: Path | None = None
    ) -> Path:
        """Render HTML to a PDF file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            from weasyprint import HTML

            HTML(string=html, base_url=str(base_url) if base_url else None).write_pdf(
                output_path
            )
        except Exception as exc:
            logger.exception("PDF rendering failed for %s", output_path)
            raise RenderError(f"Failed to render PDF {output_path}: {exc}") from exc
        return output_path
