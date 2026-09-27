"""Application services that coordinate domain operations."""

from .pipeline import ImageProcessor, ProcessedImage

__all__ = ["ImageProcessor", "ProcessedImage"]
