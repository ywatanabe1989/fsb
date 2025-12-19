"""
FSB Data Models.

Dataclass representations of FSB JSON structures.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class BBox:
    """Bounding box in normalized coordinates (0-1)."""

    x0: float
    y0: float
    x1: float
    y1: float

    @property
    def width(self) -> float:
        return self.x1 - self.x0

    @property
    def height(self) -> float:
        return self.y1 - self.y0

    @property
    def center(self) -> tuple[float, float]:
        return ((self.x0 + self.x1) / 2, (self.y0 + self.y1) / 2)

    def to_dict(self) -> Dict[str, float]:
        return {"x0": self.x0, "y0": self.y0, "x1": self.x1, "y1": self.y1}

    @classmethod
    def from_dict(cls, d: Dict[str, float]) -> "BBox":
        return cls(x0=d["x0"], y0=d["y0"], x1=d["x1"], y1=d["y1"])


@dataclass
class SizeMM:
    """Physical size in millimeters."""

    width: float
    height: float

    def to_dict(self) -> Dict[str, float]:
        return {"width": self.width, "height": self.height}

    @classmethod
    def from_dict(cls, d: Dict[str, float]) -> "SizeMM":
        return cls(width=d["width"], height=d["height"])


@dataclass
class Axes:
    """Axis configuration for plot nodes."""

    xlim: Optional[tuple[float, float]] = None
    ylim: Optional[tuple[float, float]] = None
    xscale: str = "linear"
    yscale: str = "linear"
    xlabel: Optional[str] = None
    ylabel: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d = {}
        if self.xlim:
            d["xlim"] = list(self.xlim)
        if self.ylim:
            d["ylim"] = list(self.ylim)
        if self.xscale != "linear":
            d["xscale"] = self.xscale
        if self.yscale != "linear":
            d["yscale"] = self.yscale
        if self.xlabel:
            d["xlabel"] = self.xlabel
        if self.ylabel:
            d["ylabel"] = self.ylabel
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Axes":
        return cls(
            xlim=tuple(d["xlim"]) if "xlim" in d else None,
            ylim=tuple(d["ylim"]) if "ylim" in d else None,
            xscale=d.get("xscale", "linear"),
            yscale=d.get("yscale", "linear"),
            xlabel=d.get("xlabel"),
            ylabel=d.get("ylabel"),
        )


@dataclass
class NodeRefs:
    """References to associated files."""

    encoding: Optional[str] = None
    theme: Optional[str] = None
    data: Optional[str] = None
    stats: Optional[str] = None

    def to_dict(self) -> Dict[str, str]:
        d = {}
        if self.encoding:
            d["encoding"] = self.encoding
        if self.theme:
            d["theme"] = self.theme
        if self.data:
            d["data"] = self.data
        if self.stats:
            d["stats"] = self.stats
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, str]) -> "NodeRefs":
        return cls(
            encoding=d.get("encoding"),
            theme=d.get("theme"),
            data=d.get("data"),
            stats=d.get("stats"),
        )


@dataclass
class Node:
    """FSB Node representing a figure or plot element."""

    id: str
    type: str  # 'figure', 'plot', 'text', 'shape', 'image'
    bbox_norm: BBox
    name: Optional[str] = None
    size_mm: Optional[SizeMM] = None
    axes: Optional[Axes] = None
    children: List[str] = field(default_factory=list)
    refs: Optional[NodeRefs] = None
    created_at: Optional[datetime] = None
    modified_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "id": self.id,
            "type": self.type,
            "bbox_norm": self.bbox_norm.to_dict(),
        }
        if self.name:
            d["name"] = self.name
        if self.size_mm:
            d["size_mm"] = self.size_mm.to_dict()
        if self.axes:
            d["axes"] = self.axes.to_dict()
        if self.children:
            d["children"] = self.children
        if self.refs:
            d["refs"] = self.refs.to_dict()
        if self.created_at:
            d["created_at"] = self.created_at.isoformat()
        if self.modified_at:
            d["modified_at"] = self.modified_at.isoformat()
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Node":
        return cls(
            id=d["id"],
            type=d["type"],
            bbox_norm=BBox.from_dict(d["bbox_norm"]),
            name=d.get("name"),
            size_mm=SizeMM.from_dict(d["size_mm"]) if "size_mm" in d else None,
            axes=Axes.from_dict(d["axes"]) if "axes" in d else None,
            children=d.get("children", []),
            refs=NodeRefs.from_dict(d["refs"]) if "refs" in d else None,
            created_at=datetime.fromisoformat(d["created_at"])
            if "created_at" in d
            else None,
            modified_at=datetime.fromisoformat(d["modified_at"])
            if "modified_at" in d
            else None,
        )


@dataclass
class ChannelEncoding:
    """Encoding for a single visual channel."""

    column: str
    scale: str = "linear"
    aggregate: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d = {"column": self.column, "scale": self.scale}
        if self.aggregate:
            d["aggregate"] = self.aggregate
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ChannelEncoding":
        return cls(
            column=d["column"],
            scale=d.get("scale", "linear"),
            aggregate=d.get("aggregate"),
        )


@dataclass
class TraceEncoding:
    """Encoding specification for a single trace."""

    trace_id: str
    data_ref: Optional[str] = None
    x: Optional[ChannelEncoding] = None
    y: Optional[ChannelEncoding] = None
    color: Optional[ChannelEncoding] = None
    size: Optional[ChannelEncoding] = None
    group: Optional[ChannelEncoding] = None

    def to_dict(self) -> Dict[str, Any]:
        d = {"trace_id": self.trace_id}
        if self.data_ref:
            d["data_ref"] = self.data_ref
        if self.x:
            d["x"] = self.x.to_dict()
        if self.y:
            d["y"] = self.y.to_dict()
        if self.color:
            d["color"] = self.color.to_dict()
        if self.size:
            d["size"] = self.size.to_dict()
        if self.group:
            d["group"] = self.group.to_dict()
        return d


@dataclass
class Encoding:
    """FSB Encoding specification."""

    traces: List[TraceEncoding] = field(default_factory=list)
    legends: Optional[Dict[str, Dict[str, str]]] = None

    def to_dict(self) -> Dict[str, Any]:
        d = {"traces": [t.to_dict() for t in self.traces]}
        if self.legends:
            d["legends"] = self.legends
        return d


@dataclass
class Theme:
    """FSB Theme specification for visual aesthetics."""

    colors: Optional[Dict[str, Any]] = None
    typography: Optional[Dict[str, Any]] = None
    lines: Optional[Dict[str, Any]] = None
    markers: Optional[Dict[str, Any]] = None
    grid: Optional[Dict[str, Any]] = None
    traces: Optional[List[Dict[str, Any]]] = None
    preset: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d = {}
        if self.colors:
            d["colors"] = self.colors
        if self.typography:
            d["typography"] = self.typography
        if self.lines:
            d["lines"] = self.lines
        if self.markers:
            d["markers"] = self.markers
        if self.grid:
            d["grid"] = self.grid
        if self.traces:
            d["traces"] = self.traces
        if self.preset:
            d["preset"] = self.preset
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Theme":
        return cls(
            colors=d.get("colors"),
            typography=d.get("typography"),
            lines=d.get("lines"),
            markers=d.get("markers"),
            grid=d.get("grid"),
            traces=d.get("traces"),
            preset=d.get("preset"),
        )


@dataclass
class StatsResult:
    """A single statistical analysis result."""

    result_id: str
    method: Dict[str, Any]
    inputs: Dict[str, Any]
    results: Dict[str, Any]
    display: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "result_id": self.result_id,
            "method": self.method,
            "inputs": self.inputs,
            "results": self.results,
        }
        if self.display:
            d["display"] = self.display
        if self.created_at:
            d["created_at"] = self.created_at.isoformat()
        return d


@dataclass
class Stats:
    """FSB Stats specification."""

    analyses: List[StatsResult] = field(default_factory=list)
    software: Optional[Dict[str, str]] = None

    def to_dict(self) -> Dict[str, Any]:
        d = {"analyses": [a.to_dict() for a in self.analyses]}
        if self.software:
            d["software"] = self.software
        return d

    def get_result(self, result_id: str) -> Optional[StatsResult]:
        """Get a result by its ID."""
        for r in self.analyses:
            if r.result_id == result_id:
                return r
        return None


@dataclass
class ColumnInfo:
    """Metadata for a single data column."""

    name: str
    dtype: str
    description: Optional[str] = None
    unit: Optional[str] = None
    role: Optional[str] = None
    missing_count: Optional[int] = None
    unique_count: Optional[int] = None
    min: Optional[float] = None
    max: Optional[float] = None
    mean: Optional[float] = None
    std: Optional[float] = None
    categories: Optional[List[str]] = None

    def to_dict(self) -> Dict[str, Any]:
        d = {"name": self.name, "dtype": self.dtype}
        for attr in [
            "description",
            "unit",
            "role",
            "missing_count",
            "unique_count",
            "min",
            "max",
            "mean",
            "std",
            "categories",
        ]:
            val = getattr(self, attr)
            if val is not None:
                d[attr] = val
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ColumnInfo":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class DataInfo:
    """FSB Data Info specification."""

    columns: List[ColumnInfo]
    source: Optional[Dict[str, Any]] = None
    format: Optional[Dict[str, Any]] = None
    shape: Optional[Dict[str, int]] = None

    def to_dict(self) -> Dict[str, Any]:
        d = {"columns": [c.to_dict() for c in self.columns]}
        if self.source:
            d["source"] = self.source
        if self.format:
            d["format"] = self.format
        if self.shape:
            d["shape"] = self.shape
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "DataInfo":
        return cls(
            columns=[ColumnInfo.from_dict(c) for c in d["columns"]],
            source=d.get("source"),
            format=d.get("format"),
            shape=d.get("shape"),
        )

    def get_column(self, name: str) -> Optional[ColumnInfo]:
        """Get column info by name."""
        for c in self.columns:
            if c.name == name:
                return c
        return None
