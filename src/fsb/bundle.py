"""
FSB Bundle - Main interface for reading/writing FSB bundles.
"""

import json
import shutil
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .models import BBox, Node, NodeRefs, SizeMM
from .schemas import validate_bundle


class Bundle:
    """
    FSB Bundle - A self-contained package for a reproducible scientific figure.

    A bundle can be either:
    - A directory (e.g., my_figure/)
    - A ZIP archive (e.g., my_figure.zip)

    Bundle structure:
        my_figure/
        ├── node.json           # Canonical: structure, bbox, refs
        ├── encoding.json       # Canonical: data→visual mappings
        ├── theme.json          # Aesthetics: colors, fonts, styles
        ├── data/
        │   ├── data.csv        # Canonical: raw data
        │   └── data_info.json  # Canonical: column metadata
        ├── stats/
        │   ├── stats.json      # Canonical: statistical results
        │   └── stats.csv       # Derived: human-readable table
        ├── exports/            # Derived: PNG, SVG, PDF outputs
        ├── cache/              # Regenerable: geometry_px, hitmap
        └── children/           # Child bundles (for figures)

    Example:
        >>> bundle = Bundle("my_plot")
        >>> bundle.node.type
        'plot'
        >>> bundle.encoding.traces[0].x.column
        'time'
        >>> bundle.save()
    """

    CANONICAL_FILES = ["node.json", "encoding.json", "theme.json"]
    CANONICAL_DIRS = ["data", "stats"]
    DERIVED_DIRS = ["exports"]
    CACHE_DIRS = ["cache"]

    def __init__(
        self,
        path: Union[str, Path],
        create: bool = False,
        node_type: str = "plot",
        name: Optional[str] = None,
        size_mm: Optional[Dict[str, float]] = None,
    ):
        """
        Open or create an FSB bundle.

        Args:
            path: Path to bundle (directory or .zip archive)
            create: If True, create new bundle if it doesn't exist
            node_type: Type of node ('figure' or 'plot') for new bundles
            name: Human-readable name for new bundles
            size_mm: Physical size in mm for new bundles
        """
        self.path = Path(path)
        self._is_zip = self.path.suffix == ".zip"
        self._work_dir: Optional[Path] = None

        # Internal state
        self._node: Optional[Node] = None
        self._encoding: Optional[Dict[str, Any]] = None
        self._theme: Optional[Dict[str, Any]] = None
        self._stats: Optional[Dict[str, Any]] = None
        self._data_info: Optional[Dict[str, Any]] = None
        self._modified = False

        if self.path.exists():
            self._load()
        elif create:
            self._create(node_type, name, size_mm)
        else:
            raise FileNotFoundError(f"Bundle not found: {self.path}")

    def _get_bundle_dir(self) -> Path:
        """Get the working directory for the bundle."""
        if self._is_zip:
            if self._work_dir is None:
                # Extract to temp location for reading
                import tempfile

                self._work_dir = Path(tempfile.mkdtemp(prefix="fsb_"))
                with zipfile.ZipFile(self.path, "r") as zf:
                    zf.extractall(self._work_dir)
            return self._work_dir
        return self.path

    def _load(self) -> None:
        """Load bundle contents."""
        bundle_dir = self._get_bundle_dir()

        # Load node.json
        node_path = bundle_dir / "node.json"
        if node_path.exists():
            with open(node_path, encoding="utf-8") as f:
                self._node = Node.from_dict(json.load(f))

        # Load encoding.json
        encoding_path = bundle_dir / "encoding.json"
        if encoding_path.exists():
            with open(encoding_path, encoding="utf-8") as f:
                self._encoding = json.load(f)

        # Load theme.json
        theme_path = bundle_dir / "theme.json"
        if theme_path.exists():
            with open(theme_path, encoding="utf-8") as f:
                self._theme = json.load(f)

        # Load stats/stats.json
        stats_path = bundle_dir / "stats" / "stats.json"
        if stats_path.exists():
            with open(stats_path, encoding="utf-8") as f:
                self._stats = json.load(f)

        # Load data/data_info.json
        data_info_path = bundle_dir / "data" / "data_info.json"
        if data_info_path.exists():
            with open(data_info_path, encoding="utf-8") as f:
                self._data_info = json.load(f)

    def _create(
        self,
        node_type: str,
        name: Optional[str],
        size_mm: Optional[Dict[str, float]],
    ) -> None:
        """Create a new bundle."""
        bundle_dir = self.path
        if self._is_zip:
            bundle_dir = self.path.with_suffix(
                ""
            )  # Remove .zip extension for directory

        # Create directory structure
        bundle_dir.mkdir(parents=True, exist_ok=True)
        (bundle_dir / "data").mkdir(exist_ok=True)
        (bundle_dir / "stats").mkdir(exist_ok=True)
        (bundle_dir / "exports").mkdir(exist_ok=True)
        (bundle_dir / "cache").mkdir(exist_ok=True)

        if node_type == "figure":
            (bundle_dir / "children").mkdir(exist_ok=True)

        # Create node
        now = datetime.now()
        self._node = Node(
            id=self.path.stem,
            type=node_type,
            bbox_norm=BBox(x0=0.0, y0=0.0, x1=1.0, y1=1.0),
            name=name,
            size_mm=SizeMM.from_dict(size_mm) if size_mm else None,
            refs=NodeRefs(
                encoding="encoding.json",
                theme="theme.json",
                data="data/",
                stats="stats/stats.json",
            ),
            created_at=now,
            modified_at=now,
        )

        # Initialize empty encoding and theme
        self._encoding = {"traces": []}
        self._theme = {}
        self._stats = {"analyses": []}

        # Write initial files
        self._write_json(bundle_dir / "node.json", self._node.to_dict())
        self._write_json(bundle_dir / "encoding.json", self._encoding)
        self._write_json(bundle_dir / "theme.json", self._theme)
        self._write_json(bundle_dir / "stats" / "stats.json", self._stats)

        self._modified = False

        if not self._is_zip:
            self.path = bundle_dir

    @staticmethod
    def _write_json(path: Path, data: Any) -> None:
        """Write JSON file with consistent formatting."""
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")

    @property
    def node(self) -> Optional[Node]:
        """Get the node configuration."""
        return self._node

    @property
    def encoding(self) -> Optional[Dict[str, Any]]:
        """Get the encoding configuration."""
        return self._encoding

    @property
    def theme(self) -> Optional[Dict[str, Any]]:
        """Get the theme configuration."""
        return self._theme

    @property
    def stats(self) -> Optional[Dict[str, Any]]:
        """Get the stats configuration."""
        return self._stats

    @property
    def data_info(self) -> Optional[Dict[str, Any]]:
        """Get the data info."""
        return self._data_info

    @property
    def bundle_type(self) -> str:
        """Get the bundle type (figure or plot)."""
        return self._node.type if self._node else "unknown"

    @property
    def children(self) -> List[str]:
        """Get list of child bundle IDs."""
        if self._node:
            return self._node.children
        return []

    def get_child(self, child_id: str) -> "Bundle":
        """
        Get a child bundle by ID.

        Args:
            child_id: ID of the child bundle

        Returns:
            Child Bundle instance
        """
        bundle_dir = self._get_bundle_dir()
        child_path = bundle_dir / "children" / child_id
        if not child_path.exists():
            child_path = bundle_dir / "children" / f"{child_id}.zip"
        return Bundle(child_path)

    def add_child(self, child_id: str, **kwargs) -> "Bundle":
        """
        Add a new child bundle.

        Args:
            child_id: ID for the new child
            **kwargs: Passed to Bundle constructor

        Returns:
            The newly created child Bundle
        """
        bundle_dir = self._get_bundle_dir()
        children_dir = bundle_dir / "children"
        children_dir.mkdir(exist_ok=True)

        child_path = children_dir / child_id
        child = Bundle(child_path, create=True, **kwargs)

        if self._node:
            if child_id not in self._node.children:
                self._node.children.append(child_id)
                self._modified = True

        return child

    def validate(self, raise_on_error: bool = True) -> Dict[str, tuple]:
        """
        Validate the bundle against FSB schemas.

        Args:
            raise_on_error: If True, raise exception on first error

        Returns:
            Dict mapping file names to (is_valid, error_message) tuples
        """
        bundle_dir = self._get_bundle_dir()
        return validate_bundle(bundle_dir, raise_on_error=raise_on_error)

    def save(self, path: Optional[Union[str, Path]] = None) -> Path:
        """
        Save the bundle.

        Args:
            path: Optional new path to save to

        Returns:
            Path to saved bundle
        """
        if path:
            path = Path(path)
        else:
            path = self.path

        is_zip = path.suffix == ".zip"
        bundle_dir = path.with_suffix("") if is_zip else path

        # Ensure directory exists
        bundle_dir.mkdir(parents=True, exist_ok=True)

        # Update modified timestamp
        if self._node:
            self._node.modified_at = datetime.now()

        # Write canonical files
        if self._node:
            self._write_json(bundle_dir / "node.json", self._node.to_dict())
        if self._encoding:
            self._write_json(bundle_dir / "encoding.json", self._encoding)
        if self._theme:
            self._write_json(bundle_dir / "theme.json", self._theme)

        # Ensure subdirectories exist
        for subdir in ["data", "stats", "exports", "cache"]:
            (bundle_dir / subdir).mkdir(exist_ok=True)

        if self.bundle_type == "figure":
            (bundle_dir / "children").mkdir(exist_ok=True)

        if self._stats:
            self._write_json(bundle_dir / "stats" / "stats.json", self._stats)

        # Create ZIP if requested
        if is_zip:
            with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
                for file_path in bundle_dir.rglob("*"):
                    if file_path.is_file():
                        arcname = file_path.relative_to(bundle_dir)
                        zf.write(file_path, arcname)
            # Optionally remove the directory after zipping
            # shutil.rmtree(bundle_dir)

        self._modified = False
        return path

    def export(self, format: str = "png", dpi: int = 300) -> Path:
        """
        Export the bundle to an image format.

        Args:
            format: Output format ('png', 'svg', 'pdf')
            dpi: Resolution for raster formats

        Returns:
            Path to exported file

        Note:
            Requires matplotlib to be installed.
        """
        bundle_dir = self._get_bundle_dir()
        exports_dir = bundle_dir / "exports"
        exports_dir.mkdir(exist_ok=True)

        output_path = exports_dir / f"{self._node.id}.{format}"

        # This is a placeholder - actual rendering would require
        # matplotlib integration
        raise NotImplementedError(
            "Export requires matplotlib integration. "
            "Use the full SciTeX package for rendering."
        )

    def clear_cache(self) -> None:
        """Remove all cached/derived files."""
        bundle_dir = self._get_bundle_dir()

        cache_dir = bundle_dir / "cache"
        if cache_dir.exists():
            shutil.rmtree(cache_dir)
            cache_dir.mkdir()

        exports_dir = bundle_dir / "exports"
        if exports_dir.exists():
            for f in exports_dir.iterdir():
                f.unlink()

    def to_dict(self) -> Dict[str, Any]:
        """Export bundle configuration as a dictionary."""
        return {
            "node": self._node.to_dict() if self._node else None,
            "encoding": self._encoding,
            "theme": self._theme,
            "stats": self._stats,
            "data_info": self._data_info,
        }

    def __repr__(self) -> str:
        return f"Bundle({self.path}, type={self.bundle_type})"

    def __del__(self):
        """Clean up temporary directory if needed."""
        if self._work_dir and self._work_dir.exists():
            try:
                shutil.rmtree(self._work_dir)
            except Exception:
                pass
