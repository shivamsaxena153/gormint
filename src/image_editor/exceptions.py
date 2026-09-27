"""Exceptions shared by the package and its adapters."""


class ImageValidationError(ValueError):
    """Raised when a supplied path is not a usable image."""


class ExportError(ValueError):
    """Raised when image export settings are invalid."""


class ModelLoadError(RuntimeError):
    """Raised when RMBG-2.0 cannot be downloaded or initialized."""
