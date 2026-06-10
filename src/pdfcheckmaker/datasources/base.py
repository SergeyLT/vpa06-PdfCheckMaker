"""Data source abstractions."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from pdfcheckmaker.core.models import Invoice


class DataSource(ABC):
    """Strategy interface for loading invoices from an external source."""

    def __init__(self, path: Path) -> None:
        self.path = path

    @abstractmethod
    def load(self) -> list[Invoice]:
        """Load and validate invoices."""


class ApiSource(DataSource):
    """Future extension point for remote API-backed invoice sources."""
