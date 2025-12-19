#!/usr/bin/env python3
"""
Example 06: Render multi-panel figures.

Demonstrates:
- Creating a figure node (container)
- Adding child plot nodes
- Rendering the complete figure
- Panel labels (A, B, C, ...)
"""

from pathlib import Path

import pandas as pd

import fsb

# Output directory
OUT_DIR = Path(__file__).parent / f"{Path(__file__).stem}_out"
OUT_DIR.mkdir(exist_ok=True)


def main():
    print("FSB Figure Rendering Example")
    print("=" * 40)

    if not fsb.MATPLOTLIB_AVAILABLE:
        print("Matplotlib not available. Install with: pip install fsb[plotting]")
        return

    # Create figure bundle
    figure_path = OUT_DIR / "multi_panel_figure"

    figure = fsb.Bundle(
        figure_path,
        create=True,
        node_type="figure",
        name="Experimental Results",
        size_mm={"width": 170, "height": 100},
    )

    # Add Panel A - Time series
    panel_a = figure.add_child("panel_A", node_type="plot", name="Time Course")
    panel_a.encoding = {
        "traces": [
            {"trace_id": "control", "x": {"column": "time"}, "y": {"column": "control"}},
            {"trace_id": "treatment", "x": {"column": "time"}, "y": {"column": "treatment"}},
        ],
        "legends": {"color": {"control": "Control", "treatment": "Treatment"}},
    }
    panel_a.theme = {
        "colors": {"palette": ["#666666", "#e41a1c"]},
        "lines": {"width_pt": 2.0},
    }

    # Create data for Panel A
    data_dir_a = figure_path / "children" / "panel_A" / "data"
    data_dir_a.mkdir(parents=True, exist_ok=True)
    df_a = pd.DataFrame({
        "time": [0, 1, 2, 3, 4, 5],
        "control": [1.0, 1.2, 1.1, 1.3, 1.2, 1.4],
        "treatment": [1.0, 1.5, 2.0, 2.3, 2.8, 3.2],
    })
    df_a.to_csv(data_dir_a / "data.csv", index=False)
    panel_a.save()

    # Add Panel B - Bar-like comparison (as line for simplicity)
    panel_b = figure.add_child("panel_B", node_type="plot", name="Final Values")
    panel_b.encoding = {
        "traces": [
            {"trace_id": "comparison", "x": {"column": "group"}, "y": {"column": "value"}},
        ],
    }
    panel_b.theme = {
        "colors": {"palette": ["#377eb8"]},
        "markers": {"size_pt": 10, "style": "s"},
    }

    # Create data for Panel B
    data_dir_b = figure_path / "children" / "panel_B" / "data"
    data_dir_b.mkdir(parents=True, exist_ok=True)
    df_b = pd.DataFrame({
        "group": [1, 2],
        "value": [1.4, 3.2],
    })
    df_b.to_csv(data_dir_b / "data.csv", index=False)
    panel_b.save()

    # Save figure
    figure.save()

    print(f"Figure created: {figure_path}")
    print(f"Children: {figure.children}")

    # Render figure
    print("\nRendering figure...")
    png_bytes = fsb.render_bundle(figure, fmt="png", dpi=150)
    print(f"  PNG: {len(png_bytes):,} bytes")

    # Export
    export_path = fsb.export_bundle(figure, format="png", dpi=300)
    print(f"  Exported: {export_path}")

    # Also save standalone PNG
    standalone_path = OUT_DIR / "figure_output.png"
    with open(standalone_path, "wb") as f:
        f.write(png_bytes)
    print(f"  Standalone: {standalone_path}")

    print("\n✓ Figure rendering complete!")


if __name__ == "__main__":
    main()
