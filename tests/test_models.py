"""Tests for FSB data models."""

from datetime import datetime

from fsb.models import (
    Axes,
    BBox,
    ChannelEncoding,
    ColumnInfo,
    DataInfo,
    Encoding,
    Node,
    SizeMM,
    Stats,
    StatsResult,
    TraceEncoding,
)


class TestBBox:
    """Test BBox model."""

    def test_create_bbox(self):
        """Test BBox creation."""
        bbox = BBox(x0=0.1, y0=0.2, x1=0.9, y1=0.8)
        assert bbox.x0 == 0.1
        assert bbox.y1 == 0.8

    def test_bbox_width_height(self):
        """Test BBox width and height properties."""
        bbox = BBox(x0=0.0, y0=0.0, x1=1.0, y1=0.5)
        assert bbox.width == 1.0
        assert bbox.height == 0.5

    def test_bbox_center(self):
        """Test BBox center property."""
        bbox = BBox(x0=0.0, y0=0.0, x1=1.0, y1=1.0)
        assert bbox.center == (0.5, 0.5)

    def test_bbox_to_dict(self):
        """Test BBox serialization."""
        bbox = BBox(x0=0.1, y0=0.2, x1=0.9, y1=0.8)
        d = bbox.to_dict()
        assert d == {"x0": 0.1, "y0": 0.2, "x1": 0.9, "y1": 0.8}

    def test_bbox_from_dict(self):
        """Test BBox deserialization."""
        d = {"x0": 0.1, "y0": 0.2, "x1": 0.9, "y1": 0.8}
        bbox = BBox.from_dict(d)
        assert bbox.x0 == 0.1


class TestSizeMM:
    """Test SizeMM model."""

    def test_create_size(self):
        """Test SizeMM creation."""
        size = SizeMM(width=170, height=130)
        assert size.width == 170
        assert size.height == 130

    def test_size_roundtrip(self):
        """Test SizeMM serialization roundtrip."""
        size = SizeMM(width=80, height=60)
        d = size.to_dict()
        restored = SizeMM.from_dict(d)
        assert restored.width == size.width
        assert restored.height == size.height


class TestAxes:
    """Test Axes model."""

    def test_axes_defaults(self):
        """Test Axes default values."""
        axes = Axes()
        assert axes.xscale == "linear"
        assert axes.yscale == "linear"
        assert axes.xlim is None

    def test_axes_with_limits(self):
        """Test Axes with limits."""
        axes = Axes(xlim=(0, 10), ylim=(-1, 1))
        assert axes.xlim == (0, 10)
        assert axes.ylim == (-1, 1)

    def test_axes_to_dict_minimal(self):
        """Test Axes serialization with minimal values."""
        axes = Axes()
        d = axes.to_dict()
        assert d == {}  # Default values not included

    def test_axes_to_dict_full(self):
        """Test Axes serialization with all values."""
        axes = Axes(
            xlim=(0, 10),
            ylim=(-1, 1),
            xscale="log",
            xlabel="Time",
        )
        d = axes.to_dict()
        assert d["xlim"] == [0, 10]
        assert d["xscale"] == "log"
        assert d["xlabel"] == "Time"


class TestNode:
    """Test Node model."""

    def test_create_node(self):
        """Test Node creation."""
        node = Node(
            id="test_plot",
            type="plot",
            bbox_norm=BBox(0, 0, 1, 1),
        )
        assert node.id == "test_plot"
        assert node.type == "plot"
        assert node.children == []

    def test_node_with_children(self):
        """Test Node with children."""
        node = Node(
            id="figure",
            type="figure",
            bbox_norm=BBox(0, 0, 1, 1),
            children=["plot_A", "plot_B"],
        )
        assert len(node.children) == 2
        assert "plot_A" in node.children

    def test_node_roundtrip(self):
        """Test Node serialization roundtrip."""
        now = datetime.now()
        node = Node(
            id="test",
            type="plot",
            bbox_norm=BBox(0, 0, 1, 1),
            name="Test Plot",
            size_mm=SizeMM(80, 60),
            created_at=now,
        )
        d = node.to_dict()
        restored = Node.from_dict(d)
        assert restored.id == node.id
        assert restored.name == node.name
        assert restored.size_mm.width == 80


class TestEncoding:
    """Test Encoding models."""

    def test_channel_encoding(self):
        """Test ChannelEncoding."""
        channel = ChannelEncoding(column="time", scale="linear")
        d = channel.to_dict()
        assert d["column"] == "time"
        assert d["scale"] == "linear"

    def test_trace_encoding(self):
        """Test TraceEncoding."""
        trace = TraceEncoding(
            trace_id="line1",
            x=ChannelEncoding(column="time"),
            y=ChannelEncoding(column="value"),
        )
        d = trace.to_dict()
        assert d["trace_id"] == "line1"
        assert d["x"]["column"] == "time"

    def test_encoding(self):
        """Test Encoding with traces."""
        encoding = Encoding(
            traces=[
                TraceEncoding(trace_id="line1"),
                TraceEncoding(trace_id="line2"),
            ]
        )
        d = encoding.to_dict()
        assert len(d["traces"]) == 2


class TestStats:
    """Test Stats models."""

    def test_stats_result(self):
        """Test StatsResult."""
        result = StatsResult(
            result_id="test_01",
            method={"name": "t-test"},
            inputs={"groups": ["A", "B"]},
            results={"p_value": 0.05},
        )
        d = result.to_dict()
        assert d["result_id"] == "test_01"
        assert d["results"]["p_value"] == 0.05

    def test_stats_get_result(self):
        """Test Stats.get_result."""
        stats = Stats(
            analyses=[
                StatsResult(
                    result_id="test_01",
                    method={},
                    inputs={},
                    results={},
                ),
                StatsResult(
                    result_id="test_02",
                    method={},
                    inputs={},
                    results={},
                ),
            ]
        )
        result = stats.get_result("test_02")
        assert result is not None
        assert result.result_id == "test_02"

        assert stats.get_result("nonexistent") is None


class TestDataInfo:
    """Test DataInfo models."""

    def test_column_info(self):
        """Test ColumnInfo."""
        col = ColumnInfo(
            name="time",
            dtype="float64",
            unit="ms",
            role="x",
        )
        d = col.to_dict()
        assert d["name"] == "time"
        assert d["unit"] == "ms"

    def test_data_info(self):
        """Test DataInfo."""
        info = DataInfo(
            columns=[
                ColumnInfo(name="x", dtype="float64"),
                ColumnInfo(name="y", dtype="float64"),
            ],
            shape={"rows": 100, "columns": 2},
        )
        d = info.to_dict()
        assert len(d["columns"]) == 2
        assert d["shape"]["rows"] == 100

    def test_data_info_get_column(self):
        """Test DataInfo.get_column."""
        info = DataInfo(
            columns=[
                ColumnInfo(name="time", dtype="float64"),
                ColumnInfo(name="value", dtype="float64"),
            ]
        )
        col = info.get_column("value")
        assert col is not None
        assert col.name == "value"

        assert info.get_column("nonexistent") is None
