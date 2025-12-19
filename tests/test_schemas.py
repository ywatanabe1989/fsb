"""Tests for FSB schema validation."""

import pytest

from fsb.schemas import SCHEMA_NAMES, load_schema, validate


class TestSchemaLoading:
    """Test schema loading."""

    def test_load_all_schemas(self):
        """Test that all schemas can be loaded."""
        for name in SCHEMA_NAMES:
            schema = load_schema(name)
            assert schema is not None
            assert "$schema" in schema

    def test_load_unknown_schema(self):
        """Test error on unknown schema name."""
        with pytest.raises(ValueError, match="Unknown schema"):
            load_schema("nonexistent")

    def test_schema_caching(self):
        """Test that schemas are cached."""
        schema1 = load_schema("node")
        schema2 = load_schema("node")
        assert schema1 is schema2


class TestNodeValidation:
    """Test node.json validation."""

    def test_valid_node(self):
        """Test validation of valid node."""
        node = {
            "id": "test_node",
            "type": "plot",
            "bbox_norm": {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0},
        }
        is_valid, error = validate(node, "node", raise_on_error=False)
        assert is_valid is True
        assert error is None

    def test_node_missing_required(self):
        """Test validation fails on missing required fields."""
        node = {"id": "test"}  # Missing type and bbox_norm
        is_valid, error = validate(node, "node", raise_on_error=False)
        assert is_valid is False

    def test_node_invalid_type(self):
        """Test validation fails on invalid type."""
        node = {
            "id": "test",
            "type": "invalid_type",
            "bbox_norm": {"x0": 0, "y0": 0, "x1": 1, "y1": 1},
        }
        is_valid, error = validate(node, "node", raise_on_error=False)
        assert is_valid is False


class TestEncodingValidation:
    """Test encoding.json validation."""

    def test_valid_encoding(self):
        """Test validation of valid encoding."""
        encoding = {
            "traces": [
                {
                    "trace_id": "line1",
                    "x": {"column": "time", "scale": "linear"},
                    "y": {"column": "value"},
                }
            ]
        }
        is_valid, error = validate(encoding, "encoding", raise_on_error=False)
        assert is_valid is True

    def test_empty_encoding(self):
        """Test that empty encoding is valid."""
        encoding = {}
        is_valid, error = validate(encoding, "encoding", raise_on_error=False)
        assert is_valid is True


class TestThemeValidation:
    """Test theme.json validation."""

    def test_valid_theme(self):
        """Test validation of valid theme."""
        theme = {
            "colors": {
                "primary": "#1f77b4",
                "palette": ["#1f77b4", "#ff7f0e"],
            },
            "typography": {"family": "sans-serif", "size_pt": 10},
        }
        is_valid, error = validate(theme, "theme", raise_on_error=False)
        assert is_valid is True

    def test_invalid_color_format(self):
        """Test validation fails on invalid color format."""
        theme = {"colors": {"primary": "not-a-color"}}
        is_valid, error = validate(theme, "theme", raise_on_error=False)
        assert is_valid is False


class TestStatsValidation:
    """Test stats.json validation."""

    def test_valid_stats(self):
        """Test validation of valid stats."""
        stats = {
            "analyses": [
                {
                    "result_id": "test_01",
                    "method": {"name": "t-test"},
                    "inputs": {"groups": ["A", "B"]},
                    "results": {"p_value": 0.05},
                }
            ]
        }
        is_valid, error = validate(stats, "stats", raise_on_error=False)
        assert is_valid is True

    def test_empty_stats(self):
        """Test that empty stats is valid."""
        stats = {}
        is_valid, error = validate(stats, "stats", raise_on_error=False)
        assert is_valid is True


class TestDataInfoValidation:
    """Test data_info.json validation."""

    def test_valid_data_info(self):
        """Test validation of valid data_info."""
        data_info = {
            "columns": [
                {"name": "time", "dtype": "float64", "unit": "s"},
                {"name": "value", "dtype": "float64"},
            ],
            "shape": {"rows": 100, "columns": 2},
        }
        is_valid, error = validate(data_info, "data_info", raise_on_error=False)
        assert is_valid is True

    def test_missing_columns(self):
        """Test validation fails without columns."""
        data_info = {"shape": {"rows": 100}}
        is_valid, error = validate(data_info, "data_info", raise_on_error=False)
        assert is_valid is False
