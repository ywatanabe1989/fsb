"""Tests for FSB rendering module."""

import os
import tempfile
from pathlib import Path

import pandas as pd
import pytest

import fsb
from fsb.rendering import MATPLOTLIB_AVAILABLE


@pytest.fixture
def plot_bundle():
    """Create a test plot bundle with data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        bundle_path = Path(tmpdir) / "test_plot"
        
        bundle = fsb.Bundle(
            bundle_path,
            create=True,
            node_type="plot",
            name="Test Plot",
            size_mm={"width": 100, "height": 80},
        )
        
        bundle.encoding = {
            "traces": [{
                "trace_id": "line1",
                "x": {"column": "x"},
                "y": {"column": "y"},
            }]
        }
        
        bundle.theme = {
            "colors": {"palette": ["#ff0000"]},
        }
        
        # Create test data
        data_dir = bundle_path / "data"
        data_dir.mkdir(exist_ok=True)
        df = pd.DataFrame({"x": [0, 1, 2, 3], "y": [1, 2, 3, 4]})
        df.to_csv(data_dir / "data.csv", index=False)
        
        bundle.save()
        yield bundle


@pytest.fixture
def figure_bundle():
    """Create a test figure bundle with children."""
    with tempfile.TemporaryDirectory() as tmpdir:
        figure_path = Path(tmpdir) / "test_figure"
        
        figure = fsb.Bundle(
            figure_path,
            create=True,
            node_type="figure",
            name="Test Figure",
            size_mm={"width": 170, "height": 120},
        )
        
        # Add child
        child = figure.add_child("panel_A", node_type="plot", name="Panel A")
        child.encoding = {"traces": [{"trace_id": "t1", "x": {"column": "x"}, "y": {"column": "y"}}]}
        
        child_dir = figure_path / "children" / "panel_A" / "data"
        child_dir.mkdir(parents=True, exist_ok=True)
        pd.DataFrame({"x": [0, 1, 2], "y": [1, 2, 3]}).to_csv(child_dir / "data.csv", index=False)
        child.save()
        
        figure.save()
        yield figure


@pytest.mark.skipif(not MATPLOTLIB_AVAILABLE, reason="matplotlib not available")
class TestRenderBundle:
    """Test render_bundle function."""
    
    def test_render_plot_png(self, plot_bundle):
        """Test rendering plot to PNG."""
        png_bytes = fsb.render_bundle(plot_bundle, fmt="png", dpi=100)
        assert isinstance(png_bytes, bytes)
        assert len(png_bytes) > 0
        # Check PNG signature
        assert png_bytes[:8] == b'\x89PNG\r\n\x1a\n'
    
    def test_render_plot_svg(self, plot_bundle):
        """Test rendering plot to SVG."""
        svg_bytes = fsb.render_bundle(plot_bundle, fmt="svg", dpi=100)
        assert isinstance(svg_bytes, bytes)
        assert b'<svg' in svg_bytes
    
    def test_render_figure(self, figure_bundle):
        """Test rendering figure with children."""
        png_bytes = fsb.render_bundle(figure_bundle, fmt="png", dpi=100)
        assert isinstance(png_bytes, bytes)
        assert len(png_bytes) > 0


@pytest.mark.skipif(not MATPLOTLIB_AVAILABLE, reason="matplotlib not available")
class TestExportBundle:
    """Test export_bundle function."""
    
    def test_export_to_default_path(self, plot_bundle):
        """Test exporting to default exports directory."""
        output_path = fsb.export_bundle(plot_bundle, format="png", dpi=150)
        assert output_path.exists()
        assert output_path.suffix == ".png"
    
    def test_export_to_custom_path(self, plot_bundle):
        """Test exporting to custom path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "custom_output.png"
            result = fsb.export_bundle(plot_bundle, format="png", output_path=output_path)
            assert result == output_path
            assert output_path.exists()


@pytest.mark.skipif(not MATPLOTLIB_AVAILABLE, reason="matplotlib not available")
class TestRenderPreview:
    """Test render_preview function."""
    
    def test_preview_lower_dpi(self, plot_bundle):
        """Test that preview uses lower DPI."""
        preview = fsb.render_preview(plot_bundle, dpi=72)
        full = fsb.render_bundle(plot_bundle, dpi=300)
        # Preview should be smaller
        assert len(preview) < len(full)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
