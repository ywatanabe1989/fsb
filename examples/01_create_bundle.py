#!/usr/bin/env python3
"""
Example 01: Create a basic FSB bundle.

Demonstrates:
- Creating a new plot bundle
- Setting size and metadata
- Saving as directory
"""

from pathlib import Path

import fsb

# Output directory
OUT_DIR = Path(__file__).parent / "output"
OUT_DIR.mkdir(exist_ok=True)


def main():
    # Create a new plot bundle
    bundle = fsb.Bundle(
        OUT_DIR / "my_plot",
        create=True,
        node_type="plot",
        name="My First Plot",
        size_mm={"width": 80, "height": 60},
    )

    print(f"Created: {bundle}")
    print(f"Type: {bundle.bundle_type}")
    print(f"Node ID: {bundle.node.id}")
    print(f"Size: {bundle.node.size_mm}")

    # Update encoding
    bundle._encoding = {
        "traces": [
            {
                "trace_id": "line1",
                "data_ref": "data/data.csv",
                "x": {"column": "time", "scale": "linear"},
                "y": {"column": "value", "scale": "linear"},
            }
        ]
    }

    # Update theme
    bundle._theme = {
        "colors": {"palette": ["#1f77b4", "#ff7f0e", "#2ca02c"]},
        "typography": {"family": "sans-serif", "size_pt": 10},
        "lines": {"width_pt": 1.5},
    }

    # Save
    bundle.save()
    print(f"Saved to: {bundle.path}")

    # Reload and verify
    reloaded = fsb.Bundle(OUT_DIR / "my_plot")
    print(f"Reloaded: {reloaded}")
    print(f"Encoding traces: {len(reloaded.encoding['traces'])}")


if __name__ == "__main__":
    main()
