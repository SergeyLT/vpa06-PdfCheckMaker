"""Registry mapping file extensions to data source strategies."""

from __future__ import annotations

from pathlib import Path

from pdfcheckmaker.core.exceptions import DataSourceError
from pdfcheckmaker.datasources.base import DataSource
from pdfcheckmaker.datasources.csv_source import CsvSource
from pdfcheckmaker.datasources.json_source import JsonSource


class DataSourceRegistry:
    """Extensible registry for data source classes."""

    def __init__(self) -> None:
        self._sources: dict[str, type[DataSource]] = {}

    def register(self, extension: str, source_class: type[DataSource]) -> None:
        """Register a source class for a file extension."""
        normalized = extension.lower()
        if not normalized.startswith("."):
            normalized = f".{normalized}"
        self._sources[normalized] = source_class

    def create(self, path: Path) -> DataSource:
        """Create a source for the path extension."""
        source_class = self._sources.get(path.suffix.lower())
        if source_class is None:
            supported = ", ".join(sorted(self._sources)) or "<none>"
            raise DataSourceError(f"Unsupported data source extension {path.suffix!r}. Supported: {supported}")
        return source_class(path)

    def supported_extensions(self) -> tuple[str, ...]:
        """Return known extensions."""
        return tuple(sorted(self._sources))


def default_registry() -> DataSourceRegistry:
    """Build the default data source registry."""
    registry = DataSourceRegistry()
    registry.register(".csv", CsvSource)
    registry.register(".json", JsonSource)
    return registry
