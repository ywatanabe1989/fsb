#!/usr/bin/env python3
"""
Example 02: Create a figure bundle with child plots.

Demonstrates:
- Creating a figure bundle (container)
- Adding child plot bundles
- Recursive bundle structure
"""

from pathlib import Path

import fsb

OUT_DIR = Path(__file__).parent / "output"
OUT_DIR.mkdir(exist_ok=True)


def main():
    # Create a figure bundle (2x2 layout)
    figure = fsb.Bundle(
        OUT_DIR / "multi_panel",
        create=True,
        node_type="figure",
        name="Multi-Panel Figure",
        size_mm={"width": 170, "height": 130},
    )

    print(f"Created figure: {figure}")

    # Add child plots
    for panel_id in ["A", "B", "C", "D"]:
        child = figure.add_child(
            f"plot_{panel_id}",
            node_type="plot",
            name=f"Panel {panel_id}",
            size_mm={"width": 80, "height": 60},
        )
        print(f"  Added child: {child}")

    # Save
    figure.save()
    print(f"\nFigure saved to: {figure.path}")
    print(f"Children: {figure.children}")

    # Access a child
    child_a = figure.get_child("plot_A")
    print(f"\nChild A: {child_a}")
    print(f"Child A type: {child_a.bundle_type}")


if __name__ == "__main__":
    main()
