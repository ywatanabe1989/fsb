"""
FSB Schema loading and validation utilities.
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional, Union

try:
    import jsonschema

    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False

# Schema names and their file mappings
SCHEMA_NAMES = {
    "node": "node.schema.json",
    "encoding": "encoding.schema.json",
    "theme": "theme.schema.json",
    "stats": "stats.schema.json",
    "data_info": "data_info.schema.json",
    "render_manifest": "render_manifest.schema.json",
}

# Cache for loaded schemas
_schema_cache: Dict[str, dict] = {}


def get_schema_dir() -> Path:
    """Get the directory containing schema files."""
    # Try package location first
    pkg_dir = Path(__file__).parent / "schemas"
    if pkg_dir.exists():
        return pkg_dir

    # Fall back to project root schemas directory
    project_schemas = Path(__file__).parent.parent.parent.parent / "schemas"
    if project_schemas.exists():
        return project_schemas

    raise FileNotFoundError("Could not locate FSB schema directory")


def load_schema(name: str) -> dict:
    """
    Load a JSON schema by name.

    Args:
        name: Schema name (e.g., 'node', 'encoding', 'theme')

    Returns:
        Parsed JSON schema as dict

    Raises:
        ValueError: If schema name is unknown
        FileNotFoundError: If schema file not found
    """
    if name in _schema_cache:
        return _schema_cache[name]

    if name not in SCHEMA_NAMES:
        raise ValueError(
            f"Unknown schema: {name}. Valid schemas: {list(SCHEMA_NAMES.keys())}"
        )

    schema_path = get_schema_dir() / SCHEMA_NAMES[name]
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    with open(schema_path, encoding="utf-8") as f:
        schema = json.load(f)

    _schema_cache[name] = schema
    return schema


def validate(
    data: Dict[str, Any],
    schema_name: str,
    raise_on_error: bool = True,
) -> tuple[bool, Optional[str]]:
    """
    Validate data against a named FSB schema.

    Args:
        data: Dictionary to validate
        schema_name: Name of schema to validate against
        raise_on_error: If True, raise exception on validation failure

    Returns:
        Tuple of (is_valid, error_message)

    Raises:
        jsonschema.ValidationError: If validation fails and raise_on_error=True
        ImportError: If jsonschema is not installed
    """
    if not HAS_JSONSCHEMA:
        raise ImportError(
            "jsonschema is required for validation. "
            "Install with: pip install jsonschema"
        )

    schema = load_schema(schema_name)

    try:
        jsonschema.validate(instance=data, schema=schema)
        return True, None
    except jsonschema.ValidationError as e:
        if raise_on_error:
            raise
        return False, str(e.message)


def validate_bundle(
    bundle_path: Union[str, Path],
    raise_on_error: bool = True,
) -> Dict[str, tuple[bool, Optional[str]]]:
    """
    Validate all JSON files in a bundle against their schemas.

    Args:
        bundle_path: Path to bundle directory
        raise_on_error: If True, raise on first validation error

    Returns:
        Dict mapping file names to (is_valid, error_message) tuples
    """
    bundle_path = Path(bundle_path)
    results = {}

    # Map of bundle files to schema names
    file_schema_map = {
        "node.json": "node",
        "encoding.json": "encoding",
        "theme.json": "theme",
        "stats/stats.json": "stats",
        "data/data_info.json": "data_info",
        "cache/render_manifest.json": "render_manifest",
    }

    for file_rel, schema_name in file_schema_map.items():
        file_path = bundle_path / file_rel
        if file_path.exists():
            with open(file_path, encoding="utf-8") as f:
                data = json.load(f)
            results[file_rel] = validate(
                data, schema_name, raise_on_error=raise_on_error
            )
        else:
            results[file_rel] = (None, "File not found")

    return results
