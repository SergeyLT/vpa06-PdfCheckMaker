"""Template manifest model and validation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field

from pdfcheckmaker.core.exceptions import TemplateError
from pdfcheckmaker.core.models import Invoice


class TemplateManifest(BaseModel):
    """HTML template manifest loaded from manifest.yaml."""

    model_config = ConfigDict(populate_by_name=True)

    name: str
    title: str | None = None
    description: str | None = None
    version: str | None = None
    template_file: str = "template.html"
    required_fields: list[str] = Field(default_factory=list)
    optional_fields: list[str] = Field(default_factory=list)
    computed_fields: list[str] = Field(default_factory=list)
    schema_: dict[str, Any] = Field(default_factory=dict, alias="schema")
    locale: dict[str, Any] = Field(
        default_factory=lambda: {"currency": "RUB", "currency_symbol": "RUB"}
    )
    qr: dict[str, Any] | None = None

    @classmethod
    def from_file(cls, path: Path) -> "TemplateManifest":
        """Load and validate a manifest file."""
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            return cls.model_validate(data)
        except Exception as exc:
            raise TemplateError(f"Invalid template manifest {path}: {exc}") from exc

    def validate_invoice(self, invoice: Invoice) -> None:
        """Ensure invoice data satisfies this manifest."""
        data = invoice.model_dump()
        missing = [
            field for field in self.required_fields if not self._has_value(data, field)
        ]

        for object_name, rules in self.schema_.items():
            required = rules.get("required", []) if isinstance(rules, dict) else []
            if object_name == "items":
                for index, item in enumerate(data.get("items") or [], start=1):
                    for field in required:
                        if not self._has_value(item, field):
                            missing.append(f"items[{index}].{field}")
            else:
                nested = data.get(object_name)
                for field in required:
                    if not isinstance(nested, dict) or not self._has_value(
                        nested, field
                    ):
                        missing.append(f"{object_name}.{field}")

        if missing:
            raise TemplateError(
                f"Invoice {invoice.invoice_id} does not satisfy template {self.name}. "
                f"Missing fields: {', '.join(missing)}"
            )

    @staticmethod
    def _has_value(data: dict[str, Any], dotted_path: str) -> bool:
        current: Any = data
        for part in dotted_path.split("."):
            if not isinstance(current, dict) or part not in current:
                return False
            current = current[part]
        return current not in (None, "", [])
