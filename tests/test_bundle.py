"""Tests for FSB Bundle."""

import tempfile
from pathlib import Path

import pytest

from fsb import Bundle


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


class TestBundleCreation:
    """Test bundle creation."""

    def test_create_plot_bundle(self, temp_dir):
        """Test creating a basic plot bundle."""
        bundle = Bundle(
            temp_dir / "test_plot",
            create=True,
            node_type="plot",
            name="Test Plot",
        )

        assert bundle.path.exists()
        assert bundle.bundle_type == "plot"
        assert bundle.node.name == "Test Plot"
        assert bundle.node.id == "test_plot"

    def test_create_figure_bundle(self, temp_dir):
        """Test creating a figure bundle."""
        bundle = Bundle(
            temp_dir / "test_figure",
            create=True,
            node_type="figure",
            name="Test Figure",
            size_mm={"width": 170, "height": 130},
        )

        assert bundle.bundle_type == "figure"
        assert bundle.node.size_mm.width == 170
        assert bundle.node.size_mm.height == 130
        assert (bundle.path / "children").exists()

    def test_bundle_not_found(self, temp_dir):
        """Test error when bundle doesn't exist."""
        with pytest.raises(FileNotFoundError):
            Bundle(temp_dir / "nonexistent")


class TestBundleStructure:
    """Test bundle directory structure."""

    def test_required_directories_created(self, temp_dir):
        """Test that required directories are created."""
        bundle = Bundle(temp_dir / "test", create=True)

        assert (bundle.path / "data").exists()
        assert (bundle.path / "stats").exists()
        assert (bundle.path / "exports").exists()
        assert (bundle.path / "cache").exists()

    def test_required_files_created(self, temp_dir):
        """Test that required JSON files are created."""
        bundle = Bundle(temp_dir / "test", create=True)
        bundle.save()

        assert (bundle.path / "node.json").exists()
        assert (bundle.path / "encoding.json").exists()
        assert (bundle.path / "theme.json").exists()
        assert (bundle.path / "stats" / "stats.json").exists()


class TestBundleChildren:
    """Test figure bundle with children."""

    def test_add_child(self, temp_dir):
        """Test adding child bundles."""
        figure = Bundle(
            temp_dir / "figure",
            create=True,
            node_type="figure",
        )

        child = figure.add_child("plot_A", node_type="plot", name="Panel A")

        assert "plot_A" in figure.children
        assert child.path.exists()
        assert child.bundle_type == "plot"

    def test_get_child(self, temp_dir):
        """Test retrieving child bundles."""
        figure = Bundle(
            temp_dir / "figure",
            create=True,
            node_type="figure",
        )
        figure.add_child("plot_A", node_type="plot")
        figure.save()

        child = figure.get_child("plot_A")
        assert child.node.id == "plot_A"


class TestBundleSaveLoad:
    """Test saving and loading bundles."""

    def test_save_and_reload(self, temp_dir):
        """Test saving and reloading a bundle."""
        bundle = Bundle(
            temp_dir / "test",
            create=True,
            name="Original Name",
        )
        bundle.save()

        reloaded = Bundle(temp_dir / "test")
        assert reloaded.node.name == "Original Name"

    def test_modified_timestamp_updated(self, temp_dir):
        """Test that modified_at is updated on save."""
        bundle = Bundle(temp_dir / "test", create=True)
        original_time = bundle.node.modified_at

        bundle.save()
        assert bundle.node.modified_at >= original_time


class TestBundleData:
    """Test bundle data handling."""

    def test_encoding_update(self, temp_dir):
        """Test updating encoding configuration."""
        bundle = Bundle(temp_dir / "test", create=True)

        bundle._encoding = {"traces": [{"trace_id": "line1", "x": {"column": "time"}}]}
        bundle.save()

        reloaded = Bundle(temp_dir / "test")
        assert len(reloaded.encoding["traces"]) == 1
        assert reloaded.encoding["traces"][0]["trace_id"] == "line1"

    def test_theme_update(self, temp_dir):
        """Test updating theme configuration."""
        bundle = Bundle(temp_dir / "test", create=True)

        bundle._theme = {"colors": {"primary": "#ff0000"}}
        bundle.save()

        reloaded = Bundle(temp_dir / "test")
        assert reloaded.theme["colors"]["primary"] == "#ff0000"


class TestBundleValidation:
    """Test bundle validation."""

    def test_validate_valid_bundle(self, temp_dir):
        """Test validating a valid bundle."""
        bundle = Bundle(temp_dir / "test", create=True)
        bundle.save()

        results = bundle.validate(raise_on_error=False)
        assert results["node.json"][0] is True

    def test_validate_missing_files(self, temp_dir):
        """Test validation reports missing files."""
        bundle = Bundle(temp_dir / "test", create=True)
        bundle.save()

        results = bundle.validate(raise_on_error=False)
        # data_info.json should be missing
        assert results["data/data_info.json"][0] is None


class TestClearCache:
    """Test cache clearing."""

    def test_clear_cache(self, temp_dir):
        """Test clearing cache directory."""
        bundle = Bundle(temp_dir / "test", create=True)

        # Create some cache files
        cache_dir = bundle.path / "cache"
        (cache_dir / "test.json").write_text("{}")

        bundle.clear_cache()

        # Cache dir should exist but be empty
        assert cache_dir.exists()
        assert list(cache_dir.iterdir()) == []
