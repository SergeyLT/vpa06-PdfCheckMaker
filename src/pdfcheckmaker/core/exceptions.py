"""Custom exceptions for PdfCheckMaker."""


class PdfCheckMakerError(Exception):
    """Base application error."""


class DataSourceError(PdfCheckMakerError):
    """Raised when an input data source cannot be loaded."""


class InvoiceValidationError(PdfCheckMakerError):
    """Raised when invoice data is incomplete or invalid."""


class TemplateError(PdfCheckMakerError):
    """Raised when a template or manifest is invalid."""


class RenderError(PdfCheckMakerError):
    """Raised when HTML or PDF rendering fails."""
