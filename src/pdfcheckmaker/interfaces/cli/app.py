"""Interactive command line application."""

from __future__ import annotations

import logging
import os
import platform
import subprocess
from pathlib import Path

import questionary

from pdfcheckmaker.core.generator import InvoiceGenerator
from pdfcheckmaker.datasources.registry import default_registry
from pdfcheckmaker.templates_engine.loader import TemplateLoader, discover_templates

logger = logging.getLogger(__name__)

GENERATE_ALL_LABEL = "Сгенерировать все чеки"


def main() -> None:
    """Run the interactive CLI."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    project_root = Path.cwd()
    data_dir = project_root / "data"
    templates_dir = project_root / "templates"
    output_dir = project_root / "output"

    registry = default_registry()
    data_files = discover_data_files(data_dir, registry.supported_extensions())
    template_dirs = discover_templates(templates_dir)

    if not data_files:
        raise SystemExit(f"Файлы данных не найдены в {data_dir}")
    if not template_dirs:
        raise SystemExit(f"Шаблоны не найдены в {templates_dir}")

    data_file = Path(
        questionary.select(
            "Выберите источник данных:", choices=[str(path) for path in data_files]
        ).ask()
    )
    template_dir = Path(
        questionary.select(
            "Выберите шаблон:", choices=[str(path) for path in template_dirs]
        ).ask()
    )

    invoices = registry.create(data_file).load()
    invoice_map = {invoice.invoice_id: invoice for invoice in invoices}
    choices = [GENERATE_ALL_LABEL] + list(invoice_map)
    selected = questionary.select("Выберите чек:", choices=choices).ask()

    generator = InvoiceGenerator(template_loader=TemplateLoader())
    if selected == GENERATE_ALL_LABEL:
        paths = generator.generate_many(invoices, template_dir, output_dir)
        logger.info("Создано PDF-файлов: %s. Папка: %s", len(paths), output_dir)
        return

    invoice = invoice_map[str(selected)]
    output_path = generator.generate_one(invoice, template_dir, output_dir)
    logger.info("PDF создан: %s", output_path)
    open_file(output_path)


def discover_data_files(root: Path, extensions: tuple[str, ...]) -> list[Path]:
    """Find supported data files."""
    if not root.exists():
        return []
    return sorted(
        path
        for path in root.iterdir()
        if path.is_file() and path.suffix.lower() in extensions
    )


def open_file(path: Path) -> None:
    """Open a generated PDF with the system default program."""
    system = platform.system()
    if system == "Windows":
        os.startfile(path)  # type: ignore[attr-defined]
    elif system == "Darwin":
        subprocess.run(["open", str(path)], check=False)
    else:
        subprocess.run(["xdg-open", str(path)], check=False)
