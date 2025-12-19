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

Node Types:
- figure: Container node with children (multi-panel figures)
- plot: Leaf node with traces (single plots)

Example:
    >>> import fsb
    >>>
    >>> # Create a plot bundle
    >>> bundle = fsb.Bundle("my_plot", create=True, node_type="plot")
    >>> bundle.encoding = {"traces": [...]}
    >>> bundle.save()
    >>>
    >>> # Render to PNG
    >>> png_bytes = fsb.render_bundle(bundle, dpi=150)
    >>>
    >>> # Run statistics
    >>> from fsb import stats
    >>> result = stats.ttest_ind(group1, group2)
"""

from .bundle import Bundle
from .models import (
    Axes,
    BBox,
    ChannelEncoding,
    ColumnInfo,
    DataInfo,
    Encoding,
    Node,
    NodeRefs,
    SizeMM,
    Stats,
    StatsResult,
    Theme,
    TraceEncoding,
)
from .schemas import SCHEMA_NAMES, load_schema, validate

# Rendering (requires matplotlib)
try:
    from .rendering import (
        MATPLOTLIB_AVAILABLE,
        export_bundle,
        render_bundle,
        render_node,
        render_preview,
    )
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    render_bundle = None
    render_node = None
    render_preview = None
    export_bundle = None

# Stats module
from . import stats

__version__ = "0.1.2"
__all__ = [
    # Core
    "Bundle",
    "__version__",
    # Models
    "Node",
    "BBox",
    "SizeMM",
    "Axes",
    "NodeRefs",
    "Encoding",
    "ChannelEncoding",
    "TraceEncoding",
    "Theme",
    "Stats",
    "StatsResult",
    "DataInfo",
    "ColumnInfo",
    # Schema validation
    "validate",
    "load_schema",
    "SCHEMA_NAMES",
    # Rendering
    "MATPLOTLIB_AVAILABLE",
    "render_bundle",
    "render_node",
    "render_preview",
    "export_bundle",
    # Statistics
    "stats",
]
