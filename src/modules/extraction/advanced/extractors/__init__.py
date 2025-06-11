"""
Advanced Extractors
Modular extractors that work together cohesively
"""

from .table_extractor import TableExtractor
from .image_extractor import ImageExtractor
from .text_extractor import TextExtractor

__all__ = ['TableExtractor', 'ImageExtractor', 'TextExtractor']

# Define extraction order for optimal performance
EXTRACTION_ORDER = [
    'structure',  # First analyze structure
    'text',       # Extract text with layout
    'tables',     # Extract tables based on structure
    'images',     # Extract images
    'formulas'    # Extract formulas last
]
