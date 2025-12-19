#!/usr/bin/env python3
"""
Example 04: Working with data and stats.

Demonstrates:
- Adding data files and metadata
- Recording statistical analysis results
- Linking stats to visual elements
"""

import hashlib
import json
from datetime import datetime
from pathlib import Path

import fsb

OUT_DIR = Path(__file__).parent / "output"
OUT_DIR.mkdir(exist_ok=True)


def main():
    # Create bundle
    bundle = fsb.Bundle(
        OUT_DIR / "data_stats",
        create=True,
        node_type="plot",
        name="Plot with Data and Stats",
    )

    # Create sample data
    data_dir = bundle.path / "data"
    data_file = data_dir / "data.csv"

    # Write sample CSV
    csv_content = """time,value,group
0,0.1,control
1,0.5,control
2,0.8,control
3,0.3,treatment
4,0.9,treatment
5,1.2,treatment
"""
    data_file.write_text(csv_content)

    # Calculate hash for reproducibility
    data_hash = hashlib.sha256(csv_content.encode()).hexdigest()

    # Write data_info.json
    data_info = {
        "source": {
            "path": "data/data.csv",
            "sha256": data_hash,
            "created_at": datetime.now().isoformat(),
        },
        "format": {"type": "csv", "delimiter": ","},
        "shape": {"rows": 6, "columns": 3},
        "columns": [
            {"name": "time", "dtype": "float64", "role": "x", "unit": "s"},
            {"name": "value", "dtype": "float64", "role": "y", "unit": "mV"},
            {
                "name": "group",
                "dtype": "category",
                "role": "group",
                "categories": ["control", "treatment"],
            },
        ],
    }

    with open(data_dir / "data_info.json", "w") as f:
        json.dump(data_info, f, indent=2)

    # Add encoding
    bundle._encoding = {
        "traces": [
            {
                "trace_id": "control",
                "data_ref": "data/data.csv",
                "x": {"column": "time"},
                "y": {"column": "value"},
            },
            {
                "trace_id": "treatment",
                "data_ref": "data/data.csv",
                "x": {"column": "time"},
                "y": {"column": "value"},
            },
        ],
        "legends": {
            "color": {"control": "Control Group", "treatment": "Treatment Group"}
        },
    }

    # Add stats
    bundle._stats = {
        "analyses": [
            {
                "result_id": "ttest_01",
                "method": {
                    "name": "t-test",
                    "variant": "independent",
                    "parameters": {"alternative": "two-sided"},
                },
                "inputs": {
                    "data_refs": [{"path": "data/data.csv", "sha256": data_hash}],
                    "groups": ["control", "treatment"],
                    "n_per_group": [3, 3],
                },
                "results": {
                    "statistic": -2.45,
                    "statistic_name": "t",
                    "p_value": 0.07,
                    "df": 4,
                    "effect_size": {"name": "cohens_d", "value": 1.73},
                },
                "display": {
                    "significance_label": "n.s.",
                    "bracket": {"start": "control", "end": "treatment"},
                },
                "created_at": datetime.now().isoformat(),
            }
        ],
        "software": {"python": "3.11", "scipy": "1.11", "fsb": fsb.__version__},
    }

    # Save
    bundle.save()

    print(f"Bundle saved: {bundle.path}")
    print(f"\nData file: {data_file}")
    print(f"Data hash: {data_hash[:16]}...")
    print(f"\nStats analyses: {len(bundle.stats['analyses'])}")
    print(f"First result: {bundle.stats['analyses'][0]['result_id']}")
    print(f"  p-value: {bundle.stats['analyses'][0]['results']['p_value']}")
    print(f"  label: {bundle.stats['analyses'][0]['display']['significance_label']}")


if __name__ == "__main__":
    main()
