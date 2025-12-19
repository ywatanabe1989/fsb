"""
FSB Rendering Module.

Standalone rendering for FSB bundles using matplotlib.
No external dependencies beyond matplotlib and pandas.

Node Types:
- figure: Container node with children (renders children in layout)
- plot: Leaf node with traces (renders data from encoding)

The rendering pipeline:
1. Load node.json for structure and size
2. Load encoding.json for data-to-visual mappings
3. Load theme.json for styling
4. Load data from data/ directory
5. Render to matplotlib figure
"""

from __future__ import annotations

import io
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

# Check matplotlib availability
try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    from matplotlib.gridspec import GridSpec

    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

# Check pandas availability
try:
    import pandas as pd

    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

if TYPE_CHECKING:
    from .bundle import Bundle

__all__ = [
    "MATPLOTLIB_AVAILABLE",
    "render_node",
    "render_bundle",
    "export_bundle",
    "render_preview",
]

# Default theme values
DEFAULT_THEME = {
    "colors": {
        "palette": [
            "#1f77b4",  # blue
            "#ff7f0e",  # orange
            "#2ca02c",  # green
            "#d62728",  # red
            "#9467bd",  # purple
            "#8c564b",  # brown
            "#e377c2",  # pink
            "#7f7f7f",  # gray
            "#bcbd22",  # olive
            "#17becf",  # cyan
        ],
        "background": "#ffffff",
        "foreground": "#000000",
    },
    "typography": {
        "family": "sans-serif",
        "size_pt": 10,
        "title_size_pt": 12,
    },
    "lines": {
        "width_pt": 1.5,
    },
    "markers": {
        "size_pt": 6,
        "style": "o",
    },
    "grid": {
        "visible": False,
        "color": "#cccccc",
        "linewidth": 0.5,
    },
}


def _require_matplotlib():
    """Raise ImportError if matplotlib not available."""
    if not MATPLOTLIB_AVAILABLE:
        raise ImportError(
            "Rendering requires matplotlib. Install with:\n"
            "  pip install fsb[plotting]"
        )


def _merge_theme(user_theme: Optional[Dict], default: Dict) -> Dict:
    """Deep merge user theme with defaults."""
    if not user_theme:
        return default.copy()

    result = default.copy()
    for key, value in user_theme.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = {**result[key], **value}
        else:
            result[key] = value
    return result


def render_node(
    bundle: "Bundle",
    fmt: str = "png",
    dpi: int = 150,
    for_export: bool = False,
) -> bytes:
    """
    Render a node (figure or plot) to image bytes.

    This is the main rendering entry point. It dispatches based on
    the node type:
    - figure: renders children in a layout
    - plot: renders traces from encoding

    Args:
        bundle: FSB Bundle to render
        fmt: Output format ("png", "svg", "pdf")
        dpi: Resolution for raster formats
        for_export: If True, hide editor-only elements

    Returns:
        Rendered image as bytes
    """
    _require_matplotlib()

    node_type = bundle.bundle_type

    if node_type == "figure":
        return _render_figure_node(bundle, fmt, dpi, for_export)
    elif node_type == "plot":
        return _render_plot_node(bundle, fmt, dpi, for_export)
    else:
        # Default to plot-style rendering for unknown types
        return _render_plot_node(bundle, fmt, dpi, for_export)


def _render_figure_node(
    bundle: "Bundle",
    fmt: str,
    dpi: int,
    for_export: bool,
) -> bytes:
    """Render a figure node (container with children)."""
    node = bundle.node
    theme = _merge_theme(bundle.theme, DEFAULT_THEME)

    # Get figure size
    size_mm = {"width": 170, "height": 120}
    if node and node.size_mm:
        size_mm = node.size_mm.to_dict()

    width_in = size_mm["width"] / 25.4
    height_in = size_mm["height"] / 25.4

    fig = plt.figure(figsize=(width_in, height_in), dpi=dpi)
    fig.set_facecolor(theme["colors"]["background"])

    # Get children
    children = bundle.children
    n_children = len(children)

    if n_children == 0:
        # Empty figure - just show title
        ax = fig.add_subplot(111)
        ax.axis("off")
        if node and node.name:
            ax.text(
                0.5, 0.5,
                node.name,
                ha="center", va="center",
                fontsize=theme["typography"]["title_size_pt"],
                transform=ax.transAxes,
            )
    else:
        # Render children in grid layout
        # Calculate grid dimensions
        cols = min(n_children, 3)
        rows = (n_children + cols - 1) // cols

        for i, child_id in enumerate(children):
            try:
                child_bundle = bundle.get_child(child_id)
                row = i // cols
                col = i % cols

                # Create subplot for this child
                ax = fig.add_subplot(rows, cols, i + 1)

                # Render child content into this axes
                _render_child_to_axes(ax, child_bundle, theme, for_export)

                # Add panel label
                ax.text(
                    0.02, 0.98,
                    f"({chr(65 + i)})",  # A, B, C, ...
                    transform=ax.transAxes,
                    fontsize=theme["typography"]["size_pt"],
                    fontweight="bold",
                    va="top", ha="left",
                )
            except Exception:
                # If child fails to load, show placeholder
                ax = fig.add_subplot(rows, cols, i + 1)
                ax.text(0.5, 0.5, f"[{child_id}]", ha="center", va="center")
                ax.axis("off")

    # Add figure title
    if node and node.name:
        fig.suptitle(
            node.name,
            fontsize=theme["typography"]["title_size_pt"],
            fontweight="bold",
        )

    plt.tight_layout()

    # Render to bytes
    buf = io.BytesIO()
    fig.savefig(buf, format=fmt, dpi=dpi, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    return buf.read()


def _render_plot_node(
    bundle: "Bundle",
    fmt: str,
    dpi: int,
    for_export: bool,
) -> bytes:
    """Render a plot node (leaf with traces)."""
    node = bundle.node
    encoding = bundle.encoding or {}
    theme = _merge_theme(bundle.theme, DEFAULT_THEME)

    # Get plot size
    size_mm = {"width": 80, "height": 60}
    if node and node.size_mm:
        size_mm = node.size_mm.to_dict()

    width_in = size_mm["width"] / 25.4
    height_in = size_mm["height"] / 25.4

    fig, ax = plt.subplots(figsize=(width_in, height_in), dpi=dpi)
    fig.set_facecolor(theme["colors"]["background"])

    # Render content to axes
    _render_child_to_axes(ax, bundle, theme, for_export)

    plt.tight_layout()

    # Render to bytes
    buf = io.BytesIO()
    fig.savefig(buf, format=fmt, dpi=dpi, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    return buf.read()


def _render_child_to_axes(
    ax,
    bundle: "Bundle",
    theme: Dict,
    for_export: bool,
) -> None:
    """Render a bundle's content to existing matplotlib axes."""
    node = bundle.node
    encoding = bundle.encoding or {}

    # Apply axes configuration from node
    if node and node.axes:
        _apply_axes_config(ax, node.axes)

    # Render traces
    traces = encoding.get("traces", [])
    if traces:
        _render_traces_to_axes(ax, traces, bundle, theme)
    else:
        # No traces - show placeholder or title
        if node and node.name:
            ax.text(
                0.5, 0.5,
                node.name,
                ha="center", va="center",
                fontsize=theme["typography"]["size_pt"],
                transform=ax.transAxes,
            )
            ax.axis("off")

    # Apply grid settings
    grid_config = theme.get("grid", {})
    if grid_config.get("visible", False):
        ax.grid(
            True,
            color=grid_config.get("color", "#cccccc"),
            linewidth=grid_config.get("linewidth", 0.5),
        )


def _render_traces_to_axes(
    ax,
    traces: List[Dict],
    bundle: "Bundle",
    theme: Dict,
) -> None:
    """Render trace encodings to matplotlib axes."""
    if not PANDAS_AVAILABLE:
        ax.text(0.5, 0.5, "[pandas required for data]",
                ha="center", va="center", transform=ax.transAxes)
        return

    colors = theme["colors"]["palette"]
    line_width = theme["lines"]["width_pt"]
    marker_size = theme["markers"]["size_pt"]
    marker_style = theme["markers"].get("style", "o")

    bundle_dir = bundle._get_bundle_dir()
    legends_config = bundle.encoding.get("legends", {}) if bundle.encoding else {}

    rendered_any = False

    for i, trace in enumerate(traces):
        trace_id = trace.get("trace_id", f"trace_{i}")
        data_ref = trace.get("data_ref")

        # Get trace-specific styling from theme
        trace_color = colors[i % len(colors)]
        trace_themes = theme.get("traces", [])
        if i < len(trace_themes):
            trace_theme = trace_themes[i]
            trace_color = trace_theme.get("color", trace_color)
            line_width = trace_theme.get("linewidth", line_width)
            marker_style = trace_theme.get("marker", marker_style)

        # Parse encoding channels
        x_enc = trace.get("x", {})
        y_enc = trace.get("y", {})
        color_enc = trace.get("color", {})
        group_enc = trace.get("group", {})

        x_col = x_enc.get("column") if isinstance(x_enc, dict) else None
        y_col = y_enc.get("column") if isinstance(y_enc, dict) else None
        group_col = group_enc.get("column") if isinstance(group_enc, dict) else None

        if not x_col or not y_col:
            continue

        # Load data
        df = _load_trace_data(bundle_dir, data_ref)
        if df is None:
            continue

        if x_col not in df.columns or y_col not in df.columns:
            continue

        # Handle grouping
        if group_col and group_col in df.columns:
            groups = df[group_col].unique()
            for j, group in enumerate(groups):
                group_df = df[df[group_col] == group]
                group_color = colors[(i + j) % len(colors)]

                # Get legend label from legends config
                label = legends_config.get("color", {}).get(str(group), str(group))

                ax.plot(
                    group_df[x_col],
                    group_df[y_col],
                    label=label,
                    color=group_color,
                    linewidth=line_width,
                    marker=marker_style,
                    markersize=marker_size,
                )
                rendered_any = True
        else:
            # No grouping - single trace
            label = legends_config.get("color", {}).get(trace_id, trace_id)

            ax.plot(
                df[x_col],
                df[y_col],
                label=label,
                color=trace_color,
                linewidth=line_width,
                marker=marker_style,
                markersize=marker_size,
            )
            rendered_any = True

    # Add legend if we rendered anything
    if rendered_any and len(traces) > 0:
        ax.legend(loc="best", fontsize=theme["typography"]["size_pt"] - 2)


def _load_trace_data(bundle_dir: Path, data_ref: Optional[str]) -> Optional["pd.DataFrame"]:
    """Load trace data from CSV file."""
    if not PANDAS_AVAILABLE:
        return None

    # Try explicit data_ref first
    if data_ref:
        data_path = bundle_dir / data_ref
        if data_path.exists():
            try:
                return pd.read_csv(data_path)
            except Exception:
                pass

    # Fallback to default data path
    default_paths = [
        bundle_dir / "data" / "data.csv",
        bundle_dir / "data.csv",
    ]

    for path in default_paths:
        if path.exists():
            try:
                return pd.read_csv(path)
            except Exception:
                pass

    return None


def _apply_axes_config(ax, axes) -> None:
    """Apply axes configuration from node.axes."""
    # Handle both Axes dataclass and dict
    if hasattr(axes, "to_dict"):
        axes = axes.to_dict()

    if "xlim" in axes and axes["xlim"]:
        ax.set_xlim(axes["xlim"])
    if "ylim" in axes and axes["ylim"]:
        ax.set_ylim(axes["ylim"])
    if "xlabel" in axes and axes["xlabel"]:
        ax.set_xlabel(axes["xlabel"])
    if "ylabel" in axes and axes["ylabel"]:
        ax.set_ylabel(axes["ylabel"])
    if axes.get("xscale", "linear") != "linear":
        ax.set_xscale(axes["xscale"])
    if axes.get("yscale", "linear") != "linear":
        ax.set_yscale(axes["yscale"])


# =============================================================================
# Public API (backward compatible)
# =============================================================================


def render_bundle(bundle: "Bundle", fmt: str = "png", dpi: int = 150) -> bytes:
    """
    Render bundle to image bytes.

    Args:
        bundle: FSB Bundle to render
        fmt: Output format ("png", "svg", "pdf")
        dpi: Resolution for raster formats

    Returns:
        Rendered image as bytes
    """
    return render_node(bundle, fmt=fmt, dpi=dpi, for_export=False)


def export_bundle(
    bundle: "Bundle",
    format: str = "png",
    dpi: int = 300,
    output_path: Optional[Union[str, Path]] = None,
) -> Path:
    """
    Export bundle to image file.

    Args:
        bundle: FSB Bundle to export
        format: Output format ("png", "svg", "pdf")
        dpi: Resolution for raster formats
        output_path: Output path (auto-generated if None)

    Returns:
        Path to exported file
    """
    _require_matplotlib()

    # Determine output path
    if output_path is None:
        bundle_dir = bundle._get_bundle_dir()
        exports_dir = bundle_dir / "exports"
        exports_dir.mkdir(exist_ok=True)
        node_id = bundle.node.id if bundle.node else "bundle"
        output_path = exports_dir / f"{node_id}.{format}"
    else:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

    # Render and save
    img_bytes = render_node(bundle, fmt=format, dpi=dpi, for_export=True)
    output_path.write_bytes(img_bytes)

    return output_path


def render_preview(bundle: "Bundle", dpi: int = 100) -> bytes:
    """Quick preview render at lower resolution."""
    return render_node(bundle, fmt="png", dpi=dpi, for_export=False)


# EOF
