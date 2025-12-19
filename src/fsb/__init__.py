"""
FSB: Figure-Statistics Bundle

A specification and Python API for reproducible scientific figures.

The FSB format organizes scientific figures as bundles containing:
- node.json: Canonical structure (bbox, axes, children refs)
- encoding.json: Data-to-visual channel mappings
- theme.json: Visual aesthetics (colors, fonts, styles)
- data/: Raw data files and metadata
- stats/: Statistical analysis results
- exports/: Derived outputs (PNG, SVG, PDF)
- cache/: Regenerable files (geometry_px, hitmap)

Example:
    >>> import fsb
    >>> bundle = fsb.Bundle("my_figure")
    >>> bundle.node  # Access node configuration
    >>> bundle.encoding  # Access encoding mappings
    >>> bundle.validate()  # Validate against schemas
"""

from .bundle import Bundle
from .models import DataInfo, Encoding, Node, Stats, Theme
from .schemas import SCHEMA_NAMES, load_schema, validate

__version__ = "0.1.0"
__all__ = [
    "Bundle",
    "Node",
    "Encoding",
    "Theme",
    "Stats",
    "DataInfo",
    "validate",
    "load_schema",
    "SCHEMA_NAMES",
    "__version__",
]
