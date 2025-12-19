# FSB: Figure-Statistics Bundle

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: AGPL-3.0](https://img.shields.io/badge/License-AGPL--3.0-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)

**FSB** is a specification and Python API for reproducible scientific figures. It defines a structured bundle format that captures everything needed to reproduce a figure: data, encodings, theme, and statistical analyses.

## Why FSB?

Scientific figures typically become "black boxes" once exported to PNG/PDF:
- Data is lost or separated from the figure
- Statistical test parameters are not recorded
- Visual encoding decisions (color = condition) are implicit
- Reproducing or modifying the figure requires the original script

FSB solves this by packaging figures as **self-contained bundles** with:
- **Canonical data** (CSV + metadata)
- **Encoding specification** (data → visual channel mappings)
- **Theme** (decorative styles, separable from meaning)
- **Statistical results** (with full reproducibility info)
- **Derived outputs** (PNG, SVG, PDF)

## Installation

```bash
pip install fsb
```

Or install with optional dependencies:

```bash
pip install fsb[all]  # Include matplotlib, scipy, statsmodels
```

## Quick Start

### Create a Bundle

```python
import fsb

# Create a new plot bundle
bundle = fsb.Bundle(
    "my_plot",
    create=True,
    node_type="plot",
    name="My First Plot",
    size_mm={"width": 80, "height": 60},
)

# Configure encoding
bundle.encoding = {
    "traces": [{
        "trace_id": "line1",
        "data_ref": "data/data.csv",
        "x": {"column": "time", "scale": "linear"},
        "y": {"column": "value", "scale": "linear"},
    }]
}

# Save
bundle.save()
```

### Load and Inspect

```python
bundle = fsb.Bundle("my_plot")
print(f"Type: {bundle.bundle_type}")
print(f"Size: {bundle.node.size_mm}")
print(f"Traces: {len(bundle.encoding['traces'])}")
```

### Create Figure with Children

```python
# Create a multi-panel figure
figure = fsb.Bundle(
    "my_figure",
    create=True,
    node_type="figure",
    size_mm={"width": 170, "height": 130},
)

# Add child plots
for panel in ["A", "B", "C", "D"]:
    figure.add_child(f"plot_{panel}", node_type="plot")

figure.save()
```

### Validate Against Schemas

```python
bundle = fsb.Bundle("my_plot")
results = bundle.validate(raise_on_error=False)

for file_name, (is_valid, error) in results.items():
    status = "✓" if is_valid else "✗"
    print(f"{status} {file_name}")
```

## Bundle Structure

```
my_plot/
├── node.json           # Canonical: structure, bbox, refs
├── encoding.json       # Canonical: data → visual mappings
├── theme.json          # Aesthetics: colors, fonts, styles
├── data/
│   ├── data.csv        # Canonical: raw data
│   └── data_info.json  # Canonical: column metadata
├── stats/
│   ├── stats.json      # Canonical: statistical results
│   └── stats.csv       # Derived: human-readable table
├── exports/            # Derived: rendered outputs
│   ├── plot.png
│   ├── plot.svg
│   └── plot.pdf
├── cache/              # Regenerable: can be deleted
│   ├── geometry_px.json
│   ├── render_manifest.json
│   └── hitmap.svg
└── children/           # For figures: child plot bundles
```

### File Categories

| Category | Files | Description |
|----------|-------|-------------|
| **Canonical** | `node.json`, `encoding.json`, `theme.json`, `data/*`, `stats/stats.json` | Source of truth. Don't regenerate. |
| **Derived** | `exports/*`, `stats/stats.csv` | Generated from canonical. Can regenerate. |
| **Cache** | `cache/*` | Temporary/UI data. Can delete. |

## Schema Reference

### node.json

Defines the figure/plot structure:

```json
{
  "id": "my_plot",
  "type": "plot",
  "name": "Firing Rate Over Time",
  "bbox_norm": {"x0": 0, "y0": 0, "x1": 1, "y1": 1},
  "size_mm": {"width": 80, "height": 60},
  "axes": {
    "xlim": [0, 100],
    "ylim": [0, 50],
    "xlabel": "Time (ms)",
    "ylabel": "Rate (Hz)"
  },
  "refs": {
    "encoding": "encoding.json",
    "theme": "theme.json",
    "data": "data/",
    "stats": "stats/stats.json"
  },
  "children": ["subplot_A", "subplot_B"]
}
```

### encoding.json

Maps data to visual channels:

```json
{
  "traces": [
    {
      "trace_id": "control",
      "data_ref": "data/data.csv",
      "x": {"column": "time", "scale": "linear"},
      "y": {"column": "firing_rate", "scale": "linear"},
      "group": {"column": "condition"}
    }
  ],
  "legends": {
    "color": {
      "control": "Control Group",
      "treatment": "Treatment Group"
    }
  }
}
```

### theme.json

Visual aesthetics (decorative, not semantic):

```json
{
  "colors": {
    "palette": ["#1f77b4", "#ff7f0e", "#2ca02c"],
    "background": "#ffffff"
  },
  "typography": {
    "family": "sans-serif",
    "size_pt": 10
  },
  "lines": {"width_pt": 1.5},
  "markers": {"size_pt": 6}
}
```

### stats/stats.json

Statistical analyses with reproducibility info:

```json
{
  "analyses": [
    {
      "result_id": "ttest_main",
      "method": {
        "name": "t-test",
        "variant": "independent",
        "correction": {"method": "bonferroni", "n_comparisons": 3}
      },
      "inputs": {
        "data_refs": [{"path": "data/data.csv", "sha256": "abc123..."}],
        "groups": ["control", "treatment"],
        "n_per_group": [25, 23]
      },
      "results": {
        "statistic": 2.45,
        "p_value": 0.018,
        "p_corrected": 0.054,
        "effect_size": {"name": "cohens_d", "value": 0.72}
      },
      "display": {
        "significance_label": "*",
        "bracket": {"start": "control", "end": "treatment"}
      }
    }
  ],
  "software": {
    "python": "3.11",
    "scipy": "1.11.0",
    "fsb": "0.1.0"
  }
}
```

### data/data_info.json

Column metadata:

```json
{
  "source": {
    "path": "data/data.csv",
    "sha256": "abc123...",
    "created_at": "2025-12-19T12:00:00"
  },
  "shape": {"rows": 100, "columns": 4},
  "columns": [
    {
      "name": "time",
      "dtype": "float64",
      "unit": "ms",
      "role": "x",
      "min": 0,
      "max": 100
    },
    {
      "name": "firing_rate",
      "dtype": "float64",
      "unit": "Hz",
      "role": "y"
    },
    {
      "name": "condition",
      "dtype": "category",
      "role": "group",
      "categories": ["control", "treatment"]
    }
  ]
}
```

## Key Concepts

### Canonical vs Derived

- **Canonical**: The source of truth. These files define the figure.
- **Derived**: Generated from canonical files. Can be regenerated.
- **Cache**: Temporary files for UI/rendering. Can be deleted.

### Recursive Structure

Figures and plots share the same node structure. A figure is simply a node with children:

```
figure/
├── node.json (type: "figure", children: ["plot_A", "plot_B"])
└── children/
    ├── plot_A/
    │   └── node.json (type: "plot")
    └── plot_B/
        └── node.json (type: "plot")
```

### Encoding vs Theme

- **Encoding**: Semantic mappings (color = condition, linestyle = group)
- **Theme**: Decorative properties (font family, line width, color palette)

Changing theme = same meaning, different look.
Changing encoding = different meaning.

## API Reference

### Bundle

```python
class Bundle:
    def __init__(self, path, create=False, node_type="plot", name=None, size_mm=None): ...

    # Properties
    @property def node(self) -> Node: ...
    @property def encoding(self) -> dict: ...
    @property def theme(self) -> dict: ...
    @property def stats(self) -> dict: ...
    @property def bundle_type(self) -> str: ...
    @property def children(self) -> List[str]: ...

    # Methods
    def save(self, path=None) -> Path: ...
    def validate(self, raise_on_error=True) -> dict: ...
    def add_child(self, child_id, **kwargs) -> Bundle: ...
    def get_child(self, child_id) -> Bundle: ...
    def clear_cache(self) -> None: ...
    def to_dict(self) -> dict: ...
```

### Schema Validation

```python
from fsb import validate, load_schema, SCHEMA_NAMES

# Validate data against a schema
is_valid, error = validate(data, "node", raise_on_error=False)

# Load a schema
schema = load_schema("encoding")

# Available schemas
print(SCHEMA_NAMES)  # ['node', 'encoding', 'theme', 'stats', 'data_info', 'render_manifest']
```

### Models

```python
from fsb import Node, Encoding, Theme, Stats, DataInfo
from fsb.models import BBox, SizeMM, Axes

# Create a node programmatically
node = Node(
    id="my_plot",
    type="plot",
    bbox_norm=BBox(0, 0, 1, 1),
    size_mm=SizeMM(80, 60),
)
```

## Examples

See the [examples/](examples/) directory for complete working examples:

1. **01_create_bundle.py** - Create a basic plot bundle
2. **02_figure_with_children.py** - Create multi-panel figures
3. **03_validate_bundle.py** - Validate bundles against schemas
4. **04_data_and_stats.py** - Work with data files and statistics

## Development

```bash
# Clone repository
git clone https://github.com/ywatanabe1989/fsb.git
cd fsb

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black src tests
ruff check src tests
```

## License

AGPL-3.0 License - see [LICENSE](LICENSE) for details.

## Citation

If you use FSB in your research, please cite:

```bibtex
@software{fsb2025,
  title = {FSB: Figure-Statistics Bundle},
  author = {Watanabe, Yusuke},
  year = {2025},
  url = {https://github.com/ywatanabe1989/fsb}
}
```
