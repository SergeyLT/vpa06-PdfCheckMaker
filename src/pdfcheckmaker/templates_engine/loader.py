"""Jinja2 template loader."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined, Template, select_autoescape

from pdfcheckmaker.core.exceptions import TemplateError
from pdfcheckmaker.templates_engine.manifest import TemplateManifest


@dataclass(frozen=True)
class TemplateBundle:
    """Loaded template and its metadata."""

    directory: Path
    manifest: TemplateManifest
    template: Template


class TemplateLoader:
    """Load template directories containing manifest.yaml and template.html."""

    def load(self, template_dir: Path) -> TemplateBundle:
        """Load a template directory."""
        manifest_path = template_dir / "manifest.yaml"
        if not manifest_path.exists():
            raise TemplateError(f"Template directory {template_dir} has no manifest.yaml")

        manifest = TemplateManifest.from_file(manifest_path)
        template_path = template_dir / manifest.template_file
        if not template_path.exists():
            raise TemplateError(f"Template file {template_path} does not exist")

        environment = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=select_autoescape(("html", "xml")),
            undefined=StrictUndefined,
        )
        template = environment.get_template(manifest.template_file)
        return TemplateBundle(directory=template_dir, manifest=manifest, template=template)


def discover_templates(root: Path) -> list[Path]:
    """Find template directories under a root directory."""
    if not root.exists():
        return []
    return sorted(path.parent for path in root.rglob("manifest.yaml"))
