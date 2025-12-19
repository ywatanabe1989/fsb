#!/usr/bin/env python3
"""
Example 05: Render FSB bundles to images.

Demonstrates:
- Creating a plot with data
- Rendering to PNG bytes
- Exporting to PNG/SVG/PDF files
- Theme customization affecting rendering
"""

from pathlib import Path

import pandas as pd

import fsb

# Output directory
OUT_DIR = Path(__file__).parent / f"{Path(__file__).stem}_out"
OUT_DIR.mkdir(exist_ok=True)


def main():
    print("FSB Rendering Example")
    print("=" * 40)
    print(f"FSB version: {fsb.__version__}")
    print(f"Matplotlib available: {fsb.MATPLOTLIB_AVAILABLE}")

    if not fsb.MATPLOTLIB_AVAILABLE:
        print("\nMatplotlib not available. Install with: pip install fsb[plotting]")
        return

    # Create bundle path
    bundle_path = OUT_DIR / "rendered_plot"

    # Create plot bundle
    bundle = fsb.Bundle(
        bundle_path,
        create=True,
        node_type="plot",
        name="Sample Time Series",
        size_mm={"width": 120, "height": 80},
    )

    # Configure encoding with traces
    bundle.encoding = {
        "traces": [
            {
                "trace_id": "sensor_a",
                "data_ref": "data/data.csv",
                "x": {"column": "time", "scale": "linear"},
                "y": {"column": "sensor_a", "scale": "linear"},
            },
            {
                "trace_id": "sensor_b",
                "data_ref": "data/data.csv",
                "x": {"column": "time", "scale": "linear"},
                "y": {"column": "sensor_b", "scale": "linear"},
            },
        ],
        "legends": {
            "color": {
                "sensor_a": "Sensor A",
                "sensor_b": "Sensor B",
            }
        },
    }

    # Configure theme
    bundle.theme = {
        "colors": {
            "palette": ["#e41a1c", "#377eb8", "#4daf4a"],
            "background": "#ffffff",
        },
        "typography": {
            "family": "sans-serif",
            "size_pt": 10,
            "title_size_pt": 12,
        },
        "lines": {"width_pt": 2.0},
        "markers": {"size_pt": 4, "style": "o"},
        "grid": {"visible": True, "color": "#eeeeee"},
    }

    # Create sample data
    data_dir = bundle_path / "data"
    data_dir.mkdir(exist_ok=True)

    df = pd.DataFrame({
        "time": list(range(10)),
        "sensor_a": [2, 4, 3, 5, 4, 6, 5, 7, 6, 8],
        "sensor_b": [1, 2, 2, 3, 3, 4, 4, 5, 5, 6],
    })
    df.to_csv(data_dir / "data.csv", index=False)

    # Save bundle
    bundle.save()
    print(f"\nBundle created: {bundle_path}")

    # Render to bytes
    print("\nRendering...")
    png_bytes = fsb.render_bundle(bundle, fmt="png", dpi=150)
    print(f"  PNG bytes: {len(png_bytes):,}")

    # Export to files
    print("\nExporting...")
    png_path = fsb.export_bundle(bundle, format="png", dpi=300)
    print(f"  PNG: {png_path}")

    svg_path = fsb.export_bundle(
        bundle, format="svg", output_path=OUT_DIR / "output.svg"
    )
    print(f"  SVG: {svg_path}")

    pdf_path = fsb.export_bundle(
        bundle, format="pdf", output_path=OUT_DIR / "output.pdf"
    )
    print(f"  PDF: {pdf_path}")

    # Quick preview
    preview_bytes = fsb.render_preview(bundle, dpi=72)
    print(f"\nPreview (72 dpi): {len(preview_bytes):,} bytes")

    print("\n✓ Rendering complete!")


if __name__ == "__main__":
    main()
