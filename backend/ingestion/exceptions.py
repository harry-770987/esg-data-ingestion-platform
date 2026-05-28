class IngestionException(Exception):
    """Base exception for all ingestion-related errors."""
    pass


class ParserError(IngestionException):
    """Raised when there is an issue parsing the physical file (corrupted CSV, empty file)."""
    pass


class ValidationError(IngestionException):
    """Raised when a validation rule fails the entire batch (e.g., missing critical headers)."""
    pass


class NormalizationError(IngestionException):
    """Raised when data values cannot be normalized (e.g. unknown unit configuration)."""
    pass
